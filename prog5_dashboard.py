import streamlit as st
import pandas as pd
import sqlite3
import os
import altair as alt

# Define the database path
DB_DIR = "database"
DB_FILE_NAME = "baseball_stats.db"
FULL_DB_PATH = os.path.join(DB_DIR, DB_FILE_NAME)

def get_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(FULL_DB_PATH)

def fetch_data(query, params=()):
    """Fetches data from the database using the given query and returns it as a Pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except pd.io.sql.DatabaseError as e:
        st.error(f"Database query error: {e}")
        df = pd.DataFrame() # Return empty DataFrame on error
    finally:
        conn.close()
    return df

def get_all_years():
    """Fetches all unique years from relevant statistics tables."""
    query = """
    SELECT DISTINCT year FROM home_runs_stats
    UNION
    SELECT DISTINCT year FROM batting_average_stats
    UNION
    SELECT DISTINCT year FROM strikeouts_stats
    UNION
    SELECT DISTINCT year FROM rbi_stats
    UNION
    SELECT DISTINCT year FROM wins_stats
    ORDER BY year ASC;
    """
    df = fetch_data(query)
    return df['year'].tolist() if not df.empty else []

def get_all_leagues():
    """Fetches all unique leagues from relevant statistics tables."""
    query = """
    SELECT DISTINCT league FROM home_runs_stats
    UNION
    SELECT DISTINCT league FROM batting_average_stats
    UNION
    SELECT DISTINCT league FROM strikeouts_stats
    UNION
    SELECT DISTINCT league FROM rbi_stats
    ORDER BY league;
    """
    df = fetch_data(query)
    return [l for l in df['league'].tolist() if l is not None] if not df.empty else []

# Define a list of pre-defined queries for the user to choose from for the dynamic section
# Each tuple contains (description, SQL query, expected_chart_type, x_axis, y_axis, color_by, tooltip_cols, param_type)
# param_type: 'none', 'player', 'year'
PREDEFINED_QUERIES = [
    ("Top 10 Players by Home Runs (All Time)",
     "SELECT player, SUM(home_runs) AS total_home_runs FROM home_runs_stats GROUP BY player ORDER BY total_home_runs DESC LIMIT 10;",
     "bar", "player:N", "total_home_runs:Q", "player:N", ["player", "total_home_runs"], "none"),
    ("Top 10 Players by Batting Average (Min 100 AB, All Time)",
     "SELECT player, AVG(batting_average) AS avg_batting_average FROM batting_average_stats GROUP BY player ORDER BY avg_batting_average DESC LIMIT 10;",
     "bar", "player:N", "avg_batting_average:Q", "player:N", ["player", alt.Tooltip("avg_batting_average", format=".3f")], "none"),
    ("Total Home Runs per Year (All Leagues)",
     "SELECT year, SUM(home_runs) AS total_home_runs FROM home_runs_stats GROUP BY year ORDER BY year;",
     "line", "year:O", "total_home_runs:Q", None, ["year", "total_home_runs"], "none"),
    ("Average Batting Average per Year (All Leagues)",
     "SELECT year, AVG(batting_average) AS avg_batting_average FROM batting_average_stats GROUP BY year ORDER BY year;",
     "line", "year:O", "avg_batting_average:Q", None, ["year", alt.Tooltip("avg_batting_average", format=".3f")], "none"),
    ("Total Number of Players Each Year (Across All Tables)",
     """SELECT year, COUNT(DISTINCT player) AS num_players FROM (
         SELECT year, player FROM home_runs_stats
         UNION ALL
         SELECT year, player FROM batting_average_stats
         UNION ALL
         SELECT year, player FROM strikeouts_stats
         UNION ALL
         SELECT year, player FROM wins_stats
         UNION ALL
         SELECT year, player FROM stolen_bases_stats
     ) AS combined_stats GROUP BY year ORDER BY year;""",
     "line", "year:O", "num_players:Q", None, ["year", "num_players"], "none"),
    ]


# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Baseball Stats Dashboard ⚾️")

# Dashboard Title
st.title("⚾️ Interactive Baseball Statistics Dashboard")
st.markdown("Explore historical baseball player and team data with interactive visualizations.")

# Check if database file exists
if not os.path.exists(FULL_DB_PATH):
    st.error(f"Database file not found: `{FULL_DB_PATH}`. Please ensure you have run the 'Database Import Program' first to create the database.")
    st.stop() # Stop the Streamlit app if the database is missing

# Fetch initial data for filters for parameter dropdowns
all_years = get_all_years()
all_players_for_dropdown = sorted(list(set(fetch_data("SELECT DISTINCT player FROM home_runs_stats").player.tolist() +
                                            fetch_data("SELECT DISTINCT player FROM batting_average_stats").player.tolist() +
                                            fetch_data("SELECT DISTINCT player FROM strikeouts_stats").player.tolist() +
                                            fetch_data("SELECT DISTINCT player FROM rbi_stats").player.tolist())))


# Sidebar Filters 
st.sidebar.header("Global Data Filters")
min_year_data = all_years[0] if all_years else 1870
max_year_data = all_years[-1] if all_years else 2023
year_range = st.sidebar.slider("Select Year Range", min_year_data, max_year_data, (min_year_data, max_year_data))
avg_threshold = st.sidebar.slider("Minimum Batting Average", 0.200, 0.450, 0.300, 0.005, format="%.3f")
all_leagues = get_all_leagues()
league_selection = st.sidebar.multiselect("Select League(s)", all_leagues, default=all_leagues)


# --- Dynamic Query Selection Section (Moved to the top) ---
st.markdown("---")
st.header(" Statistics Visualization")

query_options = [q[0] for q in PREDEFINED_QUERIES]
selected_query_description = st.selectbox("Select from a list",query_options, key="dynamic_query_select")

# Find the selected query details
selected_query_index = query_options.index(selected_query_description)
_, sql_query, chart_type, x_axis, y_axis, color_by, tooltip_cols, param_type = PREDEFINED_QUERIES[selected_query_index]

query_params = ()
if param_type == 'player':
    param_value = st.selectbox(f"Select Player for '{selected_query_description}':", all_players_for_dropdown, key="dynamic_player_param")
    if param_value:
        query_params = (param_value,)
    else:
        st.info("Please select a player to run this query.")
        st.stop()
elif param_type == 'year':
    param_value = st.selectbox(f"Select Year for '{selected_query_description}':", all_years, key="dynamic_year_param")
    if param_value:
        query_params = (param_value,)
    else:
        st.info("Please select a year to run this query.")
        st.stop()

# Fetch data for the selected query
data_for_dynamic_viz = fetch_data(sql_query, query_params)

if not data_for_dynamic_viz.empty:
    st.subheader(f"Visualization: {selected_query_description}")

    chart = None
    if chart_type == "bar":
        chart = alt.Chart(data_for_dynamic_viz).mark_bar().encode(
            x=alt.X(x_axis, sort="-y", title=x_axis.split(':')[0].replace('_', ' ').title()),
            y=alt.Y(y_axis, title=y_axis.split(':')[0].replace('_', ' ').title()),
            color=alt.Color(color_by, legend=None) if color_by else alt.value('#4c78a8'),
            tooltip=tooltip_cols
        ).properties(
            title=selected_query_description
        ).interactive()
    elif chart_type == "line":
        chart = alt.Chart(data_for_dynamic_viz).mark_line(point=True).encode(
            x=alt.X(x_axis, title=x_axis.split(':')[0].replace('_', ' ').title()),
            y=alt.Y(y_axis, title=y_axis.split(':')[0].replace('_', ' ').title()),
            color=alt.Color(color_by) if color_by else alt.value('purple'),
            tooltip=tooltip_cols
        ).properties(
            title=selected_query_description
        ).interactive()
    elif chart_type == "scatter":
        chart = alt.Chart(data_for_dynamic_viz).mark_circle(size=60).encode(
            x=alt.X(x_axis, title=x_axis.split(':')[0].replace('_', ' ').title()),
            y=alt.Y(y_axis, title=y_axis.split(':')[0].replace('_', ' ').title()),
            color=alt.Color(color_by, scale=alt.Scale(scheme='category20'), legend=alt.Legend(title=color_by.split(':')[0].replace('_', ' ').title())) if color_by else alt.value('blue'),
            tooltip=tooltip_cols
        ).properties(
            title=selected_query_description
        ).interactive()

    if chart:
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("Could not generate chart for the selected query type.")

else:
    st.info("No data available for the selected query with current parameters.")



st.markdown("---") 
st.header("Key Performance Indicators")

# Fetch all batting average data for filtering (this will be done once)
batting_avg_query = "SELECT year, league, player, team, batting_average FROM batting_average_stats;"
all_batting_avg_df = fetch_data(batting_avg_query)

# Filtered DataFrame for Batting Average related charts
filtered_batting_avg_df = all_batting_avg_df[
    (all_batting_avg_df["year"] >= year_range[0]) &
    (all_batting_avg_df["year"] <= year_range[1]) &
    (all_batting_avg_df["batting_average"] >= avg_threshold) &
    (all_batting_avg_df["league"].isin(league_selection))
]

# visualization #1 : Top Hitters by Batting Average (Bar Chart)
st.subheader(f"Top 10 Hitters by Batting Average ({year_range[0]}-{year_range[1]})")
top_hitters_avg = (
    filtered_batting_avg_df.groupby("player", as_index=False)
    .agg({"batting_average": "max"})
    .sort_values("batting_average", ascending=False)
    .head(10)
)

if not top_hitters_avg.empty:
    bar_chart_avg = alt.Chart(top_hitters_avg).mark_bar(color='#4c78a8').encode(
        x=alt.X("player:N", sort="-y", title="Player"),
        y=alt.Y("batting_average:Q", title="Batting Average"),
        tooltip=["player", alt.Tooltip("batting_average", format=".3f")]
    ).properties(
        title=f"Top 10 Batting Average Leaders"
    ).interactive()
    st.altair_chart(bar_chart_avg, use_container_width=True)
else:
    st.info("No hitters meet the selected criteria for Batting Average.")


# --- Fixed Visualization 2: Best Batting Average Per Year (Line Chart) ---
st.subheader("Best Batting Average Per Year Trend")
top_avgs_yearly_query = "SELECT year, MAX(batting_average) AS max_batting_average FROM batting_average_stats WHERE league IN ? GROUP BY year ORDER BY year;"
leagues_str = "('" + "','".join(league_selection) + "')" if league_selection else "('N/A')"
top_avgs_yearly = fetch_data(top_avgs_yearly_query.replace('?', leagues_str)) 

top_avgs_yearly_filtered = top_avgs_yearly[
    (top_avgs_yearly["year"] >= year_range[0]) &
    (top_avgs_yearly["year"] <= year_range[1])
]

if not top_avgs_yearly_filtered.empty:
    line_chart_avg_yearly = alt.Chart(top_avgs_yearly_filtered).mark_line(point=True, color='purple').encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("max_batting_average:Q", title="Max Batting Average"),
        tooltip=["year", alt.Tooltip("max_batting_average", format=".3f")]
    ).properties(
        title=f"Max Batting Average by Year ({year_range[0]}-{year_range[1]})"
    ).interactive()
    st.altair_chart(line_chart_avg_yearly, use_container_width=True)
else:
    st.info("No yearly batting average data available for the selected filters.")


# --- Fixed Visualization 3: Team Wins Over Years (Line Chart) ---
st.subheader("Team Wins Over Years")
st.markdown("Track the winning performance of teams over time.")

all_teams_query = "SELECT DISTINCT team FROM wins_stats ORDER BY team;"
all_teams_df = fetch_data(all_teams_query)
all_teams_for_wins = all_teams_df['team'].tolist() if not all_teams_df.empty else []

selected_teams_for_wins = st.multiselect("Select Teams to Compare (Wins):", all_teams_for_wins, 
                                          default=all_teams_for_wins[:5] if all_teams_for_wins else [], key="fixed_team_wins_select")

if selected_teams_for_wins:
    placeholders = ','.join(['?' for _ in selected_teams_for_wins])
    team_wins_query = f"""
    SELECT year, team, wins
    FROM wins_stats
    WHERE team IN ({placeholders})
    ORDER BY year, team;
    """
    team_wins_data = fetch_data(team_wins_query, tuple(selected_teams_for_wins))

    if not team_wins_data.empty:
        line_chart_team_wins = alt.Chart(team_wins_data).mark_line(point=True).encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('wins:Q', title='Number of Wins'),
            color='team:N',
            tooltip=['year', 'team', 'wins']
        ).properties(
            title="Team Wins Over Years"
        ).interactive()
        st.altair_chart(line_chart_team_wins, use_container_width=True)
    else:
        st.info("No wins data available for the selected teams.")
else:
    st.info("Please select at least one team to view wins data.")


# Table of filtered batting average results 
st.subheader("Filtered Batting Average Data")
if not filtered_batting_avg_df.empty:
    display_df = filtered_batting_avg_df.copy()
    display_df["batting_average"] = display_df["batting_average"].round(3)
    st.dataframe(display_df)
else:
    st.info("No data available for the filtered batting average table.")


st.markdown("---")
st.markdown("Dashboard created using Streamlit, Pandas, Altair, and SQLite.")

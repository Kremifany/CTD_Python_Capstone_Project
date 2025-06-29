import sqlite3
import os
import sys

# list of pre-defined queries for the user to choose from
# Each tuple contains (description, SQL query)
QUERIES = [
    ("Top 10 Players by Home Runs (All Time)",
     "SELECT player, SUM(home_runs) AS total_home_runs FROM home_runs_stats GROUP BY player ORDER BY total_home_runs DESC LIMIT 10;"),
    ("Top 10 Players by Batting Average (Min 100 AB, All Time)",
     "SELECT player, AVG(batting_average) AS avg_batting_average FROM batting_average_stats WHERE year IN (SELECT year FROM batting_average_stats GROUP BY year HAVING COUNT(player) >= 100) GROUP BY player ORDER BY avg_batting_average DESC LIMIT 10;"),
    ("Player's Home Runs Over Years (e.g., 'Babe Ruth')",
     "SELECT year, home_runs FROM home_runs_stats WHERE player = ? ORDER BY year;"),
    ("Player's Strikeouts Over Years (e.g., 'Jim Devlin')",
     "SELECT year, strikeouts FROM strikeouts_stats WHERE player = ? ORDER BY year;"),
    ("Teams with Most Wins in a Specific Year (e.g., 1927)",
     "SELECT team, wins FROM wins_stats WHERE year = ? ORDER BY wins DESC LIMIT 5;"),
    ("Total Home Runs per Year (All Leagues)",
     "SELECT year, SUM(home_runs) AS total_home_runs FROM home_runs_stats GROUP BY year ORDER BY year;"),
    ("Average Batting Average per Year (All Leagues)",
     "SELECT year, AVG(batting_average) AS avg_batting_average FROM batting_average_stats GROUP BY year ORDER BY year;"),
    ("Players with Home Runs and Strikeouts in the same year (e.g., year 1920)",
     "SELECT H.year, H.player, H.home_runs, S.strikeouts FROM home_runs_stats AS H JOIN strikeouts_stats AS S ON H.player = S.player AND H.year = S.year WHERE H.year = ? ORDER BY H.player;"),
    ("Top 5 Teams by Stolen Bases (All Time)",
     "SELECT team, SUM(stolen_bases) AS total_stolen_bases FROM stolen_bases_stats GROUP BY team ORDER BY total_stolen_bases DESC LIMIT 5;"),
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
     ) AS combined_stats GROUP BY year ORDER BY year;"""),
    ("Compare Home Runs and RBIs for Players in a Specific Year",
     "SELECT HR.year, HR.player, HR.home_runs, RBI.rbi FROM home_runs_stats AS HR JOIN rbi_stats AS RBI ON HR.player = RBI.player AND HR.year = RBI.year WHERE HR.year = ? ORDER BY HR.home_runs DESC;")
]

def run_query_program(db_path):
    """
    Connects to the SQLite database and allows users to run pre-defined SQL queries
    via a numbered menu.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Connected to SQLite database: {db_path}\n")
        print("Welcome to the Baseball Stats Dashboard Query Tool!")
        print("Select a query by entering its number, or type 'exit' to quit.")

        while True:
            print("\n=== Available Queries ===")
            for i, (description, _) in enumerate(QUERIES):
                print(f"{i + 1}. {description}")
            print("=========================")
            
            user_input = input(f"Enter query number (1-{len(QUERIES)}) or 'exit': ").strip()

            if user_input.lower() == 'exit':
                print("Exiting query tool. Goodbye!")
                break
            
            try:
                query_number = int(user_input)
                if not 1 <= query_number <= len(QUERIES):
                    print(f"Invalid query number. Please enter a number between 1 and {len(QUERIES)}.")
                    continue

                description, sql_query = QUERIES[query_number - 1]
                print(f"\n=== Running: {description} ===")

                # Check if the query requires an additional parameter
                if '?' in sql_query:
                    param_prompt = "Enter the required value for this query (e.g., Player Name or Year): "
                    if query_number == 3: # Player's Home Runs
                        param_prompt = "Enter Player Name (e.g., 'Babe Ruth'): "
                    elif query_number == 4: # Player's Strikeouts
                        param_prompt = "Enter Player Name (e.g., 'Jim Devlin'): "
                    elif query_number == 5: # Teams with Most Wins
                        param_prompt = "Enter Year (e.g., 1927): "
                    elif query_number == 8: # HR and Strikeouts in same year
                        param_prompt = "Enter Year (e.g., 1920): "
                    elif query_number == 11: # Compare HR and RBIs
                        param_prompt = "Enter Year (e.g., 1920): "


                    param = input(param_prompt).strip()
                    if not param:
                        print("No value entered. Skipping query.")
                        continue
                    # convert year parameters to int
                    if query_number in [5, 8, 11]:
                        try:
                            param = int(param)
                        except ValueError:
                            print("Invalid year entered. Please enter a number.")
                            continue
                    cursor.execute(sql_query, (param,))
                else:
                    cursor.execute(sql_query)

                # Fetch and display results
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                if not rows:
                    print("No results found for this query.")
                else:
                    # Determine optimal column width
                    col_widths = [len(col) for col in columns]
                    for row in rows:
                        for i, item in enumerate(row):
                            col_widths[i] = max(col_widths[i], len(str(item)))
                    
                    # Add padding
                    padded_widths = [width + 2 for width in col_widths] # +2 for padding

                    # Print header
                    header_line = " | ".join(f"{col:<{padded_widths[i]}}" for i, col in enumerate(columns))
                    print("=" * len(header_line))
                    print(header_line)
                    print("=" * len(header_line))

                    # Print rows
                    for row in rows:
                        print(" | ".join(f"{str(item):<{padded_widths[i]}}" for i, item in enumerate(row)))
                    print("-" * len(header_line))

            except ValueError:
                print("Invalid input. Please enter a number or 'exit'.")
            except sqlite3.OperationalError as e:
                print(f"SQL Error: {e}")
                print("There might be an issue with the query or database schema. Please check tables/columns.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        print(f"Please make sure '{db_path}' exists and is accessible.")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    db_directory = "database"
    db_file_name = "baseball_stats.db"
    full_db_path = os.path.join(db_directory, db_file_name)

    # see if database file exists before trying to connect
    if not os.path.exists(full_db_path):
        print(f"Error: Database file '{full_db_path}' not found.")
        print("Please make sure that Database is created !")
        sys.exit(1) 

    run_query_program(full_db_path)

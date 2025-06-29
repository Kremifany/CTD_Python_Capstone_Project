1. Web Scraping Program
Goal: Scrape data from Major League Baseball History.
Steps:
Uses Selenium to retrieve the data.
Extracts relevant details (year, event names, statistics).
Saves the raw data into CSV format for each dataset.

2. CleaningCsv files program
Goal: To transform raw, potentially messy, and inconsistent data into a high-quality, accurate, consistent, and usable dataset.
Steps:
Load Data: (Reads CSV files)
Validate Required: (Checks for 'Year', 'League', and metric column)
Filter Invalid: (Removes rows with missing/bad 'Year', 'League', or metric values)
Convert Types: (Transforms 'Year' to int, metric to float)
Clean Text: (Strips whitespace, removes hyphens from 'Player'/'Team')
Filter Zeros: (Removes rows where metric is 0 or NaN after conversion)
Save Cleaned: (Writes processed data to new CSVs)
Log Removed: (Saves discarded rows to a separate log file)

3. Database Import Program
Goal: Import the CSV files into a SQLite database.
Steps:
Creates a program that imports each CSV as a separate table in the database.
Ensure proper data types (numeric, date, etc.) during the import.
Check for errors during the import process.

5. Database Query Program
Goal: Provide an interactive command-line interface to explore baseball statistics
by running pre-defined SQL queries against the centralized SQLite database.
Steps:
Database Connection: Establishes a connection to the baseball_stats.db file.
Display Query Options: Presents a numbered menu of pre-defined baseball statistics queries to the user.
User Input Handling: Accepts the user's selection and prompts for any required parameters (e.g., player name, year).
Execute SQL Queries: Runs the corresponding SQL query against the connected database.
Display Formatted Results: Fetches and presents the query results in a clear, tabular format on the command line.
Error Management: Handles potential database connection issues, invalid user input, or SQL execution errors.
Exit Functionality: Allows the user to quit the program cleanly.

5. Dashboard Program
Goal: Create an interactive web-based dashboard using Streamlit to visualize baseball statistics from the processed data,
allowing users to explore trends and insights.
Steps:
Establish Database Connection: Connects to the baseball_stats.db to fetch data.
Fetch Data: Implements functions to query the database and retrieve relevant statistics.
Global Filters (Sidebar): Provides interactive sliders for Year Range and Minimum Batting Average, and a multi-select for League(s) to filter the data.
Dynamic Query Visualization:
Presents a dropdown menu for users to select from various pre-defined analytical queries (e.g., "Top Home Run Players," "Total Home Runs per Year").
Dynamically prompts for additional parameters (player name, year) if required by the selected query.
Generates and displays appropriate visualizations (bar charts, line charts) using Altair based on the selected query and parameters.
Fixed Visualizations (KPIs):
Top Hitters by Batting Average: Displays a bar chart of the top 10 players based on batting average, filtered by global selections.
Best Batting Average Per Year Trend: Shows a line chart illustrating the highest batting average recorded each year, filtered by selected leagues and year range.
Team Wins Over Years: Allows users to select multiple teams and visualizes their annual win totals as a comparative line chart.
Display Filtered Data Table: Presents a tabular view of the filtered batting average data, providing raw numbers alongside visualizations.
Error Handling: Manages cases where the database is not found, queries fail, or no data is available for selected filters.
Deployment (External Step): Mentions the goal of deploying the dashboard on a public platform (e.g., Streamlit Cloud/Render) for accessibility.

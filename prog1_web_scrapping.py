# Web Scraping Program:
# Scrape data from the Major League Baseball History website
# Assemble it into DataFrames
# Store the data as several CSV files.

import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up WebDriver with headless options
browser_driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
browser_options = webdriver.ChromeOptions()

browser_options.add_argument('--headless')  # Enable headless mode
browser_options.add_argument('--disable-gpu')  # Optional, recommended for Windows
browser_options.add_argument('--window-size=1920x1080')  # Optional, set window size
browser_driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=browser_options)

# Navigate to the initial statistics index page
initial_stats_url = "https://www.baseball-almanac.com/yearly/yr1955a.shtml"
browser_driver.get(initial_stats_url)

# Wait for the main content tables to load
wait = WebDriverWait(browser_driver, 10)

# Wait for the main content tables to load
wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ba-table table.boxed"))
)

# Find all data tables on the initial page
all_index_tables = browser_driver.find_elements(By.CSS_SELECTOR, "div.ba-table table.boxed")
print(f"Found {len(all_index_tables)} data tables on the index page.")

# List to store all scraped metric links from the index page
all_metric_links = []

# Loop through each table to extract metric links
for table_idx, current_index_table in enumerate(all_index_tables):
    print(f"Processing index table {table_idx+1} of {len(all_index_tables)}")
    try:
        # Find all <a> elements within specific cells (td.datacolBlue) in the current table
        metric_link_elements = current_index_table.find_elements(By.CSS_SELECTOR, "td.datacolBlue a")
        
        # Extract the text and href for each metric link
        current_table_metric_info = [(elem.text.strip(), elem.get_attribute("href")) for elem in metric_link_elements]
        all_metric_links.extend(current_table_metric_info)
        print(f"Extracted {len(current_table_metric_info)} metric links from this table.")
    except Exception as e:
        print(f"Warning: Could not find metric links in index table {table_idx+1}. Error: {e}")

# Define the folder for saving output CSVs
output_directory = "baseball_stats_csvs"
os.makedirs(output_directory, exist_ok=True)

# Print all collected metric links for verification
print("\n--- All Collected Metric Links from Index Page ---")
for metric_item in all_metric_links :
    print(metric_item)
print("--------------------------------------------------")

def scrape_individual_metric_page(metric_category_name, metric_page_url):
    """
    Navigates to a specific metric page, scrapes the data, and saves it to a CSV.
    """
    print(f"\nScraping data for: '{metric_category_name}' from URL: {metric_page_url}")
    browser_driver.get(metric_page_url)
    time.sleep(2)

    collected_metric_data = [] # List to store rows of data from the current metric page

    # Find tables on the individual metric page
    metric_data_tables = browser_driver.find_elements(By.CSS_SELECTOR, "div.ba-table table.boxed")
    
    if metric_data_tables:
        # Assuming the first 'boxed' table on the individual metric page contains the desired data
        primary_data_table = metric_data_tables[0] 
        data_rows = primary_data_table.find_elements(By.TAG_NAME, "tr")
        
        for data_row in data_rows:
            try:
                data_cells = data_row.find_elements(By.TAG_NAME, "td")
                # Check for the expected 8 columns (AL and NL stats side-by-side)
                if len(data_cells) == 8:
                    # Extract American League data
                    al_year = data_cells[0].text.strip()
                    al_player = data_cells[1].text.strip()
                    al_stat_value = data_cells[2].text.strip().split()[0] # Take first part for stat
                    al_team = data_cells[3].text.strip()
                    
                    # Extract National League data
                    nl_year = data_cells[4].text.strip()
                    nl_player = data_cells[5].text.strip()
                    nl_stat_value = data_cells[6].text.strip().split()[0] # Take first part for stat
                    nl_team = data_cells[7].text.strip()
                    
                    # Append data for both leagues to the collection
                    collected_metric_data.append([al_year, "AL", al_player, al_team, al_stat_value])
                    collected_metric_data.append([nl_year, "NL", nl_player, nl_team, nl_stat_value])
            except Exception as e:
                print(f":warning: Skipped a row on '{metric_category_name}' page due to error: {e}")
    else:
        print(f":warning: No expected data tables found on page: {metric_page_url}")

    # Construct the output CSV filename and path
    output_filename_base = metric_category_name.lower().replace(" ", "_").replace("/", "_") # Handle slashes in names
    output_csv_filename = f"{output_filename_base}_stats.csv"
    output_file_path = os.path.join(output_directory, output_csv_filename)
    
    # Write the collected data to a CSV file
    with open(output_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write header row (generic for all metrics)
        csv_writer.writerow(["Year", "League", "Player", "Team", metric_category_name])
        # Write all collected data rows
        csv_writer.writerows(collected_metric_data)
        
    print(f":white_check_mark: Successfully saved data to: {output_csv_filename}")

# ========== EXECUTE SCRAPING FOR ALL COLLECTED METRICS ==========
for metric_name_text, metric_link_url in all_metric_links :
    scrape_individual_metric_page(metric_name_text, metric_link_url)

# Close the browser when done
browser_driver.quit()
print("\nScraping complete and browser closed.")
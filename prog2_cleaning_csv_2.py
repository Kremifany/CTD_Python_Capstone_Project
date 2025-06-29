import pandas as pd
import os
import re

# CSV files to process
baseball_stats_csvs = [
    "base_on_balls_stats.csv",
    "batting_average_stats.csv",
    "complete_games_stats.csv",
    "doubles_stats.csv",
    "era_stats.csv",
    "games_stats.csv",
    "hits_stats.csv",
    "home_runs_stats.csv",
    "on_base_percentage_stats.csv",
    "rbi_stats.csv",
    "runs_stats.csv",
    "saves_stats.csv",
    "shutouts_stats.csv",
    "slugging_average_stats.csv",
    "stolen_bases_stats.csv",
    "strikeouts_stats.csv",
    "total_bases_stats.csv",
    "triples_stats.csv",
    "winning_percentage_stats.csv",
    "wins_stats.csv"
]

def clean_stats_csv(input_filepath):

    removed_df_for_log = pd.DataFrame() # Initialize an empty DataFrame for removed rows
    
    try:

        df_raw = pd.read_csv(input_filepath, header=0, encoding='utf-8', dtype=str)

        if not df_raw.columns.empty:
            metric_column_name_from_header = df_raw.columns[-1].strip()
        else:
            print(f"Warning: No columns found in {os.path.basename(input_filepath)}. Skipping.")
            return None, pd.DataFrame()
        
        # Get the actual column name for the metric from the DataFrame's columns
        actual_metric_column = None
        for col in df_raw.columns:
            if col.lower().replace(' ', '') == metric_column_name_from_header.lower().replace(' ', ''):
                actual_metric_column = col
                break
        
        if actual_metric_column is None:
            # Fallback if metric column name not found exactly, assume last column
            actual_metric_column = df_raw.columns[-1]
            print(f"Warning: Could not find exact metric column '{metric_column_name_from_header}'. Using last column '{actual_metric_column}'.")


        # before filtering to be sure all column are there
        required_cols = ['Year', 'League', actual_metric_column]
        if not all(col in df_raw.columns for col in required_cols):
            print(f"Error: Missing one or more required columns ({required_cols}) in {os.path.basename(input_filepath)}. Skipping.")
            return None, pd.DataFrame()

        valid_year = df_raw["Year"].notna() & (df_raw["Year"].str.lower() != "year")
        valid_league = df_raw["League"].str.strip().str.upper().isin(["AL", "NL"])
        valid_metric_value = df_raw[actual_metric_column].notna() & \
                             df_raw[actual_metric_column].astype(str).str.contains(r"\d", na=False)

        # Combine all valid conditions
        is_valid_row = valid_year & valid_league & valid_metric_value

        # Separate valid and removed rows
        removed_df_for_log = df_raw[~is_valid_row].copy() # Rows that fail any validation
        cleaned_df = df_raw[is_valid_row].copy() # Rows that pass all validation

        # Add a 'source_file' column to removed rows for logging
        removed_df_for_log['source_file'] = os.path.basename(input_filepath)

        # --- Data Cleaning and Type Conversion ---
        if cleaned_df.empty:
            print(f"No valid data remaining in {os.path.basename(input_filepath)} after initial filtering.")
            return None, removed_df_for_log

        # Convert 'Year' to integer
        cleaned_df["Year"] = pd.to_numeric(cleaned_df["Year"], errors='coerce').astype(int)

        # Extract numeric part and convert metric column to float
        cleaned_df[actual_metric_column] = cleaned_df[actual_metric_column].astype(str).str.extract(r"([\d.]+)", expand=False)
        cleaned_df[actual_metric_column] = pd.to_numeric(cleaned_df[actual_metric_column], errors='coerce')

        # Clean 'Player' and 'Team' columns
        if 'Player' in cleaned_df.columns:
            cleaned_df["Player"] = cleaned_df["Player"].astype(str).str.replace('-', '', regex=False).str.strip()
        if 'Team' in cleaned_df.columns:
            cleaned_df["Team"] = cleaned_df["Team"].astype(str).str.replace('-', '', regex=False).str.strip()

        # Remove rows where the metric value is NaN after conversion or 0
        cleaned_df = cleaned_df[cleaned_df[actual_metric_column].notna()]
        cleaned_df = cleaned_df[cleaned_df[actual_metric_column] > 0] 

        return cleaned_df, removed_df_for_log

    except FileNotFoundError:
        print(f"Error: File not found at {input_filepath}")
        return None, pd.DataFrame()
    except pd.errors.EmptyDataError:
        print(f"Error: {input_filepath} is empty or malformed.")
        return None, pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred while processing {input_filepath}: {e}")
        return None, pd.DataFrame()

if __name__ == "__main__":
    input_csvs_base_directory = 'baseball_stats_csvs' 

    # removed rows from all files
    all_removed_data_list = [] 
    processed_files_count = 0

    print("Starting batch CSV cleaning process...")

    for csv_filename in baseball_stats_csvs:
        input_full_path = os.path.join(input_csvs_base_directory, csv_filename)
        print(f"\n--- Processing: {csv_filename} ---")
        
        cleaned_df, removed_df = clean_stats_csv(input_full_path)

        # add removed rows to list
        if not removed_df.empty:
            all_removed_data_list.append(removed_df)

        if cleaned_df is not None and not cleaned_df.empty:
            # Construct the output filename: original_name_cleaned.csv
            base_name, ext = os.path.splitext(csv_filename)
            output_filename = f"{base_name}_cleaned{ext}"
            output_full_path = os.path.join(input_csvs_base_directory, output_filename) # Save in same directory
            
            cleaned_df.to_csv(output_full_path, index=False, encoding='utf-8')
            print(f"Successfully saved cleaned data to: {output_filename}")
            processed_files_count += 1
        elif cleaned_df is not None and cleaned_df.empty:
            print(f"No valid data remaining in {csv_filename} after cleaning. Skipping save.")
        else:
            print(f"Failed to clean {csv_filename}.")
    
    if all_removed_data_list:
        combined_removed_df = pd.concat(all_removed_data_list, ignore_index=True)
        for col in combined_removed_df.columns:
            combined_removed_df[col] = combined_removed_df[col].astype(str)
            
        removed_log_path = os.path.join(input_csvs_base_directory, "all_removed_rows_log.txt")
        combined_removed_df.to_csv(removed_log_path, index=False, sep="\t")
        print(f"\n===== Batch cleaning complete. =====")
        print(f"Processed {processed_files_count} files successfully.")
        print(f"A log of all removed rows can be found at: {removed_log_path}")
        print(f"\n ======= Sample of Removed rows (first 10) =======\n {combined_removed_df.head(10).to_string(index=False)}")
    else:
        print("\n ====== Batch cleaning complete. ======")
        print(f"Processed {processed_files_count} files. No rows were removed across all files.")
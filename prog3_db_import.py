import pandas as pd
import sqlite3
import os
import re

def infer_sqlite_type(series):

    # Attempt to convert to numeric (integer or float)
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"
        return "REAL"

    # Attempt to convert to datetime
    try:
        if not series.empty and pd.to_datetime(series, errors='coerce').notna().any():
            return "TEXT" 
    except Exception:
        pass # Not a date column

    # Default to TEXT for strings and other types
    return "TEXT"

def clean_column_name(col_name):
    """
    Cleans a column name to be suitable for SQLite.
    Replaces spaces and special characters with underscores, converts to lowercase.
    """
    # Replace non-alphanumeric characters (except underscore) with underscore
    cleaned_name = re.sub(r'[^a-zA-Z0-9_]', '_', col_name)
    # Replace multiple underscores with a single underscore
    cleaned_name = re.sub(r'_{2,}', '_', cleaned_name)
    # Remove leading/trailing underscores
    cleaned_name = cleaned_name.strip('_')
    # Convert to lowercase
    cleaned_name = cleaned_name.lower()
    return cleaned_name

def import_csvs_to_sqlite(csv_dir, db_name="baseball_stats.db"):
    """
    Imports all CSV files from a specified directory into a SQLite database.
    Only CSV files with '_cleaned' in their name will be processed.
    Each CSV file becomes a separate table, with '_cleaned' removed from its name.
    Each table will have a composite primary key: ('player', 'year').
    """
    # Create the database directory if it doesn't exist
    db_dir = "database"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, db_name)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print(f"Connected to SQLite database: {db_path}")

        # Filter for CSV files that contain '_cleaned' in their name
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv') and '_cleaned' in f]

        if not csv_files:
            print(f"No CSV files ending with '_cleaned.csv' found in directory: {csv_dir}")
            return

        for csv_file in csv_files:
            file_path = os.path.join(csv_dir, csv_file)
            
            # Extract base name and remove '_cleaned' before cleaning
            base_name = os.path.splitext(csv_file)[0] 
            if '_cleaned' in base_name:
                base_name = base_name.replace('_cleaned', '')
            
            table_name = clean_column_name(base_name) # Clean table name

            print(f"\n==== Importing '{csv_file}' into table '{table_name}' ====")
            try:
                # read csv file into andas DataFrame
                df = pd.read_csv(file_path)

                # Clean column names in the DataFrame
                original_columns = df.columns.tolist() # Keep original for checks
                df.columns = [clean_column_name(col) for col in df.columns]
                cleaned_columns = df.columns.tolist() # Store cleaned for checks

                # Check for required primary key columns
                pk_cols = ["player", "year"] 
                missing_pk_cols = [col for col in pk_cols if col not in cleaned_columns]

                if missing_pk_cols:
                    print(f"Skipping '{csv_file}'. Missing required primary key columns: {missing_pk_cols}. "
                          f"Available columns (cleaned): {cleaned_columns}")
                    continue # next CSV file

                if df[pk_cols].isnull().any().any():
                    print(f"Warning: Primary key columns ('{pk_cols[0]}', '{pk_cols[1]}') in '{csv_file}' contain NULL values. "
                          "SQLite PRIMARY KEY constraint will cause errors if NULLs are present. Skipping table creation/import.")
                    continue


                columns_definition = []
                for original_col_name, cleaned_col_name in zip(original_columns, cleaned_columns):
                    sql_type = infer_sqlite_type(df[cleaned_col_name])
                    
                    # Add NOT NULL to primary key columns in the definition
                    if cleaned_col_name in pk_cols:
                        columns_definition.append(f'"{cleaned_col_name}" {sql_type} NOT NULL')
                    else:
                        columns_definition.append(f'"{cleaned_col_name}" {sql_type}')

                create_table_sql = (
                    f'CREATE TABLE IF NOT EXISTS "{table_name}" ('
                    f'{", ".join(columns_definition)}, '
                    f'PRIMARY KEY ("{pk_cols[0]}", "{pk_cols[1]}"))'#for year and player to be a primary key
                )
                
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit() 

                print(f"Table '{table_name}' created or ensured with composite primary key ('player', 'year').")

                df.to_sql(table_name, conn, if_exists='append', index=False)

                print(f"Successfully imported data from '{csv_file}' into table '{table_name}'.")

            except pd.errors.EmptyDataError:
                print(f"Skipping '{csv_file}' as it is empty.")
            except FileNotFoundError:
                print(f"Error: File not found at '{file_path}'.")
            except sqlite3.Error as e:
                print(f"SQLite error during import of '{csv_file}': {e}")
            except Exception as e:
                print(f"Error occurred during import of '{csv_file}': {e}")

    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    csv_directory = "baseball_stats_csvs"

    import_csvs_to_sqlite(csv_directory)

    print("\n--- Verifying database tables ---")
    db_path = os.path.join("database", "baseball_stats.db")
    if os.path.exists(db_path):
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
            tables_info = cursor.fetchall()
            print("Tables in the database and their CREATE TABLE statements:")
            for table_name, create_sql in tables_info:
                print(f"\nTable: {table_name}")
                print(f"  CREATE SQL:\n{create_sql}")
                
                pk_match = re.search(r"PRIMARY KEY\s*\(([^)]+)\)", create_sql, re.IGNORECASE)
                if pk_match:
                    pk_columns_str = pk_match.group(1).replace('"', '').replace("'", '').strip()
                    pk_columns = [col.strip().lower() for col in pk_columns_str.split(',')]
                    if "player" in pk_columns and "year" in pk_columns:
                        print(f"  Confirmed: Composite Primary Key ('player', 'year') is defined.")
                    else:
                        print(f"  Warning: Primary key detected as ({pk_columns_str}), but may not be ('player', 'year').")
                else:
                    print(f"  No explicit PRIMARY KEY constraint found in CREATE SQL.")
                
        except sqlite3.Error as e:
            print(f"Error verifying database: {e}")
        finally:
            if conn:
                conn.close()
    else:
        print("Database file not found. Import may have failed.")

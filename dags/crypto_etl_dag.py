import json
import pandas as pd
import requests
from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

@dag(
    dag_id='crypto_market_etl_pipeline',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    doc_md="""### Crypto Market ETL Pipeline""",
    tags=['crypto', 'api', 'etl']
)
def crypto_etl_dag():
    @task
    def extract_crypto_data():
        """Fetches data from the CoinGecko API."""
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 250, 'page': 1}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @task
    def transform_data(raw_data: list):
        """
        Cleans and structures the raw JSON data into a pandas DataFrame.
        """
        df = pd.DataFrame(raw_data)

        # 1. Select only the required columns
        required_columns = [
            'id', 'symbol', 'name', 'current_price', 'market_cap',
            'total_volume', 'price_change_percentage_24h'
        ]
        df = df[required_columns]

        # 2. Rename columns for clarity in the database
        df.rename(columns={'price_change_percentage_24h': 'price_change_24h'}, inplace=True)

        # 3. Handle potential missing values
        df.fillna({
            'current_price': 0,
            'market_cap': 0,
            'total_volume': 0,
            'price_change_24h': 0
        }, inplace=True)
        
        # 4. Ensure correct data types
        df['market_cap'] = df['market_cap'].astype('int64')
        df['total_volume'] = df['total_volume'].astype('int64')

        # 5. Add a 'last_updated' timestamp
        df['last_updated'] = datetime.utcnow()
        
        # --- NEW LINE ADDED ---
        # 6. Convert the timestamp to a string to make it JSON serializable
        df['last_updated'] = df['last_updated'].astype(str)
        # --------------------

        # Convert DataFrame to a list of dictionaries for loading
        return df.to_dict(orient='records')
    @task
    def load_to_postgres(transformed_data: list):
        """Loads the transformed data into PostgreSQL."""
        if not transformed_data:
            print("No data to load.")
            return

        pg_hook = PostgresHook(postgres_conn_id='postgres_crypto_dw_conn')
        target_table = 'daily_crypto_metrics'

        # SQL to create table if it doesn't exist
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
            id VARCHAR(255) PRIMARY KEY, symbol VARCHAR(50), name VARCHAR(255),
            current_price NUMERIC(20, 10), market_cap BIGINT, total_volume BIGINT,
            price_change_24h NUMERIC(10, 4), last_updated TIMESTAMP WITH TIME ZONE
        );
        """
        pg_hook.run(create_table_sql)
        
        # Truncate the table using a standard SQL command
        pg_hook.run(f"TRUNCATE TABLE {target_table};")
        print(f"Table '{target_table}' truncated.")
      
        
        # Define columns for insert_rows
        columns = [
            'id', 'symbol', 'name', 'current_price', 'market_cap', 
            'total_volume', 'price_change_24h', 'last_updated'
        ]
        
        # Convert list of dicts to list of tuples
        rows = [[row[col] for col in columns] for row in transformed_data]
        
        pg_hook.insert_rows(table=target_table, rows=rows, target_fields=columns)
        print(f"Successfully loaded {len(rows)} records.")

        
    # Define task dependencies
    raw_data = extract_crypto_data()
    transformed_data = transform_data(raw_data)
    load_to_postgres(transformed_data)

crypto_etl_dag()
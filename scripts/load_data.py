#!/usr/bin/env python3

import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def create_database_url():
    """Create database URL from environment variables or use SQLite as fallback"""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Fallback to SQLite
    return 'sqlite:///nuclear_plants.db'

def load_csv_data():
    """Load data from CSV files"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # Load countries
    countries_df = pd.read_csv(os.path.join(data_dir, '1countries.csv'), sep=';')
    countries_df.columns = ['id', 'name']
    
    # Load nuclear power plant status types
    status_df = pd.read_csv(os.path.join(data_dir, '2nuclear_power_plant_status_type.csv'), sep=';')
    
    # Load nuclear reactor types
    reactor_types_df = pd.read_csv(os.path.join(data_dir, '3nuclear_reactor_type.csv'), sep=';')
    
    # Load nuclear power plants
    plants_df = pd.read_csv(os.path.join(data_dir, '4nuclear_power_plants.csv'), sep=';')
    
    return countries_df, status_df, reactor_types_df, plants_df

def main():
    """Main function to load data into database"""
    print("Loading nuclear power plant data...")
    
    # Create database engine
    database_url = create_database_url()
    print(f"Using database: {database_url}")
    engine = create_engine(database_url)
    
    try:
        # Load CSV data
        countries_df, status_df, reactor_types_df, plants_df = load_csv_data()
        
        # Load countries
        print("Loading countries...")
        countries_df.to_sql('countries', engine, if_exists='replace', index=False)
        
        # Load status types
        print("Loading nuclear power plant status types...")
        status_df.to_sql('nuclear_power_plant_status_types', engine, if_exists='replace', index=False)
        
        # Load reactor types
        print("Loading nuclear reactor types...")
        reactor_types_df.to_sql('nuclear_reactor_types', engine, if_exists='replace', index=False)
        
        # Load nuclear power plants
        print("Loading nuclear power plants...")
        # Clean and prepare plants data
        plants_df = plants_df.replace('', None)  # Replace empty strings with None
        
        # Handle date columns
        date_columns = ['ConstructionStartAt', 'OperationalFrom', 'OperationalTo', 'LastUpdatedAt']
        for col in date_columns:
            if col in plants_df.columns:
                plants_df[col] = pd.to_datetime(plants_df[col], errors='coerce')
        
        plants_df.to_sql('nuclear_power_plants', engine, if_exists='replace', index=False)
        
        print(f"Successfully loaded:")
        print(f"- {len(countries_df)} countries")
        print(f"- {len(status_df)} status types")
        print(f"- {len(reactor_types_df)} reactor types")
        print(f"- {len(plants_df)} nuclear power plants")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

if __name__ == "__main__":
    main()
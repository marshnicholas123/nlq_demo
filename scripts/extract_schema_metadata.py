#!/usr/bin/env python3
"""
Extract schema metadata from nuclear_plants.db for BM25 Retriever embedding.

This script extracts detailed schema information from all tables in the database
and formats them as separate documents suitable for BM25 retrieval.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any
from datetime import datetime


class SchemaExtractor:
    """Extract and format database schema metadata for BM25 retrieval"""

    def __init__(self, db_path: str):
        """
        Initialize schema extractor

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database

        Returns:
            List of table names
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")

        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default_value': row[4],
                'pk': row[5]
            })
        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get foreign key information for a table

        Args:
            table_name: Name of the table

        Returns:
            List of foreign key information dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")

        foreign_keys = []
        for row in cursor.fetchall():
            foreign_keys.append({
                'id': row[0],
                'seq': row[1],
                'table': row[2],
                'from': row[3],
                'to': row[4],
                'on_update': row[5],
                'on_delete': row[6],
                'match': row[7]
            })
        return foreign_keys

    def infer_column_description(self, table_name: str, column_name: str,
                                 column_type: str, is_pk: bool,
                                 foreign_keys: List[Dict[str, Any]]) -> str:
        """
        Infer a description for a column based on its name and properties

        Args:
            table_name: Name of the table
            column_name: Name of the column
            column_type: Data type of the column
            is_pk: Whether this is a primary key
            foreign_keys: List of foreign key relationships

        Returns:
            Inferred description string
        """
        # Check if this column is a foreign key
        fk_info = None
        for fk in foreign_keys:
            if fk['from'] == column_name:
                fk_info = fk
                break

        # Primary key
        if is_pk:
            return f"Primary key, unique identifier for each {table_name.replace('_', ' ').rstrip('s')}"

        # Foreign key
        if fk_info:
            ref_table = fk_info['table']
            return f"Foreign key reference to {ref_table} table"

        # Specific column patterns
        column_lower = column_name.lower()

        if column_lower == 'name':
            return f"Name/title of the {table_name.replace('_', ' ').rstrip('s')}"
        elif column_lower == 'type':
            return "Type/category classification"
        elif column_lower == 'description':
            return "Detailed text description"
        elif 'latitude' in column_lower:
            return "Geographic latitude coordinate"
        elif 'longitude' in column_lower:
            return "Geographic longitude coordinate"
        elif 'code' in column_lower and 'country' in column_lower:
            return "ISO 3166-1 alpha-2 country code"
        elif 'status' in column_lower:
            if 'id' in column_lower:
                return "Current lifecycle status (FK to nuclear_power_plant_status_type)"
            return "Current status or state"
        elif 'reactor' in column_lower:
            if 'type' in column_lower and 'id' in column_lower:
                return "Technology classification (FK to nuclear_reactor_type)"
            elif 'model' in column_lower:
                return "Specific reactor model/variant"
        elif 'construction' in column_lower and 'start' in column_lower:
            return "Date when construction began"
        elif 'operational' in column_lower:
            if 'from' in column_lower:
                return "Date when plant began commercial operation"
            elif 'to' in column_lower:
                return "Date when plant ceased operation (NULL if still operating)"
        elif 'capacity' in column_lower:
            return "Net electrical capacity in megawatts (MW)"
        elif 'source' in column_lower:
            return "Data source reference"
        elif 'updated' in column_lower or 'lastupdated' in column_lower:
            return "Timestamp of last data update"
        elif column_lower == 'id':
            return f"Unique identifier for {table_name.replace('_', ' ')}"

        # Default description
        return f"{column_name.replace('_', ' ').title()}"

    def map_sqlite_to_standard_type(self, sqlite_type: str) -> str:
        """
        Map SQLite type to a more standard SQL type representation

        Args:
            sqlite_type: SQLite data type

        Returns:
            Standardized type name
        """
        type_upper = sqlite_type.upper()

        if 'INT' in type_upper:
            if 'BIG' in type_upper:
                return 'INT'
            return 'INT'
        elif 'TEXT' in type_upper or 'CHAR' in type_upper:
            return 'VARCHAR(255)'
        elif 'FLOAT' in type_upper or 'REAL' in type_upper or 'DOUBLE' in type_upper:
            if 'latitude' in sqlite_type.lower() or 'longitude' in sqlite_type.lower():
                return 'DECIMAL(10,6)'
            return 'INT'
        elif 'DATE' in type_upper or 'TIME' in type_upper:
            return 'DATETIME'

        return sqlite_type

    def generate_markdown_schema(self, table_name: str) -> str:
        """
        Generate markdown formatted schema document for a table

        Args:
            table_name: Name of the table

        Returns:
            Markdown formatted schema string
        """
        columns = self.get_table_info(table_name)
        foreign_keys = self.get_foreign_keys(table_name)

        # Build markdown table
        md = f"# {table_name}\n\n"
        md += f"**Table**: {table_name}\n\n"
        md += "**Schema**:\n\n"
        md += "| Column Name | Data Type | Nullable | Description |\n"
        md += "|------------|-----------|----------|-------------|\n"

        for col in columns:
            col_name = col['name']
            col_type = self.map_sqlite_to_standard_type(col['type'])
            nullable = "YES" if not col['notnull'] else "NO"
            description = self.infer_column_description(
                table_name, col_name, col['type'],
                bool(col['pk']), foreign_keys
            )

            md += f"| {col_name} | {col_type} | {nullable} | {description} |\n"

        return md

    def extract_all_schemas(self) -> Dict[str, str]:
        """
        Extract schema metadata for all tables

        Returns:
            Dictionary mapping table names to their markdown schemas
        """
        tables = self.get_all_tables()
        schemas = {}

        for table in tables:
            schemas[table] = self.generate_markdown_schema(table)

        return schemas

    def prepare_bm25_documents(self) -> List[Dict[str, Any]]:
        """
        Prepare documents in format suitable for BM25 Retriever

        Returns:
            List of document dictionaries
        """
        schemas = self.extract_all_schemas()
        documents = []

        for table_name, schema_md in schemas.items():
            documents.append({
                'table_name': table_name,
                'content': schema_md,
                'metadata': {
                    'type': 'schema',
                    'table': table_name,
                    'extracted_at': datetime.now().isoformat()
                }
            })

        return documents

    def save_documents(self, output_path: str, format: str = 'json'):
        """
        Save extracted schema documents to file

        Args:
            output_path: Path to output file
            format: Output format ('json' or 'markdown')
        """
        documents = self.prepare_bm25_documents()

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(documents, f, indent=2)
            print(f"Saved {len(documents)} schema documents to {output_path}")
        elif format == 'markdown':
            os.makedirs(output_path, exist_ok=True)
            for doc in documents:
                file_path = os.path.join(output_path, f"{doc['table_name']}_schema.md")
                with open(file_path, 'w') as f:
                    f.write(doc['content'])
            print(f"Saved {len(documents)} schema documents to {output_path}/")


def main():
    """Main execution function"""
    # Get database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(script_dir), 'nuclear_plants.db')

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    print(f"Extracting schema metadata from: {db_path}\n")

    # Initialize extractor
    extractor = SchemaExtractor(db_path)

    try:
        # Connect to database
        extractor.connect()

        # Extract schemas
        schemas = extractor.extract_all_schemas()

        # Print schemas to console
        print("=" * 80)
        print("EXTRACTED SCHEMAS")
        print("=" * 80)
        for table_name, schema_md in schemas.items():
            print(f"\n{schema_md}")
            print("-" * 80)

        # Prepare BM25 documents
        documents = extractor.prepare_bm25_documents()
        print(f"\nPrepared {len(documents)} documents for BM25 Retriever")

        # Save to JSON
        output_json = os.path.join(script_dir, 'schema_metadata.json')
        extractor.save_documents(output_json, format='json')

        # Optionally save as markdown files
        output_md_dir = os.path.join(os.path.dirname(script_dir), 'table_meta')
        extractor.save_documents(output_md_dir, format='markdown')

        print("\nExtraction complete!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        extractor.close()


if __name__ == "__main__":
    main()

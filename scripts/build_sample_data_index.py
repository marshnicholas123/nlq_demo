#!/usr/bin/env python3
"""
Build BM25 index from sample data rows for query-relevant row retrieval.

This script extracts all rows from database tables and builds a BM25 index
to enable semantic retrieval of relevant sample data based on user queries.

Run this script whenever:
- Database data changes significantly
- Initial setup of the application
- You want to refresh the sample data index
"""

import json
import pickle
import os
import sqlite3
from typing import List, Dict, Any, Union
from pydantic import BaseModel
from rank_bm25 import BM25Okapi


class TableSampleData(BaseModel):
    """Pydantic model for table sample data"""
    table_name: str
    row_id: Union[str, int, None]
    content: str  # String representation for BM25 search
    raw_data: Dict[str, Any]  # Original row data


class SampleDataIndexBuilder:
    """Build and save BM25 index from database sample data"""

    def __init__(self, db_path: str, output_dir: str):
        """
        Initialize sample data index builder

        Args:
            db_path: Path to SQLite database file
            output_dir: Directory to save BM25 index and documents
        """
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Table definitions
        self.tables = {
            'countries': {
                'id_column': 'id',
                'columns': ['id', 'name']
            },
            'nuclear_power_plants': {
                'id_column': 'Id',
                'columns': ['Name', 'Latitude', 'Longitude', 'CountryCode', 'StatusId',
                           'ReactorTypeId', 'ReactorModel', 'ConstructionStartAt',
                           'OperationalFrom', 'OperationalTo', 'Capacity', 'Source',
                           'LastUpdatedAt', 'Id']
            },
            'nuclear_reactor_types': {
                'id_column': 'id',
                'columns': ['id', 'type']
            },
            'nuclear_power_plant_status_types': {
                'id_column': 'id',
                'columns': ['id', 'status']
            }
        }

    def connect_db(self) -> sqlite3.Connection:
        """Create database connection"""
        return sqlite3.connect(self.db_path)

    def row_to_searchable_text(self, table_name: str, row_data: Dict[str, Any]) -> str:
        """
        Convert a database row to searchable text for BM25

        Args:
            table_name: Name of the table
            row_data: Dictionary of row data

        Returns:
            String representation optimized for BM25 search
        """
        # Create natural language-like representation
        parts = []

        if table_name == 'countries':
            parts.append(f"country {row_data.get('name', '')}")
            parts.append(f"code {row_data.get('id', '')}")

        elif table_name == 'nuclear_power_plants':
            parts.append(f"plant {row_data.get('Name', '')}")
            parts.append(f"country {row_data.get('CountryCode', '')}")
            parts.append(f"reactor {row_data.get('ReactorModel', '')}")
            parts.append(f"capacity {row_data.get('Capacity', '')} MW")
            parts.append(f"status {row_data.get('StatusId', '')}")
            parts.append(f"type {row_data.get('ReactorTypeId', '')}")

            if row_data.get('OperationalFrom'):
                parts.append(f"operational from {row_data.get('OperationalFrom', '')}")
            if row_data.get('OperationalTo'):
                parts.append(f"shutdown at {row_data.get('OperationalTo', '')}")

        elif table_name == 'nuclear_reactor_types':
            parts.append(f"reactor type {row_data.get('type', '')}")
            parts.append(f"id {row_data.get('id', '')}")

        elif table_name == 'nuclear_power_plant_status_types':
            parts.append(f"status {row_data.get('status', '')}")
            parts.append(f"id {row_data.get('id', '')}")

        # Combine all parts
        searchable_text = " ".join(str(p) for p in parts if p)

        # Also add JSON representation for broader matching
        json_repr = " ".join(f"{k}:{v}" for k, v in row_data.items() if v is not None)

        return f"{searchable_text} {json_repr}"

    def extract_sample_data(self) -> List[TableSampleData]:
        """
        Extract all rows from database tables as TableSampleData objects

        Returns:
            List of TableSampleData objects
        """
        sample_data_list = []
        conn = self.connect_db()

        try:
            for table_name, table_config in self.tables.items():
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")

                # Get column names
                columns = [description[0] for description in cursor.description]

                # Process each row
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    row_id = row_dict.get(table_config['id_column'])

                    # Convert to searchable text
                    searchable_text = self.row_to_searchable_text(table_name, row_dict)

                    # Create TableSampleData object
                    sample_data = TableSampleData(
                        table_name=table_name,
                        row_id=row_id,
                        content=searchable_text,
                        raw_data=row_dict
                    )

                    sample_data_list.append(sample_data)

                cursor.close()
                print(f"  Extracted {len([s for s in sample_data_list if s.table_name == table_name])} rows from {table_name}")

        finally:
            conn.close()

        return sample_data_list

    def build_bm25_index(self, sample_data: List[TableSampleData]) -> BM25Okapi:
        """
        Build BM25 index from sample data

        Args:
            sample_data: List of TableSampleData objects

        Returns:
            BM25Okapi index object
        """
        # Tokenize documents (simple whitespace tokenization)
        tokenized_docs = [data.content.lower().split() for data in sample_data]

        # Create BM25 index
        bm25_index = BM25Okapi(tokenized_docs)

        return bm25_index

    def save_index(self, bm25_index: BM25Okapi, sample_data: List[TableSampleData]):
        """
        Save BM25 index and sample data to disk

        Args:
            bm25_index: BM25Okapi index object
            sample_data: List of TableSampleData objects
        """
        # Save BM25 index
        index_path = os.path.join(self.output_dir, 'sample_data_bm25_index.pkl')
        with open(index_path, 'wb') as f:
            pickle.dump(bm25_index, f)
        print(f"✓ Saved BM25 index to: {index_path}")

        # Save sample data corpus (as JSON-serializable dicts)
        docs_path = os.path.join(self.output_dir, 'sample_data_docs.json')
        sample_data_dicts = [data.model_dump() for data in sample_data]
        with open(docs_path, 'w') as f:
            json.dump(sample_data_dicts, f, indent=2, default=str)
        print(f"✓ Saved sample data documents to: {docs_path}")

    def build(self):
        """Build complete BM25 index from database sample data"""
        print("=" * 80)
        print("Sample Data BM25 Index Builder")
        print("=" * 80)

        # Extract sample data
        print(f"\n1. Extracting sample data from: {self.db_path}")
        sample_data = self.extract_sample_data()
        print(f"   Total rows extracted: {len(sample_data)}")

        # Build BM25 index
        print("\n2. Building BM25 index")
        bm25_index = self.build_bm25_index(sample_data)
        print(f"   Index built successfully")

        # Save to disk
        print(f"\n3. Saving index to: {self.output_dir}")
        self.save_index(bm25_index, sample_data)

        # Print summary
        print("\n" + "=" * 80)
        print("Index Build Complete!")
        print("=" * 80)
        print(f"Total documents indexed: {len(sample_data)}")

        # Count by table
        table_counts = {}
        for data in sample_data:
            table_counts[data.table_name] = table_counts.get(data.table_name, 0) + 1

        print("Rows per table:")
        for table, count in table_counts.items():
            print(f"  - {table}: {count}")

        print("\nFiles created:")
        print(f"  - {os.path.join(self.output_dir, 'sample_data_bm25_index.pkl')}")
        print(f"  - {os.path.join(self.output_dir, 'sample_data_docs.json')}")
        print("\nThe sample data retriever is now ready to use!")


def main():
    """Main execution function"""
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Input: SQLite database
    db_path = os.path.join(project_root, 'nuclear_plants.db')

    # Output: BM25 index files for backend application
    output_dir = os.path.join(project_root, 'backend', 'app', 'data')

    # Validate input file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return 1

    # Build index
    builder = SampleDataIndexBuilder(db_path, output_dir)
    builder.build()

    return 0


if __name__ == "__main__":
    exit(main())

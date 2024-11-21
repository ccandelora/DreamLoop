import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from os import environ


def create_db_dump(connection_string):
    """Create a database dump using psycopg2"""
    print("Starting database dump process...")

    # Clean and recreate dumps directory
    os.makedirs('dumps', exist_ok=True)

    # Generate timestamp for the dump file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = f'dumps/dream_journal_dump_{timestamp}.sql'

    try:
        print(f"Attempting to connect to database...")
        conn = psycopg2.connect(connection_string)
        print("Database connection successful!")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("Querying for available tables...")
        # Get list of all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()

        with open(dump_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"-- Dream Journal Database Dump\n")
            f.write(f"-- Created at: {datetime.now()}\n\n")

            # For each table
            for (table,) in tables:
                print(f"Backing up table: {table}")
                
                # Get create table statement
                cursor.execute(f"""
                    SELECT 
                        'CREATE TABLE ' || table_name || ' (' ||
                        string_agg(
                            column_name || ' ' || data_type ||
                            CASE 
                                WHEN character_maximum_length IS NOT NULL 
                                THEN '(' || character_maximum_length || ')'
                                ELSE ''
                            END ||
                            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
                            ', '
                        ) || ');'
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    GROUP BY table_name;
                """, (table,))
                create_table = cursor.fetchone()
                if create_table:
                    f.write(f"\n-- Table: {table}\n")
                    f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
                    f.write(f"{create_table[0]}\n")

                # Get column names first
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    ORDER BY ordinal_position;
                """, (table,))
                col_names = [row[0] for row in cursor.fetchall()]
                
                # Get table data
                cursor.execute('SELECT * FROM "{}"'.format(table))
                rows = cursor.fetchall()
                
                if rows:
                    
                    # Write INSERT statements
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                values.append(f"'{str(val).replace(chr(39), chr(39)+chr(39))}'")
                        
                        f.write(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n")

        cursor.close()
        conn.close()

        size = os.path.getsize(dump_file)
        print(f"\nDatabase dump created successfully: {dump_file} (Size: {size} bytes)")

        # Print first few lines of the dump file for verification
        print("\nFirst few lines of the dump file:")
        with open(dump_file, 'r', encoding='utf-8') as f:
            print(f.read(500))

        return dump_file

    except Exception as e:
        print(f"Error during backup: {str(e)}")
        if 'conn' in locals():
            print("Connection error details:", conn.notices)
        else:
            print("Failed to establish database connection")
        return None


if __name__ == "__main__":
    # Construct connection string from environment variables
    NEON_CONNECTION_STRING = f"postgresql://{environ['PGUSER']}:{environ['PGPASSWORD']}@{environ['PGHOST']}:{environ['PGPORT']}/{environ['PGDATABASE']}"

    try:
        dump_file = create_db_dump(NEON_CONNECTION_STRING)
        if dump_file:
            print("Backup completed successfully!")
            sys.exit(0)
        else:
            print("Backup failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Backup failed with error: {str(e)}")
        sys.exit(1)

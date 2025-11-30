"""
Compare Database Schemas - Local vs Railway
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_schema(conn_url, name):
    print(f'\n{"="*60}')
    print(f'{name} DATABASE SCHEMA')
    print("="*60)
    
    conn = psycopg2.connect(conn_url)
    cur = conn.cursor()
    
    # Get all tables
    cur.execute('''
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    ''')
    tables = [r[0] for r in cur.fetchall()]
    print(f'\nTables: {tables}')
    
    schema = {}
    
    # Get columns for each table
    for table in tables:
        cur.execute('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        ''', (table,))
        cols = cur.fetchall()
        schema[table] = cols
        print(f'\n📋 {table} ({len(cols)} columns):')
        for col in cols:
            nullable = '?' if col[2] == 'YES' else '!'
            default = ''
            if col[3]:
                d = str(col[3])
                default = f' = {d[:30]}...' if len(d) > 30 else f' = {d}'
            print(f'   {nullable} {col[0]}: {col[1]}{default}')
    
    conn.close()
    return tables, schema


if __name__ == "__main__":
    LOCAL_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/agent_db')
    RAILWAY_URL = 'postgresql://postgres:MiqSuHQmQtMzhSWzPKyCTxtsflktazqb@caboose.proxy.rlwy.net:35579/railway'
    
    # Local
    local_tables, local_schema = get_schema(LOCAL_URL, 'LOCAL (Development)')
    
    # Railway  
    railway_tables, railway_schema = get_schema(RAILWAY_URL, 'RAILWAY (Production)')
    
    # Compare
    print('\n' + '='*60)
    print('COMPARISON SUMMARY')
    print('='*60)
    
    local_set = set(local_tables)
    railway_set = set(railway_tables)
    
    only_local = local_set - railway_set
    only_railway = railway_set - local_set
    both = local_set & railway_set
    
    print(f'\n✅ Tables in BOTH: {len(both)}')
    for t in sorted(both):
        print(f'   - {t}')
    
    if only_local:
        print(f'\n⚠️  Only in LOCAL ({len(only_local)}):')
        for t in sorted(only_local):
            print(f'   - {t}')
    
    if only_railway:
        print(f'\n⚠️  Only in RAILWAY ({len(only_railway)}):')
        for t in sorted(only_railway):
            print(f'   - {t}')
    
    # Compare columns for shared tables
    print('\n' + '='*60)
    print('COLUMN DIFFERENCES')
    print('='*60)
    
    for table in sorted(both):
        local_cols = {c[0]: c[1:] for c in local_schema.get(table, [])}
        railway_cols = {c[0]: c[1:] for c in railway_schema.get(table, [])}
        
        only_local_cols = set(local_cols.keys()) - set(railway_cols.keys())
        only_railway_cols = set(railway_cols.keys()) - set(local_cols.keys())
        
        if only_local_cols or only_railway_cols:
            print(f'\n📋 {table}:')
            if only_local_cols:
                print(f'   ⚠️  Only in LOCAL: {only_local_cols}')
            if only_railway_cols:
                print(f'   ⚠️  Only in RAILWAY: {only_railway_cols}')
    
    print('\n✅ Schema comparison complete!')


import duckdb

con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

# all_varchar : tout est lu en texte. Une date mal formée reste visible
# au lieu d'être transformée en NULL sans prévenir.
con.execute("""
    CREATE OR REPLACE TABLE bronze.orders AS
    SELECT *, current_timestamp AS _ingested_at
    FROM read_csv('dataset/orders.csv', header = true, all_varchar = true)
""")

# TODO : la même chose pour dataset/customers.csv -> bronze.customers
con.execute("""
    CREATE OR REPLACE TABLE bronze.customers AS
    SELECT *, current_timestamp AS _ingested_at
    FROM read_csv('dataset/customers.csv', header = true, all_varchar = true)
""")

print("Extract → bronze done")

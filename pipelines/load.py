import duckdb

con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS gold;")
con.execute("""
    CREATE OR REPLACE TABLE gold.daily_revenue AS
    SELECT order_date,
           -- revenue_eur : somme des montants, arrondie à 2 décimales
           ROUND(SUM(amount_eur), 2) AS revenue_eur,
           -- orders      : nombre de commandes
           COUNT(*) AS orders
    FROM silver.orders
    GROUP BY order_date
    ORDER BY order_date
""")
print("Load → gold done")
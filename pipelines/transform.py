import duckdb

con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS silver;")

# 1. Clients : emails et pays normalisés
con.execute(r"""
    CREATE OR REPLACE TABLE silver.customers AS
    SELECT DISTINCT
        CAST(customer_id AS INTEGER) AS customer_id,
        trim(name)                   AS name,
        -- email : minuscules, sans espaces, sans points doublés ni point avant "@"
        regexp_replace(
            regexp_replace(lower(trim(email)), '\.{2,}', '.', 'g'),
            '\.@', '@', 'g'
        )                            AS email,
        -- country : majuscules, sans espaces
        upper(trim(country))         AS country
    FROM bronze.customers
""")

# 2. Commandes : vraie date, montant en euros, sans doublons
con.execute(r"""
    CREATE OR REPLACE TABLE silver.orders AS
    SELECT DISTINCT
        CAST(order_id AS INTEGER)    AS order_id,
        CAST(customer_id AS INTEGER) AS customer_id,
        -- order_date : accepter les 3 formats de date (YYYY-MM-DD, DD/MM/YYYY, YYYYMMDD)
        COALESCE(
            TRY_STRPTIME(trim(date), '%Y-%m-%d'),
            TRY_STRPTIME(trim(date), '%d/%m/%Y'),
            TRY_STRPTIME(trim(date), '%Y%m%d')
        )::DATE                      AS order_date,
        -- amount_eur : montant converti en euros (1 USD = 0.9 EUR)
        CAST(
            CASE upper(trim(currency))
                WHEN 'USD' THEN CAST(amount AS DECIMAL(10, 2)) * 0.9
                ELSE            CAST(amount AS DECIMAL(10, 2))
            END
        AS DECIMAL(10, 2))           AS amount_eur
    FROM bronze.orders
""")

print("Transform → silver done")
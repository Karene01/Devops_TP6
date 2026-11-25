import datetime
import sys

import duckdb
import pandas as pd

con = duckdb.connect("warehouse.duckdb", read_only=True)
today = datetime.date.today()

# Les colonnes n'ont pas le même nom ni le même type dans bronze (texte brut) et silver
DATE_SQL = {
    "bronze": "COALESCE(TRY_STRPTIME(date, '%Y-%m-%d'), TRY_STRPTIME(date, '%d/%m/%Y'), TRY_STRPTIME(date, '%Y%m%d'))::DATE",
    "silver": "order_date",
}
AMOUNT_SQL = {"bronze": "TRY_CAST(amount AS DOUBLE)", "silver": "amount_eur"}
# Un email bien formé : pas de "..", pas de ".@"
EMAIL_REGEX = r"^[a-z0-9]+(\.[a-z0-9]+)*@[a-z0-9-]+(\.[a-z0-9-]+)+$"


def ratio(sql: str) -> float:
    """Exécute une requête qui renvoie un nombre entre 0 et 1."""
    return round(float(con.execute(sql).fetchone()[0]), 3)


report = {}
for layer in ("bronze", "silver"):
    metrics = {}
    # Complétude : part des clients qui ont un email (exemple complet)
    metrics["customers_email_completeness"] = ratio(
        f"SELECT count(NULLIF(trim(email), '')) / count(*) FROM {layer}.customers")
    # Unicité   : part des order_id distincts parmi les commandes
    metrics["orders_id_uniqueness"] = ratio(
        f"SELECT count(DISTINCT order_id) / count(*) FROM {layer}.orders")
    # Cohérence : part des commandes dont le customer_id existe dans customers (LEFT JOIN)
    metrics["orders_customer_consistency"] = ratio(
        f"SELECT count(c.customer_id) / count(*) "
        f"FROM {layer}.orders o LEFT JOIN {layer}.customers c ON o.customer_id = c.customer_id")
    # Validité  : part des clients dont le pays est dans ('FR', 'DE', 'ES', 'US')
    #             ET dont l'email est bien formé (regexp_matches(email, EMAIL_REGEX))
    metrics["customers_validity"] = ratio(
        f"SELECT count(*) FILTER (WHERE country IN ('FR', 'DE', 'ES', 'US') "
        f"AND regexp_matches(email, '{EMAIL_REGEX}')) / count(*) FROM {layer}.customers")
    # Exactitude: part des commandes dont le montant est > 0 (AMOUNT_SQL[layer])
    metrics["orders_amount_accuracy"] = ratio(
        f"SELECT count(*) FILTER (WHERE {AMOUNT_SQL[layer]} > 0) / count(*) FROM {layer}.orders")
    # Fraîcheur : 1 si la commande la plus récente a moins de 30 jours, sinon 0 (DATE_SQL[layer])
    metrics["orders_freshness"] = ratio(
        f"SELECT CASE WHEN max({DATE_SQL[layer]}) >= DATE '{today}' - INTERVAL 30 DAY THEN 1 ELSE 0 END "
        f"FROM {layer}.orders")

    report[layer] = metrics

df = pd.DataFrame(report)
df.to_csv("quality_report.csv", index_label="metric")
print(df)
failed = df[df["silver"] < 0.98]
if not failed.empty:
    print("Quality check failed on silver:")
    print(failed["silver"])
    sys.exit(1)

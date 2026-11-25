import duckdb
import matplotlib.pyplot as plt
import streamlit as st

# read_only : le dashboard peut rester ouvert pendant que la pipeline écrit
con = duckdb.connect("warehouse.duckdb", read_only=True)
df = con.execute("SELECT * FROM gold.daily_revenue ORDER BY order_date").df()

st.title("Daily Revenue")
col1, col2 = st.columns(2)
col1.metric("Jours", len(df))
# TODO col2 : le CA total
col2.metric("CA total", f"{df['revenue_eur'].sum():,.2f} €")

fig, ax = plt.subplots(figsize=(10, 4))
# TODO : un graphique en barres du CA par jour (ax.bar)
ax.bar(df['order_date'], df['revenue_eur'])
st.pyplot(fig)

st.write("Top jours par CA")
st.dataframe(df.sort_values("revenue_eur", ascending=False).head(10))
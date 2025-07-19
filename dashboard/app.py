# import streamlit as st
# import pandas as pd
# from sqlalchemy import create_engine

# @st.cache_data(ttl=600)
# def load_results():
#     engine = create_engine('postgresql://jaelyn:pass@db:5432/quant')
#     sql = """
#       SELECT
#         run_id,
#         strategy,
#         pnl,
#         sharpe,
#         max_drawdown AS drawdown
#       FROM backtest_metrics
#     """
#     df = pd.read_sql(sql, engine, parse_dates=['run_id'])
#     df['run_id'] = pd.to_datetime(df['run_id'])
#     df = df.set_index('run_id').sort_index()
#     return df

# def main():
#     st.title("Quant Backtester Dashboard")

#     df = load_results()

#     # Sidebar filters
#     st.sidebar.header("Filters")
#     # Strategy selector
#     strategies = df['strategy'].unique().tolist()
#     sel = st.sidebar.multiselect("Pick strategy", strategies, default=strategies)

#     # Date range
#     min_date, max_date = df.index.min(), df.index.max()
#     date_range = st.sidebar.date_input("Run date range", [min_date, max_date],
#                                        min_value=min_date, max_value=max_date)

#     # Apply filters
#     mask = (
#         df['strategy'].isin(sel) &
#         (df.index.date >= date_range[0]) &
#         (df.index.date <= date_range[1])
#     )
#     filtered = df.loc[mask]

#     # Main charts
#     st.subheader("PnL Over Time")
#     st.line_chart(filtered['pnl'])

#     st.subheader("Summary Table")
#     st.dataframe(filtered[['strategy','pnl','drawdown','sharpe']])

# if __name__ == "__main__":
#     main()

#app.py

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import altair as alt

# Pull DB connection string from an env var
DB_URL = os.getenv("DB_URL")  # or use os.getenv("DB_URL")

@st.cache_data(ttl=300)
def load_results():
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM backtest_metrics", engine)
    # normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

st.title("📊 Quant Backtest Dashboard")

df = load_results()
if df.empty:
    st.warning("No backtest results found yet.")
    st.stop()

# Show raw table
with st.expander("Show raw metrics table"):
    st.dataframe(df)

# pick a strategy to explore
strategy = st.selectbox("Strategy", df["strategy"].unique())
sub = df[df["strategy"] == strategy].sort_values("maperiod")

# line chart of PnL vs maperiod
st.subheader(f"PnL vs `maperiod` for {strategy}")
st.line_chart(sub.set_index("maperiod")["pnl"])

# line chart of Sharpe
st.subheader(f"Sharpe vs `maperiod` for {strategy}")
st.line_chart(sub.set_index("maperiod")["sharpe"])

# Scatter: Sharpe vs Max Drawdown across all strategies
st.subheader("Sharpe vs Max Drawdown (all strategies)")
scatter = (
    alt.Chart(df)
    .mark_circle(size=80, opacity=0.7)
    .encode(
        x=alt.X("max_drawdown:Q", title="Max Drawdown (%)"),
        y=alt.Y("sharpe:Q",         title="Sharpe Ratio"),
        color=alt.Color("strategy:N", title="Strategy"),
        tooltip=["strategy","maperiod","pnl","sharpe","max_drawdown"]
    )
    .properties(width=800, height=400)
    .interactive()
)
st.altair_chart(scatter, use_container_width=True)

"""Chart helpers (matplotlib + seaborn), rendered in Streamlit via st.pyplot."""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 100

# Figure sizes tuned to render ~600px wide in Streamlit (use_container_width=False).
FIG_W = 6.0
FIG_H = 4.0


def bar(df, x, y, title, horizontal=False, top=None):
    """Vertical or horizontal bar chart from an aggregated DataFrame."""
    d = df.sort_values(y, ascending=not horizontal)
    if top:
        d = d.tail(top) if horizontal else d.head(top)
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    if horizontal:
        sns.barplot(data=d, x=y, y=x, ax=ax)
    else:
        sns.barplot(data=d, x=x, y=y, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def hist_with_normal(series, title, bins=50):
    """Histogram + KDE + overlaid normal curve (for normality assessment)."""
    s = pd.Series(series).dropna()
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    sns.histplot(s, bins=bins, kde=True, stat="density", ax=ax, color="steelblue")
    mu, sigma = s.mean(), s.std()
    x = np.linspace(s.min(), s.max(), 200)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), "r--", lw=2, label="Normal")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def log_hist(series, title, bins=50):
    """Histogram on a log10 scale (for heavy-tailed / power-law data)."""
    s = pd.Series(series).dropna()
    s = s[s > 0]
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    sns.histplot(np.log10(s), bins=bins, kde=True, ax=ax, color="seagreen")
    ax.set_xlabel("log10(value)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def time_series(df, date_col, val_col, title):
    """Line plot of a value over time."""
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col]).sort_values(date_col)
    fig, ax = plt.subplots(figsize=(7.0, FIG_H))
    ax.plot(d[date_col], d[val_col], marker="o", ms=3, lw=1)
    ax.set_title(title)
    fig.tight_layout()
    return fig

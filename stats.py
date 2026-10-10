"""Descriptive and inferential statistics helpers."""
import pandas as pd
from scipy import stats


def describe_numeric(series, name=""):
    """Descriptive stats: mean, median, mode, std, skew, kurtosis, normality."""
    s = pd.Series(series).dropna()
    if len(s) == 0:
        return {}
    sample = s if len(s) <= 5000 else s.sample(5000, random_state=0)
    return {
        "name": name,
        "n": int(len(s)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "mode": float(s.mode().iloc[0]) if not s.mode().empty else None,
        "std": float(s.std()),
        "var": float(s.var()),
        "min": float(s.min()),
        "max": float(s.max()),
        "q25": float(s.quantile(0.25)),
        "q75": float(s.quantile(0.75)),
        "skew": float(stats.skew(sample)),
        "kurtosis": float(stats.kurtosis(sample)),
        "shapiro_p": float(stats.shapiro(sample).pvalue),
    }


def chi2_test(df, col1, col2):
    """Chi-square test of independence between two categorical columns."""
    ct = pd.crosstab(df[col1], df[col2])
    chi2, p, dof, expected = stats.chi2_contingency(ct)
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof), "table": ct}


def mannwhitney(a, b):
    """Mann-Whitney U test between two independent samples."""
    a = pd.Series(a).dropna()
    b = pd.Series(b).dropna()
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"u": float(u), "p": float(p), "n_a": int(len(a)), "n_b": int(len(b))}


def kruskal(*groups):
    """Kruskal-Wallis H test across 3+ independent samples."""
    groups = [pd.Series(g).dropna() for g in groups]
    h, p = stats.kruskal(*groups)
    return {"h": float(h), "p": float(p)}


def correlation(a, b, method="spearman"):
    """Pearson or Spearman correlation between two numeric series."""
    df = pd.DataFrame({"a": pd.Series(a), "b": pd.Series(b)}).dropna()
    if method == "pearson":
        r, p = stats.pearsonr(df["a"], df["b"])
    else:
        r, p = stats.spearmanr(df["a"], df["b"])
    return {"r": float(r), "p": float(p), "n": int(len(df))}

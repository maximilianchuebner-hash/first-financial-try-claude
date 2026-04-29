"""
Regress S&P 500 returns on a set of macro/financial drivers, daily and weekly.

Predictors (X):
  - d_dgs10      : Δ 10Y nominal Treasury yield (bps)
  - d_be10       : Δ 10Y breakeven inflation (bps)
  - r_dxy        : DXY return (%)
  - r_oil        : WTI crude return (%)
  - d_vix        : Δ VIX (points)
  - d_hyoas      : Δ ICE BofA HY OAS (bps)
  - d_gpr        : Δ Caldara-Iacoviello GPR daily (index points)

Target (Y):
  - r_spx        : S&P 500 return (%)

Frequencies: daily, weekly (W-FRI, last obs in week).
Standard errors: HAC (Newey-West).
"""

from __future__ import annotations

import io
import sys
import warnings
from datetime import date

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import yfinance as yf

warnings.filterwarnings("ignore")

START = "2003-01-02"  # T10YIE starts here
END = date.today().isoformat()

FRED_SERIES = {
    "DGS10": "dgs10",          # 10Y nominal yield, %
    "T10YIE": "be10",          # 10Y breakeven, %
    "VIXCLS": "vix",           # VIX level
    "BAMLH0A0HYM2": "hyoas",   # HY OAS, %
    "DTWEXBGS": "dxy_fred",    # broad USD index (fallback if yfinance fails)
    "DCOILWTICO": "oil_fred",  # WTI spot, USD/bbl
}

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"


def fetch_fred_one(series_id: str) -> pd.Series:
    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        f"&cosd={START}&coed={END}"
    )
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    df = pd.read_csv(io.BytesIO(r.content))
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = df[date_col]
    s.name = series_id
    return s.dropna()


def fetch_fred() -> pd.DataFrame:
    print(f"Fetching FRED series {list(FRED_SERIES)} ...")
    parts = []
    for sid, name in FRED_SERIES.items():
        s = fetch_fred_one(sid).rename(name)
        parts.append(s)
    return pd.concat(parts, axis=1).sort_index()


def fetch_yf(ticker: str, name: str) -> pd.Series:
    print(f"Fetching {ticker} from Yahoo ...")
    df = yf.download(ticker, start=START, end=END, progress=False, auto_adjust=False)
    if df.empty:
        return pd.Series(dtype=float, name=name)
    s = df["Close"]
    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]
    s.name = name
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s


def fetch_gpr() -> pd.Series:
    print(f"Fetching GPR daily from {GPR_URL} ...")
    r = requests.get(GPR_URL, timeout=30)
    r.raise_for_status()
    # Try xls then xlsx engine
    for engine in ("xlrd", "openpyxl"):
        try:
            df = pd.read_excel(io.BytesIO(r.content), engine=engine)
            break
        except Exception:
            df = None
    if df is None:
        raise RuntimeError("Could not parse GPR file")
    # Expected columns: DAY (or date) and GPRD
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("day") or cols.get("date")
    val_col = cols.get("gprd") or cols.get("gpr")
    if date_col is None or val_col is None:
        raise RuntimeError(f"Unexpected GPR columns: {list(df.columns)}")
    s = pd.Series(df[val_col].values, index=pd.to_datetime(df[date_col]), name="gpr")
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s


def build_levels() -> pd.DataFrame:
    fred = fetch_fred()
    spx = fetch_yf("^GSPC", "spx")
    vix_yf = fetch_yf("^VIX", "vix_yf")
    dxy_yf = fetch_yf("DX-Y.NYB", "dxy")
    oil_yf = fetch_yf("CL=F", "oil")
    try:
        gpr = fetch_gpr()
    except Exception as e:
        print(f"WARN: GPR fetch failed ({e}); proceeding without GPR.")
        gpr = pd.Series(dtype=float, name="gpr")

    df = fred.join(spx, how="outer")
    # prefer yfinance for DXY/oil/VIX, fall back to FRED
    df["vix"] = vix_yf.reindex(df.index).combine_first(df["vix"])
    df["dxy"] = dxy_yf.reindex(df.index).combine_first(df["dxy_fred"])
    df["oil"] = oil_yf.reindex(df.index).combine_first(df["oil_fred"])
    df = df.drop(columns=["dxy_fred", "oil_fred"])
    if not gpr.empty:
        df = df.join(gpr, how="outer")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().loc[START:END]
    return df


def build_changes(levels: pd.DataFrame, freq: str) -> pd.DataFrame:
    """freq: 'D' (use levels as-is) or 'W-FRI' (resample to weekly)."""
    if freq == "D":
        lv = levels.copy()
    else:
        lv = levels.resample(freq).last()

    out = pd.DataFrame(index=lv.index)
    # Returns in % for price-like series
    out["r_spx"] = lv["spx"].pct_change() * 100.0
    out["r_dxy"] = lv["dxy"].pct_change() * 100.0
    out["r_oil"] = lv["oil"].pct_change() * 100.0
    # First differences in bps for yields/spreads (FRED reports in %)
    out["d_dgs10"] = lv["dgs10"].diff() * 100.0
    out["d_be10"] = lv["be10"].diff() * 100.0
    out["d_hyoas"] = lv["hyoas"].diff() * 100.0
    # VIX: change in points
    out["d_vix"] = lv["vix"].diff()
    # GPR: change in index points
    if "gpr" in lv.columns:
        out["d_gpr"] = lv["gpr"].diff()
    return out


def run_regression(df: pd.DataFrame, label: str, maxlags: int) -> sm.regression.linear_model.RegressionResultsWrapper:
    y_col = "r_spx"
    x_cols = [c for c in ["d_dgs10", "d_be10", "r_dxy", "r_oil", "d_vix", "d_hyoas", "d_gpr"] if c in df.columns]
    data = df[[y_col] + x_cols].dropna()
    y = data[y_col]
    X = sm.add_constant(data[x_cols])
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    print("\n" + "=" * 78)
    print(f"OLS regression — {label}  (n={int(res.nobs)}, HAC maxlags={maxlags})")
    print("=" * 78)
    print(res.summary())
    return res


def main() -> int:
    levels = build_levels()
    print(f"\nLevels coverage: {levels.index.min().date()} → {levels.index.max().date()}, "
          f"{len(levels):,} rows, columns={list(levels.columns)}")

    daily = build_changes(levels, "D")
    weekly = build_changes(levels, "W-FRI")

    # Save merged inputs for inspection
    daily.to_csv("regression_daily.csv")
    weekly.to_csv("regression_weekly.csv")
    print("Wrote regression_daily.csv and regression_weekly.csv")

    run_regression(daily, "daily",  maxlags=5)   # ~1 trading week
    run_regression(weekly, "weekly", maxlags=4)  # ~1 month

    return 0


if __name__ == "__main__":
    sys.exit(main())

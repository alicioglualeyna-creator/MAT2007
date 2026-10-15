# Docstrings """" 
# Python will not run these lines, but will store them as documentation for the code.
"""
Title: Life Expectancy vs. Health Spending

Research Question: To what extent is the association between healthcare spending and life expectancy
characterized by diminishing returns across countries?

Data Source: Our World in Data, "Life expectancy vs. health spending"
      (UN World Population Prospects 2024; OECD Health Expenditure database)
"""

# IMPORTS
import ssl                        # Built-in module
import certifi                    # Third-party module

from pathlib import Path          # Path = safe way to write file paths 
import urllib.request             # standard-library module to download a file from a URL

# Downloadable tools:
import numpy as np                # numerical maths
import pandas as pd               # tables ("DataFrames"): load CSV, filter rows, sort
import matplotlib.pyplot as plt   # used for plotting
from scipy import stats           # statistics: stats.linregress, stats.norm, stats.t


# SETTINGS 
# Settings should be placed at the top so they are easy to change
URL = ("https://ourworldindata.org/grapher/life-expectancy-vs-health-expenditure.csv"
       "?v=1&csvType=full&useColumnShortNames=false")
DATA = Path("life-expectancy-vs-health-expenditure.csv")    # CSV is saved here

# I chose the year 2019 because it was the last year before the Covid-19 pandemic
# I did this to avoid pandemic-related distortions in the data
YEAR = 2019                       # main year: latest pre-COVID year
VALIDATION_YEAR = 2023            # year used to test predictions on unseen data
ROBUST_YEARS = [2000, 2010, 2019, 2023]   # years for the robustness check
SPEND_LEVELS = [500, 1000, 2500, 5000, 10000]   # spending levels for the marginal-return table
N_LABEL = 3                       # countries labelled on each side of the scatter plot


# FUNCTIONS
# I will reuse the "def name(input):" syntax to define functions
# "return" will send the output back to the caller 
# However, nothing will run until main() calls it 
def t_crit(n):
    """t-value for a 95% confidence interval of a straight-line fit with n points
    (n - 2 degrees of freedom). CI half-width = t_crit * standard error."""
    return stats.t.ppf(0.975, n - 2)


def load_data():
    """Read the CSV from disk; download it first if it is missing."""
    # "not DATA.exists()" is True only when the file is missing
    if not DATA.exists():
        print("Downloading dataset ...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
        with opener.open(request) as response:
            DATA.write_bytes(response.read())
    df = pd.read_csv(DATA)       # df = DataFrame, which is pandas' name for a table
    # Rename columns
    # Order matches the order of the columns in the CSV file
    df.columns = ["country", "code", "year", "life_exp", "health_exp", "region"]
    return df


# Cleans the data
# Script will remove any rows that have missing values for either life expectancy or health spending
# It will also remove the countries with health spending less than or equal to zero
def clean(df):
    """Keep rows that have BOTH life expectancy and health spending."""
    n_all = len(df)
    # dropna removes any rows with missing values
    df = df.dropna(subset=["life_exp", "health_exp"])
    df = df[df["health_exp"] > 0].copy()        # .copy() = independent table, safe to add a column
    df["ln_exp"] = np.log(df["health_exp"])     # natural log of spending
    print(f"Rows in file: {n_all}, rows with both variables: {len(df)}")
    return df


# Linear and log fits to one year of data (2019)
def fit_models(s):
    """Fit two straight-line models to one year of data.
    linear: life_exp = a + b * spending       (constant return per dollar)
    log:    life_exp = a + b * ln(spending)   (diminishing returns per dollar)
    Compare R^2: the model with the higher R^2 describes the data better."""
    lin = stats.linregress(s["health_exp"], s["life_exp"])
    log = stats.linregress(s["ln_exp"], s["life_exp"])
    return lin, log


# The countries will be split into two groups: low-spending and high-spending, based on the 
# median healthcare spending per person
# I chose median because it is a robust measure of central tendency that is not affected by 
# extreme values or outliers (e.g. United States)
def split_slopes(s, exclude=()):
    """Split countries at the MEDIAN spending, fit a straight line in each half and
    return the slope (extra years per extra $1,000) with its 95% confidence interval.
    Diminishing returns => low-spending slope is larger than high-spending slope."""
    s = s[~s["country"].isin(exclude)]          # ~ means NOT: drop the excluded countries
    median = s["health_exp"].median()
    halves = {"low": s[s["health_exp"] <= median], "high": s[s["health_exp"] > median]}
    out = {"median": median}
    for name, g in halves.items():
        f = stats.linregress(g["health_exp"], g["life_exp"])
        # multiply by 1000: slope per $1 -> slope per $1,000 (same for the error)
        out[name] = {"n": len(g), "slope": f.slope * 1000,
                     "err": f.stderr * 1000,                       # width of the normal curve
                     "ci": t_crit(len(g)) * f.stderr * 1000,       # 95% CI half-width
                     "p": f.pvalue}
    diff = out["low"]["slope"] - out["high"]["slope"]
    diff_err = np.hypot(out["low"]["err"], out["high"]["err"])   # uncertainty of a difference
    out.update({"diff": diff, "diff_err": diff_err, "sigma": diff / diff_err})
    return out


# Extra years of life expectancy from one more $1,000 at different spending levels (low- and high-spending countries)
def marginal_returns(log_fit, n):
    """Extra years per additional $1,000 at different spending levels, with 95% CI.
    For y = a + b*ln(S) the slope at S is dy/dS = b / S (calculus: derivative of ln)."""
    t = t_crit(n)
    rows = []
    for S in SPEND_LEVELS:
        rows.append({"spending": S,
                     "years_per_1000usd": 1000 * log_fit.slope / S,
                     "ci95": t * 1000 * log_fit.stderr / S})
    return pd.DataFrame(rows)


def predict_test(df, fit, year):
    """Predict life expectancy in another year with a fitted log line; compare with reality."""
    s = df[df["year"] == year]
    error = s["life_exp"] - (fit.intercept + fit.slope * s["ln_exp"])
    return {"year": year, "n": len(s), "mean_error": error.mean(),
            "rmse": np.sqrt((error ** 2).mean())}


def doubling_by_year(df):
    """Years of life expectancy gained per doubling of spending, for each robustness year."""
    rows = []
    for y in ROBUST_YEARS:
        s = df[df["year"] == y]
        _, log = fit_models(s)
        rows.append({"year": y, "n": len(s),
                     "gain": log.slope * np.log(2),
                     "err": log.stderr * np.log(2),
                     "ci": t_crit(len(s)) * log.stderr * np.log(2),   # 95% CI half-width
                     "r2": log.rvalue ** 2})
    return pd.DataFrame(rows)


# This function will find the countries furthest below and above the log curve (the outliers)
# So the countries that are below or above the predicted curve will be labelled in the scatter plot
def top_residuals(s, log, k=3):
    """Countries furthest below/above the log fit (residual in years)."""
    r = (s["life_exp"] - (log.intercept + log.slope * s["ln_exp"])).rename("residual")
    out = s[["country"]].join(r).sort_values("residual")
    return out.head(k), out.tail(k)


# This function will plot the first figure, which is the scatter plot with the linear and log fits
def plot_fits(s, lin, log):
    """FIGURE 1: scatter on a LINEAR x-axis with the linear and the log fit.
    The curve flattening at high spending is the visual sign of diminishing returns.
    The grey band is the 95% confidence interval of the log fit."""
    fig, ax = plt.subplots(figsize=(8, 5))
    # The different regions will be color-coded 
    for region, g in s.groupby("region"):
        ax.scatter(g["health_exp"], g["life_exp"], s=28, label=region)
    x = np.linspace(s["health_exp"].min(), s["health_exp"].max(), 300)
    # Dashed line = linear fit, solid line = log fit
    ax.plot(x, lin.intercept + lin.slope * x, "k--", lw=1.2,
            label=f"Linear fit (R² = {lin.rvalue ** 2:.2f})")
    ax.plot(x, log.intercept + log.slope * np.log(x), "k-", lw=1.8,
            label=f"Log fit (R² = {log.rvalue ** 2:.2f})")

    # 95% confidence band of the log fit
    n = len(s)
    xl = s["ln_exp"]
    s_res = np.sqrt(((s["life_exp"] - (log.intercept + log.slope * xl)) ** 2).sum() / (n - 2))
    xg = np.linspace(xl.min(), xl.max(), 300)
    se = s_res * np.sqrt(1 / n + (xg - xl.mean()) ** 2 / ((xl - xl.mean()) ** 2).sum())
    t95 = t_crit(n)
    yg = log.intercept + log.slope * xg
    ax.fill_between(np.exp(xg), yg - t95 * se, yg + t95 * se,
                    color="k", alpha=0.12, label="95% CI (log fit)")

    # Label the countries furthest from the log curve
    # This avoids a cluster of names in the middle of the plot, which would make it hard to read
    resid = s["life_exp"] - (log.intercept + log.slope * s["ln_exp"])
    order = resid.sort_values().index
    for i in list(order[:N_LABEL]) + list(order[-N_LABEL:]):
        ax.annotate(s.loc[i, "country"], (s.loc[i, "health_exp"], s.loc[i, "life_exp"]),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("Health spending per person (international-$, 2020 prices)")
    ax.set_ylabel("Life expectancy at birth (years)")
    ax.set_title(f"Life expectancy vs. health spending, {YEAR}")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig("fig1_fits.png", dpi=200)
    plt.close(fig)


# Figure 2: normal distribution curves of the slopes for the low- and high-spending groups
def plot_normal_slopes(split):
    """FIGURE 2: normal curves of the slope (extra years per $1,000) for the
    low- and high-spending halves. Each curve is centred on the estimate; the
    shaded area is the 95% confidence interval. Little overlap = the two slopes
    really differ."""
    fig, ax = plt.subplots(figsize=(7, 4))
    groups = [("low", f"Low spending (≤ ${split['median']:,.0f})"),
              ("high", f"High spending (> ${split['median']:,.0f})")]
    lo = min(split[k]["slope"] - 4 * split[k]["err"] for k, _ in groups)
    hi = max(split[k]["slope"] + 4 * split[k]["err"] for k, _ in groups)
    x = np.linspace(lo, hi, 500)
    for key, label in groups:
        mu, sigma, ci = split[key]["slope"], split[key]["err"], split[key]["ci"]
        pdf = stats.norm.pdf(x, loc=mu, scale=sigma)
        ax.plot(x, pdf, label=f"{label}: {mu:.2f} (95% CI ± {ci:.2f}, n = {split[key]['n']})")
        ax.fill_between(x, pdf, where=(x >= mu - ci) & (x <= mu + ci), alpha=0.3)  # 95% CI
    ax.axvline(0, color="k", lw=0.8, ls=":")             # 0 = "no association"
    ax.set_xlabel("Extra years of life expectancy per additional $1,000 of spending")
    ax.set_ylabel("Probability density")
    ax.set_title(f"Slope in low vs. high spending countries (shaded = 95% CI, z = {split['sigma']:.1f})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("fig2_normal_slopes.png", dpi=200)
    plt.close(fig)

# This will run everything in order
def main():
    """Run the whole analysis from start to finish."""
    df = clean(load_data())
    s = df[df["year"] == YEAR]
    print(f"\n=== {YEAR}: {len(s)} countries ===")

    # 1) Linear vs log model
    lin, log = fit_models(s)
    k = np.log(2)
    print(f"R² linear = {lin.rvalue ** 2:.3f}, R² log = {log.rvalue ** 2:.3f}")
    print(f"Gain per doubling of spending = {log.slope * k:.2f} "
          f"(95% CI +/- {t_crit(len(s)) * log.stderr * k:.2f}) years")

    # 2) Low vs high spending halves
    split = split_slopes(s)
    print(f"\nMedian spending = ${split['median']:,.0f}")
    for key in ["low", "high"]:
        g = split[key]
        print(f"  {key:>4} half (n={g['n']}): {g['slope']:.2f} (95% CI +/- {g['ci']:.2f}) "
              f"years per $1,000 (p = {g['p']:.3f})")
    print(f"  difference = {split['diff']:.2f}, z = {split['sigma']:.1f}")

    # 3) Robustness: without the United States, and for other years
    no_us = split_slopes(s, exclude=["United States"])
    print(f"\nWithout USA: low {no_us['low']['slope']:.2f} (95% CI +/- {no_us['low']['ci']:.2f}), "
          f"high {no_us['high']['slope']:.2f} (95% CI +/- {no_us['high']['ci']:.2f}), z = {no_us['sigma']:.1f}")
    rows = []
    for y in ROBUST_YEARS:
        sp = split_slopes(df[df["year"] == y])
        rows.append({"year": y, "n": sp["low"]["n"] + sp["high"]["n"],
                     "low_slope": sp["low"]["slope"], "low_ci": sp["low"]["ci"],
                     "high_slope": sp["high"]["slope"], "high_ci": sp["high"]["ci"],
                     "z": sp["sigma"]})
    robust = pd.DataFrame(rows)
    print("\nRobustness across years (slopes in years per $1,000, 95% CI half-width):")
    print(robust.round(2).to_string(index=False))

    # 4) Marginal returns at different spending levels
    marg = marginal_returns(log, len(s))
    print("\nMarginal return of an extra $1,000 (95% CI half-width in ci95):")
    print(marg.round(2).to_string(index=False))

    # 5) Prediction test: fit on YEAR, predict VALIDATION_YEAR
    val = predict_test(df, log, VALIDATION_YEAR)
    print(f"\nPrediction test {YEAR} fit -> {val['year']} ({val['n']} countries): "
          f"mean error = {val['mean_error']:.2f}, RMSE = {val['rmse']:.2f} years")

    # 6) Has the return to doubling changed? (2000 vs 2019 etc.)
    d = doubling_by_year(df)
    print("\nGain per doubling of spending by year (ci = 95% CI half-width):")
    print(d.round(2).to_string(index=False))
    a, b = d[d["year"] == 2000].iloc[0], d[d["year"] == 2019].iloc[0]
    z = (b["gain"] - a["gain"]) / np.hypot(a["err"], b["err"])
    print(f"2019 - 2000 change: {b['gain'] - a['gain']:.2f} years (z = {z:.1f})")

    # 7) Over- and under-performers
    under, over = top_residuals(s, log)
    print("\nBelow expected:\n", under.round(2).to_string(index=False))
    print("\nAbove expected:\n", over.round(2).to_string(index=False))

    # Save tables (CSV) and figures (PNG)
    robust.round(3).to_csv("robustness.csv", index=False)
    marg.round(3).to_csv("marginal_returns.csv", index=False)
    d.round(3).to_csv("doubling_by_year.csv", index=False)
    plot_fits(s, lin, log)
    plot_normal_slopes(split)
    print("\nSaved: fig1_fits.png, fig2_normal_slopes.png, "
          "robustness.csv, marginal_returns.csv, doubling_by_year.csv")


# Will only run main()
if __name__ == "__main__":
    main()
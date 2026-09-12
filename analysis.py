from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import wilcoxon


DATA_FILE = Path("data/Eurostat_HPI_quarterly.xlsx")
OUTPUT_DIR = Path("output")
ANALYSIS_PERIOD = "2025-Q3"

# German country labels are used because the supplied Eurostat export is in German.
EU_COUNTRIES = [
    "Belgien", "Bulgarien", "Tschechien", "Dänemark", "Deutschland", "Estland",
    "Irland", "Griechenland", "Spanien", "Frankreich", "Kroatien", "Italien",
    "Zypern", "Lettland", "Litauen", "Luxemburg", "Ungarn", "Malta",
    "Niederlande", "Österreich", "Polen", "Portugal", "Rumänien", "Slowenien",
    "Slowakei", "Finnland", "Schweden",
]


def extract_eurostat_series(file_path: Path, sheet_name: str, value_name: str) -> pd.DataFrame:
    """Convert one Eurostat worksheet from wide format into tidy long format."""
    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    # Row 9 of the workbook contains quarterly labels in every second column.
    period_columns = {
        col: raw.iat[8, col]
        for col in range(1, raw.shape[1])
        if isinstance(raw.iat[8, col], str)
        and raw.iat[8, col].startswith("20")
        and "-Q" in raw.iat[8, col]
    }

    # Data start on row 11 and end before legend Spezial Zeichen.
    data = raw.iloc[10:].copy()
    stop = data.index[data.iloc[:, 0].eq("Spezial Zeichen")]
    if len(stop):
        data = data.loc[data.index < stop[0]]

    records = []
    for _, row in data.iterrows():
        country = row.iloc[0]
        if pd.isna(country):
            continue

        for value_col, period in period_columns.items():
            value = pd.to_numeric(row.iloc[value_col], errors="coerce")
            flag_col = value_col + 1
            flag = row.iloc[flag_col] if flag_col < len(row) else pd.NA

            if pd.notna(value):
                records.append(
                    {
                        "country": country,
                        "period": period,
                        value_name: float(value),
                        f"{value_name}_flag": flag,
                    }
                )

    result = pd.DataFrame(records)

    if result.duplicated(["country", "period"]).any():
        raise ValueError(f"Duplicate country-period observations found in {sheet_name}.")

    return result


def is_unflagged(series: pd.Series) -> pd.Series:
    """Return True for observations without Eurostat quality flags."""
    return series.isna() | series.astype(str).str.strip().eq("")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Sheet 4: annual growth rate for newly built dwellings.
    new = extract_eurostat_series(
        DATA_FILE,
        sheet_name="Blatt 4",
        value_name="new_dwellings_yoy",
    )

    # Sheet 6: annual growth rate for existing dwellings.
    existing = extract_eurostat_series(
        DATA_FILE,
        sheet_name="Blatt 6",
        value_name="existing_dwellings_yoy",
    )

    merged = new.merge(existing, on=["country", "period"], how="inner")
    merged = merged[merged["country"].isin(EU_COUNTRIES)].copy()

    sample = merged[merged["period"].eq(ANALYSIS_PERIOD)].copy()
    sample["difference_pp"] = (
        sample["new_dwellings_yoy"] - sample["existing_dwellings_yoy"]
    )

    if sample.empty:
        raise ValueError(f"No observations found for {ANALYSIS_PERIOD}.")

    # Main paired non-parametric test.
    test = wilcoxon(
        sample["new_dwellings_yoy"],
        sample["existing_dwellings_yoy"],
        alternative="two-sided",
        zero_method="wilcox",
    )

    # Sensitivity check excluding observations carrying Eurostat flags.
    clean = sample[
        is_unflagged(sample["new_dwellings_yoy_flag"])
        & is_unflagged(sample["existing_dwellings_yoy_flag"])
    ].copy()

    clean_test = wilcoxon(
        clean["new_dwellings_yoy"],
        clean["existing_dwellings_yoy"],
        alternative="two-sided",
        zero_method="wilcox",
    )

    summary = [
        f"Analysis period: {ANALYSIS_PERIOD}",
        f"Countries with paired observations: {len(sample)}",
        f"Median annual growth, newly built dwellings: "
        f"{sample['new_dwellings_yoy'].median():.2f}%",
        f"Median annual growth, existing dwellings: "
        f"{sample['existing_dwellings_yoy'].median():.2f}%",
        f"Median paired difference (new - existing): "
        f"{sample['difference_pp'].median():.2f} percentage points",
        f"Wilcoxon statistic: {test.statistic:.2f}",
        f"Wilcoxon p-value: {test.pvalue:.4f}",
        "",
        "Sensitivity excluding flagged observations:",
        f"Unflagged paired observations: {len(clean)}",
        f"Wilcoxon statistic: {clean_test.statistic:.2f}",
        f"Wilcoxon p-value: {clean_test.pvalue:.4f}",
    ]

    print("\n".join(summary))

    sample.sort_values("country").to_csv(
        OUTPUT_DIR / f"hpi_new_vs_existing_{ANALYSIS_PERIOD}.csv",
        index=False,
    )
    (OUTPUT_DIR / "results.txt").write_text("\n".join(summary), encoding="utf-8")

    # Visualise the country-level paired differences.
    plot_data = sample.sort_values("difference_pp")
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(plot_data["country"], plot_data["difference_pp"])
    ax.axvline(0, linewidth=1)
    ax.set_xlabel("Difference in annual growth (percentage points)")
    ax.set_ylabel("Country")
    ax.set_title(
        f"House-price growth: newly built minus existing dwellings, {ANALYSIS_PERIOD}"
    )
    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / f"hpi_difference_{ANALYSIS_PERIOD}.png",
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()

# Credits for the Wilcoxon signed rank test Python code: kulkarnisuraj92

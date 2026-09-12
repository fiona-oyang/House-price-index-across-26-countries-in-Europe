# Eurostat House Price Index: New vs Existing Dwellings

A small Python data-analysis example using Eurostat's quarterly House Price Index (HPI) dataset (`prc_hpi_q`).

## Purpose

The repository demonstrates a compact end-to-end workflow for:

- importing a multi-sheet Eurostat Excel export;
- reshaping data from wide to tidy format;
- preserving Eurostat observation flags;
- validating and merging country-quarter observations;
- performing a paired statistical test; and
- visualising and exporting the results.

## Research question

**Did annual house-price growth in Q3 2025 differ systematically between newly built and existing dwellings across EU countries with available data?**

Q3 2025 is used because the supplied export contains relatively few provisional observations for that quarter, while the newest quarter contains substantially more provisional data.

## Method

Annual growth rates for newly built dwellings and existing dwellings are matched by country. A two-sided Wilcoxon signed-rank test is used because the observations are paired at country level and the method does not require normally distributed paired differences.

The script also performs a sensitivity check excluding observations carrying Eurostat quality flags.

## Data

Source: Eurostat, **House price index – quarterly data**, dataset code `prc_hpi_q`.

The supplied workbook was downloaded from Eurostat on 12 September 2026. It contains quarterly data from 2015-Q2 to 2026-Q1 and separates total purchases, newly built dwellings and existing dwellings.

Eurostat background information:
https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Housing_price_statistics_-_house_price_index

## Expected result for Q3 2025

Using the supplied export:

- 26 EU countries have paired observations;
- median annual growth is 4.25% for newly built dwellings;
- median annual growth is 6.75% for existing dwellings;
- median paired difference is -2.40 percentage points;
- Wilcoxon p-value is approximately 0.0246.

Hungary and Malta are flagged as provisional in this quarter. Excluding flagged observations leaves 24 countries and produces a p-value of approximately 0.0486.

These results are descriptive evidence for this sample and should not be interpreted causally.

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

The script creates an `output` folder containing:

- a cleaned country-level CSV;
- a text file with statistical results; and
- a bar chart of the paired differences.

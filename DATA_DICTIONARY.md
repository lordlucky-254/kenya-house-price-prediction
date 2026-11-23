# Data Dictionary — `kenya_dashboard.csv`

## Overview

- **File:** `data/kenya_dashboard.csv`
- **Granularity:** One row per Kenyan county per calendar year
- **Coverage:** 10 counties × 8 years (`2018–2025`) = **80 rows**
- **Data Nature:** Synthetic demonstration dataset modeled on realistic Kenyan indicator ranges. Do not use for policy, lending, or commercial decisions without replacing it with verified official datasets.

## Schema

| Column | Type | Unit / Scale | Description |
| :--- | :--- | :--- | :--- |
| `county` | `string` | — | Name of the Kenyan county (e.g., `Nairobi`, `Nyeri`, `Nakuru`). |
| `year` | `int` | Calendar year | Observation year (`2018`–`2025`). |
| `rainfall_mm` | `float` / `int` | Millimeters (`mm`) | Annual total rainfall recorded in the county. |
| `maize_yield_tonnes_per_ha` | `float` | Tonnes per hectare (`t/ha`) | Average annual maize yield per hectare harvested. |
| `kcse_mean_score` | `float` | Points (`1.0`–`12.0`) | Kenya Certificate of Secondary Education (KCSE) county mean grade score. |
| `house_price_ksh` | `float` / `int` | Kenyan Shillings (`KES`) | Representative housing price index / unit valuation in KES. |
| `mpesa_agents` | `int` | Count | Active M-Pesa mobile money agent outlets operating in the county during that year. |

## Counties Included

| County | Region | Latitude | Longitude |
| :--- | :--- | :---: | :---: |
| Nairobi | Nairobi | -1.2921 | 36.8219 |
| Kiambu | Central | -1.1714 | 36.8356 |
| Mombasa | Coast | -4.0435 | 39.6682 |
| Kisumu | Nyanza | -0.0917 | 34.7680 |
| Nakuru | Rift Valley | -0.3031 | 36.0800 |
| Kericho | Rift Valley | -0.3677 | 35.2831 |
| Uasin Gishu | Rift Valley | 0.5143 | 35.2698 |
| Machakos | Eastern | -1.5177 | 37.2634 |
| Kakamega | Western | 0.2827 | 34.7519 |
| Nyeri | Central | -0.4167 | 36.9500 |

## Replacing with Production Data

You can replace `data/kenya_dashboard.csv` (or upload a CSV directly from the dashboard sidebar) as long as your file contains the exact 7 required column headers listed above.

Recommended authoritative sources for Kenya:
- **Kenya National Bureau of Statistics (KNBS):** Statistical Abstracts & Economic Surveys
- **Kenya Meteorological Department (KMD):** County rainfall records
- **Kenya National Examinations Council (KNEC):** KCSE performance summaries
- **Central Bank of Kenya (CBK) / Communications Authority:** Mobile money agent statistics
- **World Bank Open Data / Kenya Open Data Initiative:** Macro & county indicators

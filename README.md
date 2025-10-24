# Market Premium Analysis

This Python project fetches and analyzes the relationship between:
- **Damodaran's Implied Equity Risk Premium (ERP)**: Market expectations of future returns
- **Shiller CAPE Ratio**: Cyclically Adjusted Price-to-Earnings ratio
- **S&P 500 Forward 2-Year Returns**: Actual returns over the next 2 years

## Features

- Fetches real-time data from authoritative sources:
  - Damodaran's implied ERP from NYU Stern
  - Shiller CAPE from Yale University
  - S&P 500 price data via Yahoo Finance
- Calculates forward 2-year returns for the S&P 500
- Creates comprehensive visualizations showing:
  - Time series of all metrics
  - Correlation analysis
  - Scatter plots with trend lines
  - Distribution analysis by quartiles
- Generates detailed summary statistics and insights
- Exports data to CSV for further analysis

## Installation

1. Clone this repository or download the files

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python market_premium_analysis.py
```

The script will:
1. Fetch data from various sources
2. Merge and align the datasets
3. Display summary statistics and correlations
4. Generate and save visualizations
5. Export the merged data to CSV

## Output Files

- `market_premium_analysis_YYYYMMDD.png`: Comprehensive visualization with 6 subplots
- `market_data_YYYYMMDD.csv`: Merged dataset with all variables

## Key Metrics Explained

### Damodaran Implied Equity Risk Premium
- Calculated by Professor Aswath Damodaran at NYU Stern
- Represents the expected return above the risk-free rate
- Higher ERP typically indicates higher expected future returns or increased market risk

### Shiller CAPE Ratio
- Developed by Nobel laureate Robert Shiller
- Price divided by 10-year average inflation-adjusted earnings
- Higher CAPE typically indicates overvaluation and lower future returns
- Historical mean is around 16-17; levels above 25-30 considered elevated

### Forward 2-Year Returns
- Actual S&P 500 returns over the subsequent 24 months
- Used to validate whether high ERP or low CAPE predict better returns
- Note: Most recent 24 months will have NaN values (future data not available)

## Expected Relationships

Based on financial theory:

1. **Implied ERP vs Forward Returns**: Positive correlation expected
   - Higher implied premium should predict higher future returns

2. **CAPE vs Forward Returns**: Negative correlation expected
   - Higher valuations (high CAPE) should predict lower future returns

3. **ERP vs CAPE**: Generally negative correlation
   - High valuations often coincide with lower risk premiums

## Data Sources

- **Damodaran Implied ERP**: http://pages.stern.nyu.edu/~adamodar/
- **Shiller CAPE**: http://www.econ.yale.edu/~shiller/data.htm
- **S&P 500 Data**: Yahoo Finance via yfinance package

## Requirements

- Python 3.8+
- Internet connection for data fetching
- See requirements.txt for package dependencies

## Notes

- The script includes fallback sample data generation if any source is unavailable
- Forward returns for the most recent 24 months will be NaN (future data not yet available)
- Data is resampled to monthly frequency for consistency
- All returns are expressed in percentage terms

## Author

Generated with Claude Code

## License

MIT License - Feel free to use and modify for your own analysis

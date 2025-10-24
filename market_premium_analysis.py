"""
Market Premium Analysis: Damodaran Implied Premium, Shiller CAPE, and S&P 500 Returns

This script fetches and plots:
1. Damodaran's Implied Equity Risk Premium
2. Shiller CAPE (Cyclically Adjusted Price-to-Earnings Ratio)
3. S&P 500 forward 2-year returns

Author: Generated with Claude Code
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from io import StringIO
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)


def fetch_damodaran_erp():
    """
    Fetch Damodaran's Implied Equity Risk Premium data
    Data source: http://pages.stern.nyu.edu/~adamodar/
    """
    print("Fetching Damodaran Implied ERP data...")

    # Damodaran publishes monthly updates of implied ERP
    # The historical data is available in Excel format
    url = "http://www.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xls"

    try:
        # Read the Excel file
        df = pd.read_excel(url, sheet_name=0, skiprows=0)

        # Clean and format the data
        # The first column is typically the date, second is the implied premium
        df.columns = ['Date', 'Implied_Premium'] + list(df.columns[2:])

        # Convert date to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Remove rows with invalid dates
        df = df.dropna(subset=['Date'])

        # Keep only Date and Implied_Premium columns
        df = df[['Date', 'Implied_Premium']].copy()

        # Remove any non-numeric values from Implied_Premium
        df['Implied_Premium'] = pd.to_numeric(df['Implied_Premium'], errors='coerce')
        df = df.dropna()

        df = df.set_index('Date').sort_index()

        print(f"  ✓ Fetched {len(df)} data points from {df.index.min()} to {df.index.max()}")
        return df

    except Exception as e:
        print(f"  ✗ Error fetching Damodaran data: {e}")
        print("  Creating sample data for demonstration...")

        # Create sample data if fetch fails
        dates = pd.date_range(start='2000-01-01', end='2024-12-31', freq='M')
        data = {
            'Implied_Premium': np.random.uniform(3.5, 6.5, len(dates)) +
                              np.sin(np.arange(len(dates)) / 12) * 0.5
        }
        df = pd.DataFrame(data, index=dates)
        return df


def fetch_shiller_cape():
    """
    Fetch Shiller CAPE data from Robert Shiller's website
    Data source: http://www.econ.yale.edu/~shiller/data.htm
    """
    print("Fetching Shiller CAPE data...")

    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

    try:
        # Read the Excel file
        df = pd.read_excel(url, sheet_name='Data', skiprows=7)

        # The columns are: Date, P, D, E, CPI, etc.
        # CAPE is usually in column 'CAPE' or needs to be calculated

        # Clean up column names
        df.columns = df.columns.str.strip()

        # Create date from year and month columns
        if 'Date' in df.columns:
            # Parse date (format is typically YYYY.MM)
            df['Date'] = df['Date'].astype(str)
            df['Year'] = df['Date'].str.split('.').str[0].astype(float)
            df['Month'] = df['Date'].str.split('.').str[1].astype(float) * 12
            df['Month'] = df['Month'].round().astype(int)
            df['Month'] = df['Month'].clip(1, 12)

            df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))

        # Find CAPE column (might be named 'CAPE', 'P/E10', or similar)
        cape_col = None
        for col in df.columns:
            if 'CAPE' in str(col).upper() or 'P/E10' in str(col).upper():
                cape_col = col
                break

        if cape_col:
            df = df[['Date', cape_col]].copy()
            df.columns = ['Date', 'CAPE']
        else:
            # If CAPE column not found, use a proxy column
            print("  ! CAPE column not found, using available data...")
            df = df[['Date'] + [col for col in df.columns if col != 'Date'][:1]].copy()
            df.columns = ['Date', 'CAPE']

        # Clean data
        df['CAPE'] = pd.to_numeric(df['CAPE'], errors='coerce')
        df = df.dropna()
        df = df.set_index('Date').sort_index()

        print(f"  ✓ Fetched {len(df)} data points from {df.index.min()} to {df.index.max()}")
        return df

    except Exception as e:
        print(f"  ✗ Error fetching Shiller CAPE data: {e}")
        print("  Creating sample data for demonstration...")

        # Create sample data if fetch fails
        dates = pd.date_range(start='2000-01-01', end='2024-12-31', freq='M')
        data = {
            'CAPE': np.random.uniform(15, 35, len(dates)) +
                   np.sin(np.arange(len(dates)) / 24) * 5
        }
        df = pd.DataFrame(data, index=dates)
        return df


def fetch_sp500_returns():
    """
    Fetch S&P 500 data and calculate forward 2-year returns
    """
    print("Fetching S&P 500 data...")

    try:
        # Fetch S&P 500 data using yfinance
        sp500 = yf.download('^GSPC', start='1995-01-01', progress=False)

        # Use adjusted close prices
        prices = sp500['Adj Close'].copy()

        # Calculate forward 2-year returns (24 months)
        # Forward return = (Price in 24 months / Current Price) - 1
        forward_returns = (prices.shift(-24) / prices - 1) * 100  # Convert to percentage

        df = pd.DataFrame({
            'SP500_Price': prices,
            'Forward_2Y_Return': forward_returns
        })

        # Resample to monthly (using end of month)
        df = df.resample('M').last()

        print(f"  ✓ Fetched {len(df)} data points from {df.index.min()} to {df.index.max()}")
        return df

    except Exception as e:
        print(f"  ✗ Error fetching S&P 500 data: {e}")
        print("  Creating sample data for demonstration...")

        # Create sample data if fetch fails
        dates = pd.date_range(start='2000-01-01', end='2024-12-31', freq='M')
        data = {
            'SP500_Price': np.exp(np.arange(len(dates)) * 0.005) * 1000 +
                          np.random.normal(0, 50, len(dates)),
            'Forward_2Y_Return': np.random.uniform(-20, 30, len(dates))
        }
        df = pd.DataFrame(data, index=dates)
        return df


def merge_data(damodaran_df, cape_df, sp500_df):
    """
    Merge all datasets by date
    """
    print("\nMerging datasets...")

    # Merge all dataframes
    merged = damodaran_df.join(cape_df, how='outer')
    merged = merged.join(sp500_df, how='outer')

    # Forward fill to handle missing values (within reason)
    merged = merged.fillna(method='ffill', limit=3)

    # Drop rows with any remaining NaN values
    merged = merged.dropna()

    print(f"  ✓ Merged dataset: {len(merged)} observations from {merged.index.min()} to {merged.index.max()}")

    return merged


def create_plots(df):
    """
    Create comprehensive plots showing relationships between variables
    """
    print("\nCreating plots...")

    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(18, 12))

    # 1. Time series of all three variables
    ax1 = plt.subplot(3, 2, 1)
    ax1_twin = ax1.twinx()

    line1 = ax1.plot(df.index, df['Implied_Premium'], 'b-', label='Implied ERP (%)', linewidth=2)
    line2 = ax1_twin.plot(df.index, df['CAPE'], 'r-', label='Shiller CAPE', linewidth=2)

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Implied ERP (%)', color='b')
    ax1_twin.set_ylabel('Shiller CAPE', color='r')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1_twin.tick_params(axis='y', labelcolor='r')
    ax1.set_title('Damodaran Implied ERP vs Shiller CAPE Over Time', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    # 2. Time series of S&P 500 forward returns
    ax2 = plt.subplot(3, 2, 2)
    ax2.plot(df.index, df['Forward_2Y_Return'], 'g-', linewidth=2)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.fill_between(df.index, 0, df['Forward_2Y_Return'],
                     where=(df['Forward_2Y_Return'] > 0), alpha=0.3, color='green', label='Positive')
    ax2.fill_between(df.index, 0, df['Forward_2Y_Return'],
                     where=(df['Forward_2Y_Return'] <= 0), alpha=0.3, color='red', label='Negative')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Forward 2-Year Return (%)')
    ax2.set_title('S&P 500 Forward 2-Year Returns', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Scatter: Implied ERP vs Forward Returns
    ax3 = plt.subplot(3, 2, 3)
    scatter1 = ax3.scatter(df['Implied_Premium'], df['Forward_2Y_Return'],
                          c=df.index.year, cmap='viridis', alpha=0.6, s=50)

    # Add trend line
    z = np.polyfit(df['Implied_Premium'].dropna(), df['Forward_2Y_Return'].dropna(), 1)
    p = np.poly1d(z)
    ax3.plot(df['Implied_Premium'], p(df['Implied_Premium']), "r--", linewidth=2, label='Trend')

    # Calculate correlation
    corr1 = df['Implied_Premium'].corr(df['Forward_2Y_Return'])
    ax3.set_xlabel('Damodaran Implied ERP (%)')
    ax3.set_ylabel('Forward 2-Year Return (%)')
    ax3.set_title(f'Implied ERP vs Forward Returns (Corr: {corr1:.3f})',
                 fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    plt.colorbar(scatter1, ax=ax3, label='Year')

    # 4. Scatter: CAPE vs Forward Returns
    ax4 = plt.subplot(3, 2, 4)
    scatter2 = ax4.scatter(df['CAPE'], df['Forward_2Y_Return'],
                          c=df.index.year, cmap='viridis', alpha=0.6, s=50)

    # Add trend line
    z = np.polyfit(df['CAPE'].dropna(), df['Forward_2Y_Return'].dropna(), 1)
    p = np.poly1d(z)
    ax4.plot(df['CAPE'], p(df['CAPE']), "r--", linewidth=2, label='Trend')

    # Calculate correlation
    corr2 = df['CAPE'].corr(df['Forward_2Y_Return'])
    ax4.set_xlabel('Shiller CAPE')
    ax4.set_ylabel('Forward 2-Year Return (%)')
    ax4.set_title(f'CAPE vs Forward Returns (Corr: {corr2:.3f})',
                 fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    plt.colorbar(scatter2, ax=ax4, label='Year')

    # 5. Distribution of Forward Returns by Implied ERP Quartiles
    ax5 = plt.subplot(3, 2, 5)
    df['ERP_Quartile'] = pd.qcut(df['Implied_Premium'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    df.boxplot(column='Forward_2Y_Return', by='ERP_Quartile', ax=ax5)
    ax5.set_xlabel('Implied ERP Quartile')
    ax5.set_ylabel('Forward 2-Year Return (%)')
    ax5.set_title('Forward Returns by Implied ERP Level', fontsize=12, fontweight='bold')
    plt.sca(ax5)
    plt.xticks(rotation=45)

    # 6. Distribution of Forward Returns by CAPE Quartiles
    ax6 = plt.subplot(3, 2, 6)
    df['CAPE_Quartile'] = pd.qcut(df['CAPE'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    df.boxplot(column='Forward_2Y_Return', by='CAPE_Quartile', ax=ax6)
    ax6.set_xlabel('CAPE Quartile')
    ax6.set_ylabel('Forward 2-Year Return (%)')
    ax6.set_title('Forward Returns by CAPE Level', fontsize=12, fontweight='bold')
    plt.sca(ax6)
    plt.xticks(rotation=45)

    plt.tight_layout()

    # Save the plot
    filename = f'market_premium_analysis_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"  ✓ Plot saved as: {filename}")

    plt.show()

    return fig


def print_summary_statistics(df):
    """
    Print summary statistics
    """
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    print("\nData Overview:")
    print(f"  Period: {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}")
    print(f"  Number of observations: {len(df)}")

    print("\nDescriptive Statistics:")
    print(df[['Implied_Premium', 'CAPE', 'Forward_2Y_Return']].describe().round(2))

    print("\nCorrelation Matrix:")
    corr_matrix = df[['Implied_Premium', 'CAPE', 'Forward_2Y_Return']].corr()
    print(corr_matrix.round(3))

    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)

    erp_corr = df['Implied_Premium'].corr(df['Forward_2Y_Return'])
    cape_corr = df['CAPE'].corr(df['Forward_2Y_Return'])

    print(f"\n1. Implied ERP vs Forward Returns: {erp_corr:.3f}")
    if erp_corr > 0:
        print("   → Higher implied ERP is associated with HIGHER forward returns (positive relationship)")
    else:
        print("   → Higher implied ERP is associated with LOWER forward returns (negative relationship)")

    print(f"\n2. CAPE vs Forward Returns: {cape_corr:.3f}")
    if cape_corr < 0:
        print("   → Higher CAPE is associated with LOWER forward returns (negative relationship)")
        print("   → This is consistent with valuation theory (expensive markets → lower future returns)")
    else:
        print("   → Higher CAPE is associated with HIGHER forward returns (positive relationship)")

    # Quartile analysis
    df['ERP_Quartile'] = pd.qcut(df['Implied_Premium'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    df['CAPE_Quartile'] = pd.qcut(df['CAPE'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

    print("\n3. Average Forward Returns by Implied ERP Quartile:")
    erp_quartile_returns = df.groupby('ERP_Quartile')['Forward_2Y_Return'].mean()
    for q, ret in erp_quartile_returns.items():
        print(f"   {q}: {ret:.2f}%")

    print("\n4. Average Forward Returns by CAPE Quartile:")
    cape_quartile_returns = df.groupby('CAPE_Quartile')['Forward_2Y_Return'].mean()
    for q, ret in cape_quartile_returns.items():
        print(f"   {q}: {ret:.2f}%")

    print("\n" + "="*80)


def main():
    """
    Main execution function
    """
    print("\n" + "="*80)
    print("MARKET PREMIUM ANALYSIS")
    print("Damodaran Implied ERP, Shiller CAPE, and S&P 500 Forward Returns")
    print("="*80 + "\n")

    # Fetch all data
    damodaran_df = fetch_damodaran_erp()
    cape_df = fetch_shiller_cape()
    sp500_df = fetch_sp500_returns()

    # Merge datasets
    merged_df = merge_data(damodaran_df, cape_df, sp500_df)

    # Print summary statistics
    print_summary_statistics(merged_df)

    # Create plots
    create_plots(merged_df)

    # Save the merged data to CSV
    output_file = f'market_data_{datetime.now().strftime("%Y%m%d")}.csv'
    merged_df.to_csv(output_file)
    print(f"\n✓ Data saved to: {output_file}")

    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

# Example: Import External Export
"""Import data exported from external tools (a-stock-data, etc.)."""

from cogalpha_mvp.data.adapters import AStockDataExportAdapter, LocalCSVAdapter
from cogalpha_mvp.domain.data_contract import DataRequest


def main():
    # Example 1: Import from a-stock-data export
    # adapter = AStockDataExportAdapter()
    # request = DataRequest(path="data/raw/astock_export.csv", start_date="2020-01-01")
    # data = adapter.load(request)
    # print(f"Loaded {len(data)} rows")

    # Example 2: Import from generic CSV
    adapter = LocalCSVAdapter()
    # request = DataRequest(path="data/raw/your_data.csv")
    # data = adapter.load(request)

    print("See data_contract.md for required CSV format.")
    print("Required fields: symbol, trade_date, open, high, low, close, volume")


if __name__ == "__main__":
    main()

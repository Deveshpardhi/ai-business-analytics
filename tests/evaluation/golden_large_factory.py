from __future__ import annotations

import numpy as np
import pandas as pd


ROW_COUNT = 100_000
SEED = 20261004


def build_large_golden_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    departments = np.array(
        ["Electronics", "Home", "Apparel", "Grocery"]
    )
    regions = np.array(
        ["North", "South", "East", "West", "Central"]
    )
    genders = np.array(
        ["Male", "Female", "Other"]
    )
    channels = np.array(
        ["Online", "Retail Store", "Distributor"]
    )
    returned_values = np.array(
        ["Yes", "No"]
    )

    transaction_id = np.arange(1, ROW_COUNT + 1)

    dates = pd.date_range(
        "2023-01-01",
        "2025-12-31",
        freq="D",
    )

    transaction_date = rng.choice(
        dates,
        size=ROW_COUNT,
        replace=True,
    )

    department = rng.choice(
        departments,
        size=ROW_COUNT,
        replace=True,
    )

    region = rng.choice(
        regions,
        size=ROW_COUNT,
        replace=True,
    )

    gender = rng.choice(
        genders,
        size=ROW_COUNT,
        replace=True,
    )

    sales_channel = rng.choice(
        channels,
        size=ROW_COUNT,
        replace=True,
    )

    returned = rng.choice(
        returned_values,
        size=ROW_COUNT,
        p=[0.08, 0.92],
    )

    units_sold = rng.integers(
        1,
        18,
        size=ROW_COUNT,
    )

    department_price_ranges = {
        "Electronics": (650.0, 1450.0),
        "Home": (180.0, 480.0),
        "Apparel": (60.0, 220.0),
        "Grocery": (25.0, 120.0),
    }

    unit_price = np.empty(ROW_COUNT)

    for name, (low, high) in department_price_ranges.items():
        mask = department == name

        unit_price[mask] = rng.uniform(
            low,
            high,
            size=mask.sum(),
        )

    discount = rng.uniform(
        0.0,
        0.20,
        size=ROW_COUNT,
    )

    gross_revenue = units_sold * unit_price

    revenue = gross_revenue * (1.0 - discount)

    cost_ratio = rng.normal(
        0.78,
        0.015,
        size=ROW_COUNT,
    )

    cost = revenue * cost_ratio
    profit = revenue - cost

    # ---------------------------------------------------------
    # Inject exactly 50 deliberate Revenue anomalies.
    # ---------------------------------------------------------

    anomaly_indices = rng.choice(
        ROW_COUNT,
        size=50,
        replace=False,
    )

    revenue[anomaly_indices] *= 8.0
    cost[anomaly_indices] = revenue[anomaly_indices] * cost_ratio[
        anomaly_indices
    ]
    profit[anomaly_indices] = (
        revenue[anomaly_indices]
        - cost[anomaly_indices]
    )

    age = rng.integers(
        18,
        71,
        size=ROW_COUNT,
    ).astype(float)

    customer_satisfaction = rng.integers(
        1,
        6,
        size=ROW_COUNT,
    ).astype(float)

    delivery_days = rng.integers(
        1,
        12,
        size=ROW_COUNT,
    ).astype(float)

    employee_count = rng.integers(
        1,
        31,
        size=ROW_COUNT,
    ).astype(float)

    customer_id = np.array(
        [
            f"CUST{i:06d}"
            for i in rng.integers(
                1,
                12_001,
                size=ROW_COUNT,
            )
        ]
    )

    product_category = department.copy()

    products_by_department = {
        "Electronics": [
            "Laptop",
            "Tablet",
            "Smartphone",
            "Monitor",
        ],
        "Home": [
            "Chair",
            "Table",
            "Lamp",
            "Storage",
        ],
        "Apparel": [
            "Shirt",
            "Jeans",
            "Jacket",
            "Shoes",
        ],
        "Grocery": [
            "Rice",
            "Tea",
            "Cereal",
            "Coffee",
        ],
    }

    product = np.empty(
        ROW_COUNT,
        dtype=object,
    )

    for name, products in products_by_department.items():
        mask = department == name

        product[mask] = rng.choice(
            products,
            size=mask.sum(),
        )

    df = pd.DataFrame(
        {
            "TransactionID": transaction_id,
            "TransactionDate": pd.to_datetime(
                transaction_date
            ).strftime("%Y-%m-%d"),
            "CustomerID": customer_id,
            "Age": age,
            "Gender": gender.astype(object),
            "Region": region,
            "Department": department,
            "ProductCategory": product_category,
            "Product": product,
            "SalesChannel": sales_channel,
            "UnitsSold": units_sold,
            "UnitPrice": np.round(unit_price, 2),
            "Discount": np.round(discount, 4),
            "Revenue": np.round(revenue, 2),
            "Cost": np.round(cost, 2),
            "Profit": np.round(profit, 2),
            "CustomerSatisfaction": customer_satisfaction,
            "DeliveryDays": delivery_days,
            "Returned": returned,
            "EmployeeCount": employee_count,
        }
    )

    # ---------------------------------------------------------
    # Inject exactly 250 missing values into six non-key fields.
    # Total missing cells = 1,500.
    # ---------------------------------------------------------

    nullable_columns = [
        "Age",
        "Gender",
        "Discount",
        "CustomerSatisfaction",
        "DeliveryDays",
        "EmployeeCount",
    ]

    for column in nullable_columns:
        missing_indices = rng.choice(
            ROW_COUNT,
            size=250,
            replace=False,
        )

        df.loc[missing_indices, column] = np.nan

    return df


def write_large_golden_dataset(path) -> pd.DataFrame:
    df = build_large_golden_dataset()
    df.to_csv(path, index=False)
    return df
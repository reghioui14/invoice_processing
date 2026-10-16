import numpy as np
import pandas as pd
import random

NUM_INVOICES = 1000
ANOMALY_RATE = 0.07  # 7% of invoices will be deliberately broken

def generate_normal_invoice() -> dict:
    """
    Generate one realistic, internally consistent invoice.
    Returns raw line item data (not yet turned into features).
    """
    num_items = random.randint(1, 15)

    # Realistic unit prices: lognormal distribution avoids negatives,
    # naturally produces mostly-small values with occasional larger ones,
    # which mimics real-world price distributions better than uniform.
    unit_prices = np.random.lognormal(mean=3.0, sigma=0.5, size=num_items)

    # Realistic quantities: mostly small integers
    quantities = np.random.randint(1, 20, size=num_items)

    line_totals = unit_prices * quantities
    total_amount = float(np.sum(line_totals))

    return {
        "num_items": num_items,
        "unit_prices": unit_prices.tolist(),
        "quantities": quantities.tolist(),
        "line_totals": line_totals.tolist(),
        "total_amount": total_amount,
        "is_anomaly": 0,
        "anomaly_type": "none"
    }

def inject_anomaly(invoice: dict) -> dict:
    """
    Deliberately break one aspect of an otherwise normal invoice.
    """
    anomaly_type = random.choice([
        "unit_price_outlier",
        "quantity_outlier",
        "dominant_item",
        "too_many_items"
    ])

    if anomaly_type == "unit_price_outlier" and invoice["num_items"] > 1:
        idx = random.randint(0, invoice["num_items"] - 1)
        invoice["unit_prices"][idx] *= random.uniform(15, 40)

    elif anomaly_type == "quantity_outlier" and invoice["num_items"] > 1:
        idx = random.randint(0, invoice["num_items"] - 1)
        invoice["quantities"][idx] *= random.randint(15, 40)

    elif anomaly_type == "dominant_item" and invoice["num_items"] > 1:
        idx = random.randint(0, invoice["num_items"] - 1)
        invoice["unit_prices"][idx] *= random.uniform(20, 50)

    elif anomaly_type == "too_many_items":
        extra = random.randint(50, 150)
        invoice["num_items"] += extra
        invoice["unit_prices"] += np.random.lognormal(3.0, 0.5, extra).tolist()
        invoice["quantities"] += np.random.randint(1, 20, extra).tolist()

    # Recalculate everything after tampering
    unit_prices = np.array(invoice["unit_prices"])
    quantities = np.array(invoice["quantities"])
    line_totals = unit_prices * quantities

    invoice["unit_prices"] = unit_prices.tolist()
    invoice["quantities"] = quantities.tolist()
    invoice["line_totals"] = line_totals.tolist()
    invoice["total_amount"] = float(np.sum(line_totals))
    invoice["is_anomaly"] = 1
    invoice["anomaly_type"] = anomaly_type

    return invoice

def compute_features(invoice: dict) -> dict:
    """
    Turn raw invoice data into the 4 vendor-agnostic features
    that Isolation Forest will actually learn from.
    """
    unit_prices = np.array(invoice["unit_prices"])
    quantities = np.array(invoice["quantities"])
    line_totals = np.array(invoice["line_totals"])
    total_amount = invoice["total_amount"]

    # Coefficient of variation = std / mean
    # Measures relative spread, independent of scale (a $10 vs $50 spread
    # means something different than a $1000 vs $5000 spread of the same ratio)
    unit_price_cv = float(np.std(unit_prices) / np.mean(unit_prices)) if np.mean(unit_prices) > 0 else 0.0
    quantity_cv = float(np.std(quantities) / np.mean(quantities)) if np.mean(quantities) > 0 else 0.0

    max_line_item_fraction = float(np.max(line_totals) / total_amount) if total_amount > 0 else 0.0

    return {
        "unit_price_cv": unit_price_cv,
        "quantity_cv": quantity_cv,
        "max_line_item_fraction": max_line_item_fraction,
        "num_line_items": invoice["num_items"],
        "is_anomaly": invoice["is_anomaly"],
        "anomaly_type": invoice["anomaly_type"]
    }

def generate_dataset() -> pd.DataFrame:
    num_anomalies = int(NUM_INVOICES * ANOMALY_RATE)
    num_normal = NUM_INVOICES - num_anomalies

    rows = []

    for _ in range(num_normal):
        invoice = generate_normal_invoice()
        rows.append(compute_features(invoice))

    for _ in range(num_anomalies):
        invoice = generate_normal_invoice()
        invoice = inject_anomaly(invoice)
        rows.append(compute_features(invoice))

    df = pd.DataFrame(rows)
    df = df.sample(frac=1).reset_index(drop=True)  # shuffle rows
    return df

if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("training_data.csv", index=False)

    print(f"Generated {len(df)} synthetic invoices")
    print(f"Normal: {len(df[df['is_anomaly'] == 0])}")
    print(f"Anomalies: {len(df[df['is_anomaly'] == 1])}")
    print("\nSample rows:")
    print(df.head(10))
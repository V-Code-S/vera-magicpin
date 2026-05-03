import json
import os
import time

from bot import compose

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "dataset", "expanded")


# ─────────────────────────────────────────
# LOAD HELPERS
# ─────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_all(folder):
    data = {}
    folder_path = os.path.join(DATASET_DIR, folder)

    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            obj = load_json(os.path.join(folder_path, file))

            if folder == "categories":
                data[obj["slug"]] = obj
            elif folder == "merchants":
                data[obj["merchant_id"]] = obj
            elif folder == "customers":
                data[obj["customer_id"]] = obj
            elif folder == "triggers":
                data[obj["id"]] = obj

    return data


# ─────────────────────────────────────────
# LOAD DATASET
# ─────────────────────────────────────────

print("🔄 Loading dataset...")

categories = load_all("categories")
merchants = load_all("merchants")
customers = load_all("customers")
triggers = load_all("triggers")

# 🔥 FIXED TEST PAIRS LOADING (ROBUST)
raw = load_json(os.path.join(DATASET_DIR, "test_pairs.json"))

test_pairs = []

if isinstance(raw, dict):
    # Case: {"T01": {...}}
    if all(isinstance(v, dict) for v in raw.values()):
        for k, v in raw.items():
            v["test_id"] = k
            test_pairs.append(v)

    # Case: {"pairs": [...]}
    elif "pairs" in raw:
        test_pairs = raw["pairs"]

elif isinstance(raw, list):
    # Case: already list of dicts
    if all(isinstance(x, dict) for x in raw):
        test_pairs = raw

    # Case: nested list
    elif len(raw) == 1 and isinstance(raw[0], list):
        test_pairs = raw[0]

    else:
        raise ValueError("Unsupported test_pairs format")

else:
    raise ValueError("Unknown test_pairs format")


print(f"✓ Categories: {len(categories)}")
print(f"✓ Merchants: {len(merchants)}")
print(f"✓ Customers: {len(customers)}")
print(f"✓ Triggers: {len(triggers)}")
print(f"✓ Test pairs: {len(test_pairs)}")

print("\n🎯 Generating test pairs...\n")


# ─────────────────────────────────────────
# GENERATE OUTPUT
# ─────────────────────────────────────────

output = []

for i, pair in enumerate(test_pairs, 1):
    print(f"[{i:02d}/{len(test_pairs)}]")

    merchant = merchants[pair["merchant_id"]]
    category = categories[merchant["category_slug"]]
    trigger = triggers[pair["trigger_id"]]
    customer = customers.get(pair.get("customer_id"))

    result = compose(category, merchant, trigger, customer)

    output.append({
        "test_id": pair.get("test_id", f"T{i:02d}"),
        "trigger_id": pair["trigger_id"],
        "merchant_id": pair["merchant_id"],
        "customer_id": pair.get("customer_id"),
        "trigger_kind": trigger["kind"],
        **result
    })

    time.sleep(0.1)


# ─────────────────────────────────────────
# SAVE FILE
# ─────────────────────────────────────────

output_path = os.path.join(BASE_DIR, "submission.jsonl")

with open(output_path, "w") as f:
    for row in output:
        f.write(json.dumps(row) + "\n")

print("\n✅ Done!")
print(f"📝 Output: {output_path}")

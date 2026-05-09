import json

with open('backend/data/clean_products.json', encoding='utf-8') as f:
    products = json.load(f)

red_in_name = [p for p in products if 'red' in p.get('productDisplayName', '').lower()]
print(f"Found {len(red_in_name)} products with 'red' in name")
for p in red_in_name[:10]:
    print(f"ID: {p['id']}, Name: {p['productDisplayName']}, Color: {p['baseColour']}, Cat: {p['subCategory']}")

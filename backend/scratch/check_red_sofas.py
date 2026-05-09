import json

with open('backend/data/clean_products.json', encoding='utf-8') as f:
    products = json.load(f)

red_sofas = [p for p in products if p.get('subCategory') == 'Sofa' and p.get('baseColour') == 'red']
print(f"Found {len(red_sofas)} red sofas")
for p in red_sofas[:5]:
    print(p)

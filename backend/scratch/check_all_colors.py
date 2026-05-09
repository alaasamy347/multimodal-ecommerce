import json
from collections import Counter

with open('backend/data/clean_products.json', encoding='utf-8') as f:
    products = json.load(f)

all_colors = Counter(p.get('baseColour') for p in products)
print("All product colors:")
for color, count in all_colors.items():
    print(f"{color}: {count}")

red_products = [p for p in products if p.get('baseColour') == 'red']
print(f"\nFound {len(red_products)} red products")
if red_products:
    print("Example red products categories:")
    categories = Counter(p.get('subCategory') for p in red_products)
    for cat, count in categories.items():
        print(f"{cat}: {count}")

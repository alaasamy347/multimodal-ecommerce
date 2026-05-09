import json
from collections import Counter

with open('backend/data/clean_products.json', encoding='utf-8') as f:
    products = json.load(f)

sofa_colors = Counter(p.get('baseColour') for p in products if p.get('subCategory') == 'Sofa')
print("Sofa colors:")
for color, count in sofa_colors.items():
    print(f"{color}: {count}")

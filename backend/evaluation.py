import json
import numpy as np
import faiss

DATA_DIR = "data"
K_VALUES = [1, 5, 10]

with open(f"{DATA_DIR}/clean_products.json") as f:
    products = json.load(f)

image_index = faiss.read_index(f"{DATA_DIR}/image_index.faiss")
text_index = faiss.read_index(f"{DATA_DIR}/text_index.faiss")
id_map = np.load(f"{DATA_DIR}/id_map.npy")

def precision_recall_at_k(query_label, retrieved_ids, k):
    retrieved_k = retrieved_ids[:k]
    relevant = [pid for pid in retrieved_k if products[pid]["subCategory"] == query_label]
    
    precision = len(relevant) / k
    recall = len(relevant) / sum(
        1 for p in products if p["subCategory"] == query_label
    )
    return precision, recall

def evaluate_text_queries():
    results = {k: {"p": [], "r": []} for k in K_VALUES}

    for i, product in enumerate(products):
        label = product["subCategory"]
        query_vector = text_index.reconstruct(i).reshape(1, -1)

        _, ids = image_index.search(query_vector, max(K_VALUES))
        retrieved_ids = ids[0]

        for k in K_VALUES:
            p, r = precision_recall_at_k(label, retrieved_ids, k)
            results[k]["p"].append(p)
            results[k]["r"].append(r)

    for k in K_VALUES:
        print(
            f"Text→Image @ {k}: "
            f"Precision={np.mean(results[k]['p']):.3f}, "
            f"Recall={np.mean(results[k]['r']):.3f}"
        )

if __name__ == "__main__":
    evaluate_text_queries()
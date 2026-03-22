import torch
import clip
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def encode_text(text: str):
    with torch.no_grad():
        tokens = clip.tokenize([text]).to(device)
        return model.encode_text(tokens).float()

def encode_image(image_path: str):
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        return model.encode_image(image).float()

def cosine_sim(a, b):
    return torch.nn.functional.cosine_similarity(a, b).item()
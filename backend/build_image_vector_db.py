import os
import faiss
import pickle
from PIL import Image, ImageDraw, ImageFont
from sentence_transformers import SentenceTransformer
import torch

KNOWLEDGE_BASE_PATH = os.getenv(
    "KNOWLEDGE_BASE_PATH",
    "/home/asperger/genspark_fqa/backend/knowledge_base.txt",
)
IMAGE_DIR = "kb_images"
FAISS_IMAGE_INDEX_PATH = "faiss_image_index.bin"
IMAGE_PATHS_PKL_PATH = "image_paths.pkl"

def render_text_to_image(text, path, width=800, height=1200):
    """Renders a block of text into a PNG image."""
    img = Image.new('RGB', (width, height), color = 'white')
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,10), text, fill=(0,0,0), font=font)
    img.save(path)

def build_image_vector_db():
    """Builds a FAISS vector database from images of the knowledge base."""
    print("Starting to build image vector database...")

    # 1. Create directory for images
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # 2. Read knowledge base and render to images
    try:
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        return

    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    image_paths = []
    for i, chunk in enumerate(chunks):
        img_path = os.path.join(IMAGE_DIR, f"chunk_{i}.png")
        render_text_to_image(chunk, img_path)
        image_paths.append(img_path)
    print(f"Rendered {len(chunks)} text chunks to images.")

    # 3. Load CLIP model
    print("Loading CLIP model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer('clip-ViT-B-32', device=device)

    # 4. Encode images into vectors
    print("Encoding images into vectors...")
    image_embeddings = model.encode(
        [Image.open(path) for path in image_paths],
        batch_size=16,
        convert_to_tensor=True,
        show_progress_bar=True
    )

    # 5. Build FAISS index
    print("Building FAISS index...")
    index = faiss.IndexFlatL2(image_embeddings.shape[1])
    index.add(image_embeddings.cpu().numpy())

    # 6. Save index and image paths
    print(f"Saving FAISS index to {FAISS_IMAGE_INDEX_PATH}")
    faiss.write_index(index, FAISS_IMAGE_INDEX_PATH)

    print(f"Saving image paths to {IMAGE_PATHS_PKL_PATH}")
    with open(IMAGE_PATHS_PKL_PATH, "wb") as f:
        pickle.dump(image_paths, f)

    print("Image vector database build complete.")

if __name__ == "__main__":
    build_image_vector_db()

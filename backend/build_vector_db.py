import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer

KNOWLEDGE_BASE_PATH = os.getenv(
    "KNOWLEDGE_BASE_PATH",
    "/home/asperger/genspark_fqa/backend/knowledge_base.txt",
)
FAISS_INDEX_PATH = "faiss_index.bin"
KNOWLEDGE_CHUNKS_PATH = "knowledge_chunks.pkl"

def build_vector_db():
    """Builds a FAISS vector database from the knowledge base."""
    print("Starting to build vector database...")

    # 1. Read knowledge base
    try:
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        return

    # 2. Split text into chunks (e.g., by paragraph)
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not chunks:
        print("Error: No text chunks found in the knowledge base.")
        return
    print(f"Found {len(chunks)} text chunks.")

    # 3. Load sentence transformer model
    print("Loading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 4. Encode chunks into vectors
    print("Encoding text chunks into vectors...")
    embeddings = model.encode(chunks, show_progress_bar=True)

    # 5. Build FAISS index
    print("Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    # 6. Save index and chunks
    print(f"Saving FAISS index to {FAISS_INDEX_PATH}")
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"Saving knowledge chunks to {KNOWLEDGE_CHUNKS_PATH}")
    with open(KNOWLEDGE_CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print("Vector database build complete.")

if __name__ == "__main__":
    build_vector_db()

import os, glob, pickle, faiss, PyPDF2, pdfplumber
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

APP_DIR = os.environ.get('APP_DIR', '.')
INDEX_PATH = os.path.join(APP_DIR, "faiss_index.bin")
META_PATH = os.path.join(APP_DIR, "faiss_meta.pkl")

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedder

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except:
        try:
            for page in PyPDF2.PdfReader(pdf_path).pages:
                text += (page.extract_text() or "") + "\n"
        except:
            pass
    return text

def ingest_documents(docs_dir):
    if not os.path.exists(docs_dir):
        return 0

    existing_metadata = []
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, 'rb') as f:
                existing_metadata = pickle.load(f)
        except:
            pass

    existing_filenames = set([d['filename'] for d in existing_metadata])

    files = glob.glob(os.path.join(docs_dir, "*"))
    
    embedder = get_embedder()
    
    # Load or create FAISS index
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        # MiniLM uses 384 dimensions
        index = faiss.IndexFlatL2(384)

    total_new_chunks = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        if filename in existing_filenames:
            continue

        print(f"📄 Reading {filename}...", flush=True)
        text = ""

        if filepath.lower().endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        elif filepath.lower().endswith((".htm", ".html")):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = BeautifulSoup(f.read(), 'html.parser').get_text(separator=' ')
        elif filepath.lower().endswith(".txt"):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        file_chunks = []
        if text.strip():
            for i in range(0, len(text), 1500):
                chunk = text[i:i+1500]
                if len(chunk) > 50:
                    file_chunks.append(chunk)

        if file_chunks:
            print(f"   🔄 Encoding {len(file_chunks)} chunks for {filename}...", flush=True)
            
            # Encode just this file's chunks
            embeddings = embedder.encode(file_chunks, convert_to_numpy=True)
            index.add(embeddings)
            
            # Update metadata
            new_meta = [{"filename": filename, "content": c} for c in file_chunks]
            existing_metadata.extend(new_meta)
            existing_filenames.add(filename)
            total_new_chunks += len(file_chunks)
            
            # Save progress immediately! (If it crashes, you don't lose progress)
            faiss.write_index(index, INDEX_PATH)
            with open(META_PATH, 'wb') as f:
                pickle.dump(existing_metadata, f)
                
            print(f"   ✅ Saved {filename} to database.\n", flush=True)

    return total_new_chunks

def search_documents(query, top_k=5):
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return []

    try:
        embedder = get_embedder()
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, 'rb') as f:
            metadata = pickle.load(f)

        distances, indices = index.search(embedder.encode([query], convert_to_numpy=True), top_k)

        results = []
        file_count = {}
        for idx in indices[0]:
            if idx != -1 and idx < len(metadata):
                doc = metadata[idx]
                fname = doc['filename']
                file_count[fname] = file_count.get(fname, 0) + 1
                if file_count[fname] <= 2:
                    results.append(doc)
        return results
    except:
        return []

def get_all_documents():
    if not os.path.exists(META_PATH):
        return []
    with open(META_PATH, 'rb') as f:
        return pickle.load(f)
"""Example: ingest a local text file into the RAG index.

Usage: uv run python scripts/ingest_example.py path/to/file.txt
"""

import sys

from app.rag import ingest_document

if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        text = f.read()

    count = ingest_document(text, source=path)
    print(f"Ingested {count} chunks from {path}")

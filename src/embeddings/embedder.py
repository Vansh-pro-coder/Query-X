# import os
# from src.ingestion.chunker import create_chunks

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types


# # Load variables from .env
# from pathlib import Path

# # Find the project root
# PROJECT_ROOT = Path(__file__).resolve().parents[2]

# # Load .env from project root
# load_dotenv(PROJECT_ROOT / ".env")

# # Get API key
# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env")

# # Connect to Gemini
# client = genai.Client(api_key=api_key)


# # Test text
# text = "The central library is located in Block A."


# # Generate embedding
# result = client.models.embed_content(
#     model="gemini-embedding-2",
#     contents=text,
#     config=types.EmbedContentConfig(
#         output_dimensionality=768
#     )
# )


# # Get embedding
# embedding = result.embeddings[0].values


# print("Embedding generated successfully!")
# print("Embedding dimensions:", len(embedding))
# print("First 10 values:", embedding[:10])

import os
from pathlib import Path
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb

from src.ingestion.pdf_loader import extract_text_from_pdf
from src.ingestion.chunker import create_chunks
# import re


# ----------------------------------------
# 1. Load API key
# ----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")


# ----------------------------------------
# 2. Connect to Gemini
# ----------------------------------------

client = genai.Client(api_key=api_key)


# ----------------------------------------
# 3. Load PDF
# ----------------------------------------

pdf_path = PROJECT_ROOT / "data" / "raw" / "knowledge-base.pdf"

text = extract_text_from_pdf(pdf_path)

print(f"Total characters: {len(text):,}")


# ----------------------------------------
# 4. Create chunks
# ----------------------------------------

chunks = create_chunks(
    text,
    chunk_size=500,
    overlap=50
)

print(f"Total chunks: {len(chunks)}")


# ----------------------------------------
# 5. Create embeddings
# ----------------------------------------

# embeddings = []

# for i, chunk in enumerate(chunks):

#     result = client.models.embed_content(
#         model="gemini-embedding-2",
#         contents=chunk,
#         config=types.EmbedContentConfig(
#             output_dimensionality=768
#         )
#     )

#     embedding = result.embeddings[0].values

#     embeddings.append(embedding)

#     print(
#         f"Embedded chunk {i + 1}/{len(chunks)}"
#     )

#Modified

embedded_chunks = []

for i, chunk in enumerate(chunks):

    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=chunk,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    embedding = result.embeddings[0].values

    embedded_chunks.append({
        "chunk_id": i,
        "text": chunk,
        "embedding": embedding
    })

    print(f"Embedded chunk {i + 1}/{len(chunks)}")


# Save embeddings
output_path = PROJECT_ROOT / "data" / "processed" / "embeddings.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(
        embedded_chunks,
        file,
        ensure_ascii=False,
        indent=2
    )

print("\nEmbedding process completed!")
print(f"Total chunks: {len(embedded_chunks)}")
print(f"Embedding dimensions: {len(embedded_chunks[0]['embedding'])}")
print(f"Saved to: {output_path}")

# ----------------------------------------
# 6. Store embeddings in ChromaDB
# ----------------------------------------

database_path = PROJECT_ROOT / "vector_db"

chroma_client = chromadb.PersistentClient(
    path=str(database_path)
)

collection = chroma_client.get_or_create_collection(
    name="campus_knowledge",
    metadata={"hnsw:space": "cosine"}
)

collection.delete(
    ids=collection.get()["ids"]
)

collection.upsert(
    ids=[
        f"chunk_{item['chunk_id']}"
        for item in embedded_chunks
    ],
    documents=[
        item["text"]
        for item in embedded_chunks
    ],
    embeddings=[
        item["embedding"]
        for item in embedded_chunks
    ],
    metadatas=[
        {"chunk_id": item["chunk_id"]}
        for item in embedded_chunks
    ]
)

print("\nChromaDB storage completed!")
print("Total records in database:", collection.count())
print("Database location:", database_path)
# ----------------------------------------
# 6. Final result
# ----------------------------------------

print("\nEmbedding process completed!")

print("Total chunks:", len(chunks))
# print("Embedding dimensions:", len(embedded_chunks[0]))

# 7. Final result

print("\nEmbedding process completed!")
print("Total chunks:", len(embedded_chunks))
print(
    "Embedding dimensions:",
    len(embedded_chunks[0]["embedding"])
)
print("ChromaDB records:", collection.count())



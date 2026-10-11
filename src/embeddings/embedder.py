# # import os
# # from src.ingestion.chunker import create_chunks

# # from dotenv import load_dotenv
# # from google import genai
# # from google.genai import types


# # # Load variables from .env
# # from pathlib import Path

# # # Find the project root
# # PROJECT_ROOT = Path(__file__).resolve().parents[2]

# # # Load .env from project root
# # load_dotenv(PROJECT_ROOT / ".env")

# # # Get API key
# # api_key = os.getenv("GEMINI_API_KEY")

# # if not api_key:
# #     raise ValueError("GEMINI_API_KEY not found in .env")

# # # Connect to Gemini
# # client = genai.Client(api_key=api_key)


# # # Test text
# # text = "The central library is located in Block A."


# # # Generate embedding
# # result = client.models.embed_content(
# #     model="gemini-embedding-2",
# #     contents=text,
# #     config=types.EmbedContentConfig(
# #         output_dimensionality=768
# #     )
# # )


# # # Get embedding
# # embedding = result.embeddings[0].values


# # print("Embedding generated successfully!")
# # print("Embedding dimensions:", len(embedding))
# # print("First 10 values:", embedding[:10])

# import os
# from pathlib import Path
# import json

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types
# import chromadb

# from src.ingestion.pdf_loader import extract_text_from_pdf
# from src.ingestion.chunker import create_chunks
# # import re


# # ----------------------------------------
# # 1. Load API key
# # ----------------------------------------

# PROJECT_ROOT = Path(__file__).resolve().parents[2]

# load_dotenv(PROJECT_ROOT / ".env")

# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env")


# # ----------------------------------------
# # 2. Connect to Gemini
# # ----------------------------------------

# client = genai.Client(api_key=api_key)


# # ----------------------------------------
# # 3. Load PDF
# # ----------------------------------------

# pdf_path = PROJECT_ROOT / "data" / "raw" / "knowledge-base.pdf"

# text = extract_text_from_pdf(pdf_path)

# print(f"Total characters: {len(text):,}")


# # ----------------------------------------
# # 4. Create chunks
# # ----------------------------------------

# chunks = create_chunks(
#     text,
#     chunk_size=500,
#     overlap=50
# )

# print(f"Total chunks: {len(chunks)}")


# # ----------------------------------------
# # 5. Create embeddings
# # ----------------------------------------

# # embeddings = []

# # for i, chunk in enumerate(chunks):

# #     result = client.models.embed_content(
# #         model="gemini-embedding-2",
# #         contents=chunk,
# #         config=types.EmbedContentConfig(
# #             output_dimensionality=768
# #         )
# #     )

# #     embedding = result.embeddings[0].values

# #     embeddings.append(embedding)

# #     print(
# #         f"Embedded chunk {i + 1}/{len(chunks)}"
# #     )

# #Modified

# embedded_chunks = []

# for i, chunk in enumerate(chunks):

#     result = client.models.embed_content(
#         model="gemini-embedding-2",
#         contents=chunk,
#         config=types.EmbedContentConfig(
#             output_dimensionality=768
#         )
#     )

#     embedding = result.embeddings[0].values

#     embedded_chunks.append({
#         "chunk_id": i,
#         "text": chunk,
#         "embedding": embedding
#     })

#     print(f"Embedded chunk {i + 1}/{len(chunks)}")


# # Save embeddings
# output_path = PROJECT_ROOT / "data" / "processed" / "embeddings.json"

# with open(output_path, "w", encoding="utf-8") as file:
#     json.dump(
#         embedded_chunks,
#         file,
#         ensure_ascii=False,
#         indent=2
#     )

# print("\nEmbedding process completed!")
# print(f"Total chunks: {len(embedded_chunks)}")
# print(f"Embedding dimensions: {len(embedded_chunks[0]['embedding'])}")
# print(f"Saved to: {output_path}")

# # ----------------------------------------
# # 6. Store embeddings in ChromaDB
# # ----------------------------------------

# database_path = PROJECT_ROOT / "vector_db"

# chroma_client = chromadb.PersistentClient(
#     path=str(database_path)
# )

# collection = chroma_client.get_or_create_collection(
#     name="campus_knowledge",
#     metadata={"hnsw:space": "cosine"}
# )

# collection.delete(
#     ids=collection.get()["ids"]
# )

# collection.upsert(
#     ids=[
#         f"chunk_{item['chunk_id']}"
#         for item in embedded_chunks
#     ],
#     documents=[
#         item["text"]
#         for item in embedded_chunks
#     ],
#     embeddings=[
#         item["embedding"]
#         for item in embedded_chunks
#     ],
#     metadatas=[
#         {"chunk_id": item["chunk_id"]}
#         for item in embedded_chunks
#     ]
# )

# print("\nChromaDB storage completed!")
# print("Total records in database:", collection.count())
# print("Database location:", database_path)
# # ----------------------------------------
# # 6. Final result
# # ----------------------------------------

# print("\nEmbedding process completed!")

# print("Total chunks:", len(chunks))
# # print("Embedding dimensions:", len(embedded_chunks[0]))

# # 7. Final result

# print("\nEmbedding process completed!")
# print("Total chunks:", len(embedded_chunks))
# print(
#     "Embedding dimensions:",
#     len(embedded_chunks[0]["embedding"])
# )
# print("ChromaDB records:", collection.count())




import os
import json
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.ingestion.pdf_loader import extract_text_from_pdf
from src.ingestion.chunker import create_chunks


# 1. Project configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FOLDER = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "embeddings.json"
DATABASE_PATH = PROJECT_ROOT / "vector_db"

load_dotenv(PROJECT_ROOT / ".env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def main():
    # 2. Find all PDFs
    pdf_files = sorted(RAW_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {RAW_FOLDER}")
        return

    print(f"Found {len(pdf_files)} PDF file(s).")

    # 3. Extract pages from all PDFs
    all_pages = []

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        pages = extract_text_from_pdf(pdf_path)
        all_pages.extend(pages)

    if not all_pages:
        print("No extractable text found in the PDF files.")
        return

    # 4. Create chunks with source metadata
    chunks = create_chunks(
        all_pages,
        chunk_size=700,
        overlap=100
    )

    if not chunks:
        print("No chunks were created.")
        return

    print(f"\nTotal chunks: {len(chunks)}")

    # 5. Generate embeddings
    embedded_chunks = []

    for i, chunk in enumerate(chunks):
        result = client.models.embed_content(
            model="gemini-embedding-2",
            contents=chunk["text"],
            config=types.EmbedContentConfig(
                output_dimensionality=768
            )
        )

        embedding = result.embeddings[0].values

        embedded_chunks.append({
            "chunk_id": i,
            "text": chunk["text"],
            "source": chunk["source"],
            "page": chunk["page"],
            "embedding": embedding
        })

        print(f"Embedded chunk {i + 1}/{len(chunks)}")

    # 6. Save embedding data
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            embedded_chunks,
            file,
            ensure_ascii=False
        )

    print(f"\nEmbeddings saved to: {OUTPUT_PATH}")

    # 7. Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(
        path=str(DATABASE_PATH)
    )

    collection = chroma_client.get_or_create_collection(
        name="campus_knowledge",
        metadata={"hnsw:space": "cosine"}
    )

    # 8. Replace the old index only after new embeddings are ready
    # This collection contains the index for all PDFs in data/raw/.
    existing_ids = collection.get()["ids"]

    if existing_ids:
        collection.delete(ids=existing_ids)

    # Insert in batches to avoid oversized requests
    batch_size = 100

    for start in range(0, len(embedded_chunks), batch_size):
        batch = embedded_chunks[start:start + batch_size]

        collection.upsert(
            ids=[f"chunk_{item['chunk_id']}" for item in batch],
            documents=[item["text"] for item in batch],
            embeddings=[item["embedding"] for item in batch],
            metadatas=[
                {
                    "chunk_id": item["chunk_id"],
                    "source": item["source"],
                    "page": item["page"]
                }
                for item in batch
            ]
        )

        print(
            f"Stored chunks {start + 1}-"
            f"{start + len(batch)} of {len(embedded_chunks)}"
        )

    print("\nIngestion completed successfully!")
    print(f"PDF files processed: {len(pdf_files)}")
    print(f"Chunks created: {len(embedded_chunks)}")
    print(f"ChromaDB records: {collection.count()}")
    print(f"Database location: {DATABASE_PATH}")


if __name__ == "__main__":
    main()

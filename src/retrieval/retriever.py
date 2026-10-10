
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
import re
from src.generation.answer_generator import generate_answer

# Find project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load API key
load_dotenv(PROJECT_ROOT / ".env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Connect to Gemini
gemini_client = genai.Client(api_key=api_key)

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(PROJECT_ROOT / "vector_db")
)

collection = chroma_client.get_collection(
    name="campus_knowledge"
)



def find_exact_erp(question):

    # Find an ERP-like number in the question
    match = re.search(r"\b\d{7}\b", question)

    if not match:
        return None

    erp_number = match.group(0)

    # Search the stored chunk text for the exact number
    results = collection.get(
        where_document={"$contains": erp_number},
        include=["documents", "metadatas"]
    )

    matches = []

    for i, text in enumerate(results["documents"]):
        matches.append({
            "text": text,
            "chunk_id": results["metadatas"][i]["chunk_id"]
        })

    return matches

def retrieve_chunks(question, top_k=3):

    # Convert the question into an embedding
    result = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=question,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    query_embedding = result.embeddings[0].values

    # Find similar chunks in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    retrieved_chunks = []

    for i, text in enumerate(results["documents"][0]):
        retrieved_chunks.append({
            "text": text,
            "chunk_id": results["metadatas"][0][i]["chunk_id"],
            "distance": results["distances"][0][i]
        })

    return retrieved_chunks


#__________________________________________________________________________________


# if __name__ == "__main__":

#     question = input("Ask a campus question: ")

#     # chunks = retrieve_chunks(question)

#     chunks = find_exact_erp(question)

#     if chunks is None:
#     chunks = retrieve_chunks(question)

#     if not chunks:
#         print("No matching record found in the database.")
#         continue

#         for chunk in chunks:
#         print(f"Chunk ID: {chunk['chunk_id']}")
#         print(f"Text: {chunk['text']}")
#         print("-" * 50)


#         print("\nMost relevant chunks:\n")

#         for chunk in chunks:
#             print(f"Chunk ID: {chunk['chunk_id']}")
#             print(f"Distance: {chunk['distance']:.4f}")
#             print(f"Text: {chunk['text']}")

# if __name__ == "__main__":

#     while True:
#         question = input(
#             "\nAsk a campus question (or type 'exit'): "
#         )

#         if question.strip().lower() == "exit":
#             break

#         if not question.strip():
#             continue

#         # Try exact ERP search first
#         chunks = find_exact_erp(question)

#         # If no ERP number was detected, use semantic search
#         # if chunks is None:
#         #     chunks = retrieve_chunks(question)

#         # if not chunks:
#         #     print("No matching record found in the database.")
#         #     continue

#         # print("\nMatching chunks:\n")

#         # for chunk in chunks:
#         #     print(f"Chunk ID: {chunk['chunk_id']}")
#         #     print(f"Text: {chunk['text']}")
#         #     if "distance" in chunk:
#         #         print(f"Distance: {chunk['distance']:.4f}")
#         #     print("-" * 50)

#         #     # print("-" * 50)

#         if not chunks:
#             print("\nQuery-X: I couldn't find that information in the document.")
#             continue

#         answer = generate_answer(question, chunks)
#         print(f"\nQuery-X: {answer}")



if __name__ == "__main__":

    while True:
        question = input(
            "\nAsk a campus question (or type 'exit'): "
        )

        if question.strip().lower() == "exit":
            break

        if not question.strip():
            continue

        # Try exact ERP search first
        chunks = find_exact_erp(question)

        # If no ERP number was detected, use semantic search
        if chunks is None:
            chunks = retrieve_chunks(question)

        if not chunks:
            print(
                "\nQuery-X: I couldn't find that information "
                "in the document."
            )
            continue

        # Generate a concise answer from retrieved context
        answer = generate_answer(question, chunks)
        print(f"\nQuery-X: {answer}")


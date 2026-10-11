
# from src.retrieval.retriever import retrieve_chunks
# from src.generation.answer_generator import generate_answer


# def get_chatbot_response(question):
#     """Retrieve relevant knowledge and generate a grounded answer."""

#     question = question.strip()

#     if not question:
#         return {
#             "answer": "Please enter a question.",
#             "supported": False,
#             "sources": []
#         }

#     # Step 1: Retrieve relevant information from the vector database
#     chunks = retrieve_chunks(question, top_k=3)

#     # Step 2: Handle questions with no retrieved information
#     if not chunks:
#         return {
#             "answer": "Sorry, I couldn't find relevant information in the knowledge base.",
#             "supported": False,
#             "sources": []
#         }

#     # Step 3: Generate an answer using the retrieved information
#     answer = generate_answer(question, chunks)

#     return {
#         "answer": answer,
#         "supported": True,
#         "sources": []
#     }


from src.retrieval.retriever import (
    find_exact_erp,
    retrieve_chunks,
)
from src.generation.answer_generator import generate_answer


def get_chatbot_response(question):
    """Retrieve relevant knowledge and generate a grounded answer."""

    question = question.strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "supported": False,
            "sources": []
        }

    # Step 1: Try exact ERP search first
    chunks = find_exact_erp(question)

    # Step 2: Use semantic search if no ERP number was detected
    if chunks is None:
        chunks = retrieve_chunks(question, top_k=3)

    # Step 3: Handle missing information
    if not chunks:
        return {
            "answer": (
                "Sorry, I couldn't find relevant information "
                "in the knowledge base."
            ),
            "supported": False,
            "sources": []
        }

    # Step 4: Generate the answer from retrieved context
    answer = generate_answer(question, chunks)

    # Step 5: Include source information for the frontend
    sources = []

    for chunk in chunks:
        sources.append({
            "file": chunk.get("source", "Unknown source"),
            "page": chunk.get("page"),
            "snippet": chunk["text"]
        })

    return {
        "answer": answer,
        "supported": True,
        "sources": sources
    }

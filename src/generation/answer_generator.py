
# import os
# from pathlib import Path

# from dotenv import load_dotenv
# from google import genai

# # Find the project root
# PROJECT_ROOT = Path(__file__).resolve().parents[2]

# # Load the API key
# load_dotenv(PROJECT_ROOT / ".env")
# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env")

# # Connect to Gemini
# client = genai.Client(api_key=api_key)


# def generate_answer(question, chunks):
#     if not chunks:
#         return "I couldn't find that information in the document."

#     context = "\n\n".join(chunk["text"] for chunk in chunks)

#     prompt = f"""
# You are Query-X, a campus information assistant.

# Answer using ONLY the supplied context.

# Rules:
# 1. Answer the specific question asked.
# 2. Do not guess or use outside knowledge.
# 3. If the context does not clearly support an answer,
#    say: "I couldn't find that information in the document."
# 4. Do not reveal passwords or phone numbers.
# 5. Keep the answer concise.

# CONTEXT:
# {context}

# QUESTION:
# {question}

# ANSWER:
# """

#     # response = client.models.generate_content(
#     #     model="gemini-3.8-flash",
#     #     contents=prompt

# response = None

# for attempt in range(3):
#     try:
#         response = client.models.generate_content(
#             model="gemini-3.8-flash",
#             contents=prompt
#         )
#         break

#     except Exception as exc:
#         error_text = str(exc)

#         # Retry only temporary service or rate-limit errors
#         temporary_error = (
#             "503" in error_text
#             or "UNAVAILABLE" in error_text
#             or "429" in error_text
#             or "RESOURCE_EXHAUSTED" in error_text
#         )

#         if not temporary_error or attempt == 2:
#             raise

#         time.sleep(2 ** attempt)

# if response is None:
#     return "Gemini is temporarily unavailable. Please try again."

#     )

#     answer = (response.text or "").strip()

#     if not answer:
#         return "I couldn't find that information in the document."

#     return answer


import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the API key
load_dotenv(PROJECT_ROOT / ".env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Connect to Gemini
client = genai.Client(api_key=api_key)


def generate_answer(question, chunks):
    if not chunks:
        return "I couldn't find that information in the document."

    context = "\n\n".join(chunk["text"] for chunk in chunks)

    prompt = f"""
You are Query-X, a campus information assistant.

Answer using ONLY the supplied context.

Rules:
1. Answer the specific question asked.
2. Do not guess or use outside knowledge.
3. If the context does not clearly support an answer,
   say: "I couldn't find that information in the document."
4. Do not reveal passwords or phone numbers.
5. Keep the answer concise.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    response = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            break

        except Exception as exc:
            error_text = str(exc)
            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if not temporary_error or attempt == 2:
                raise

            time.sleep(2 ** attempt)

    if response is None:
        return "Gemini is temporarily unavailable. Please try again."

    answer = (response.text or "").strip()

    if not answer:
        return "I couldn't find that information in the document."

    return answer

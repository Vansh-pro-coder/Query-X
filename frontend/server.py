"""
server.py  |  Small Flask server that connects the website to your RAG code
-----------------------------------------------------------------------------
What it does:
  1. Serves index.html / style.css / script.js  (so the site opens at
     http://localhost:5000)
  2. POST /api/chat      -> receives a question, calls YOUR RAG function,
                            returns answer + sources as JSON
  3. POST /api/feedback  -> stores thumbs up / down from testers
  4. GET  /pdf/<name>    -> lets the "View PDF" button open your PDFs

Run it:
    pip install flask
    python server.py
Then open http://localhost:5000 and turn OFF "Demo mode" in Settings.
"""

# import json
# import os
# from datetime import datetime

# from flask import Flask, jsonify, request, send_from_directory



# import sys
# from pathlib import Path

# from src.chatbot import get_chatbot_response

# PROJECT_ROOT = Path(__file__).resolve().parent.parent

# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Find the main Query-X project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow Python to import the project's src package
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory
from src.chatbot import get_chatbot_response



# static_folder="." means: serve the html/css/js files sitting next to this file
app = Flask(__name__, static_folder=".", static_url_path="")

PDF_FOLDER = "docs"  # <-- put your PDF files in a folder with this name


# ---------------------------------------------------------------------------
# STEP 1 (YOUR JOB): connect your existing RAG code here
# ---------------------------------------------------------------------------
# def get_rag_answer(question: str, history: list, language: str) -> dict:
#     """
#     Replace the body of this function with a call to your own RAG code.

#     Inputs
#       question : the user's current question, e.g. "Where is it held?"
#       history  : previous messages, e.g. [{"role": "user", "text": "..."},
#                                           {"role": "bot",  "text": "..."}]
#                  Use it to understand follow-ups ("it", "that event").
#                  Tip: ask your LLM to rewrite the question into a standalone one
#                  first, e.g. "Where is the Annual Tech Fest held?"
#       language : "en" or "hi"  (answer in this language)

#     Must return a dictionary like:
#       {
#         "answer": "The Tech Fest is held at the main auditorium.",
#         "supported": True,     # False if the documents don't contain the answer
#         "sources": [
#           {"file": "Campus Events.pdf",   # must match a file in the docs folder
#            "page": 2,
#            "section": "Student activities",   # optional
#            "snippet": "exact text of the retrieved chunk"}
#         ],
#       }
#     """

# import sys
# from pathlib import Path

# Locate the main Query-X project folder
# PROJECT_ROOT = Path(__file__).resolve().parent.parent

# # Allow Python to import modules from the project root
# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))

# from src.chatbot import get_chatbot_response


def get_rag_answer(question, language="English", history=None):
    """Connect the frontend request to the existing RAG chatbot."""

    result = get_chatbot_response(question)

    return {
        "answer": result["answer"],
        "supported": result["supported"],
        "sources": result["sources"]
    }

    # Example of how it could look (uncomment and adapt):
    #
    # from my_rag import answer_question        # <- your existing file
    # result = answer_question(question, history, language)
    # return {
    #     "answer": result.text,
    #     "supported": result.score > 0.5,      # your own relevance check
    #     "sources": [
    #         {"file": c.pdf_name, "page": c.page, "snippet": c.text}
    #         for c in result.chunks
    #     ],
    # }

    # Temporary placeholder so the server runs before you connect anything:
    # return {"answer": "", "supported": False, "sources": []}


# ---------------------------------------------------------------------------
# Routes (you normally don't need to edit below this line)
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    history = data.get("history") or []
    language = data.get("language") or "en"

    # Reliable fallback: reject empty questions
    if not question:
        return jsonify({"error": "Empty question"}), 400

    try:
        result = get_rag_answer(question, history, language)
        return jsonify(result)
    except Exception as exc:  # any crash in the RAG code -> clean error for the UI
        print("RAG error:", exc)
        return jsonify({"error": "Internal error"}), 500


@app.route("/api/feedback", methods=["POST"])
def feedback():
    """Appends every thumbs up/down to feedback.jsonl so you can review it later."""
    data = request.get_json(silent=True) or {}
    data["time"] = datetime.now().isoformat()
    with open("feedback.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
    return jsonify({"ok": True})


@app.route("/pdf/<path:name>")
def pdf(name):
    return send_from_directory(os.path.abspath(PDF_FOLDER), name)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

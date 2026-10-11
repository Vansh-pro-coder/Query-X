# # import fitz


# # def extract_text_from_pdf(pdf_path):
# #     document = fitz.open(pdf_path)

# #     all_text = ""

# #     for page in document:
# #         all_text += page.get_text()

# #     document.close()

# #     return all_text


# # if __name__ == "__main__":
# #     pdf_path = "data/raw/knowledge-base.pdf"

# #     text = extract_text_from_pdf(pdf_path)

# #     print(text)

# import pymupdf as fitz


# def extract_text_from_pdf(pdf_path):

#     print("=" * 45)
#     print("       PDF INGESTION STARTED")
#     print("=" * 45)

#     document = fitz.open(pdf_path)

#     print("[✓] PDF loaded successfully")
#     print(f"[✓] Total pages: {len(document)}")

#     all_text = ""

#     for page in document:
#         all_text += page.get_text()

#     document.close()

#     # Calculate statistics
#     total_characters = len(all_text)
#     total_words = len(all_text.split())

#     print("[✓] Text extracted successfully")
#     print(f"[✓] Total characters: {total_characters:,}")
#     print(f"[✓] Total words: {total_words:,}")

#     print("=" * 45)
#     print("       PDF INGESTION COMPLETED")
#     print("=" * 45)

#     return all_text


# if __name__ == "__main__":

#     pdf_path = "data/raw/knowledge-base.pdf"

#     text = extract_text_from_pdf(pdf_path)
#     print(text)


import pymupdf as fitz
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """Extract text page by page, preserving source filename and page number."""

    pdf_path = Path(pdf_path)
    pages = []

    print("=" * 45)
    print(f"Processing PDF: {pdf_path.name}")
    print("=" * 45)

    with fitz.open(pdf_path) as document:
        print(f"[✓] PDF loaded: {len(document)} pages")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text().strip()

            if text:
                pages.append({
                    "text": text,
                    "source": pdf_path.name,
                    "page": page_number,
                })

    total_text = "\n".join(item["text"] for item in pages)

    print(f"[✓] Extracted {len(pages)} pages containing text")
    print(f"[✓] Total words: {len(total_text.split()):,}")
    print("=" * 45)

    return pages


if __name__ == "__main__":
    pdf_path = Path("data/raw/knowledge-base.pdf")
    pages = extract_text_from_pdf(pdf_path)

    for item in pages:
        print(f"\n--- Page {item['page']} ---")
        print(item["text"])

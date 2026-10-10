# import fitz


# def extract_text_from_pdf(pdf_path):
#     document = fitz.open(pdf_path)

#     all_text = ""

#     for page in document:
#         all_text += page.get_text()

#     document.close()

#     return all_text


# if __name__ == "__main__":
#     pdf_path = "data/raw/knowledge-base.pdf"

#     text = extract_text_from_pdf(pdf_path)

#     print(text)

import pymupdf as fitz


def extract_text_from_pdf(pdf_path):

    print("=" * 45)
    print("       PDF INGESTION STARTED")
    print("=" * 45)

    document = fitz.open(pdf_path)

    print("[✓] PDF loaded successfully")
    print(f"[✓] Total pages: {len(document)}")

    all_text = ""

    for page in document:
        all_text += page.get_text()

    document.close()

    # Calculate statistics
    total_characters = len(all_text)
    total_words = len(all_text.split())

    print("[✓] Text extracted successfully")
    print(f"[✓] Total characters: {total_characters:,}")
    print(f"[✓] Total words: {total_words:,}")

    print("=" * 45)
    print("       PDF INGESTION COMPLETED")
    print("=" * 45)

    return all_text


if __name__ == "__main__":

    pdf_path = "data/raw/knowledge-base.pdf"

    text = extract_text_from_pdf(pdf_path)
    print(text)
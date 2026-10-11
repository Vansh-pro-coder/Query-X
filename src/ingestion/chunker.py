# def create_chunks(text, chunk_size=500, overlap=50):
#     words = text.split()

#     chunks = []
#     current_chunk = []
#     current_length = 0

#     for word in words:
#         word_length = len(word) + 1

#         if current_length + word_length > chunk_size:
#             chunks.append(" ".join(current_chunk))

#             overlap_words = []
#             overlap_length = 0

#             for previous_word in reversed(current_chunk):
#                 if overlap_length + len(previous_word) + 1 > overlap:
#                     break

#                 overlap_words.insert(0, previous_word)
#                 overlap_length += len(previous_word) + 1

#             current_chunk = overlap_words
#             current_length = overlap_length

#         current_chunk.append(word)
#         current_length += word_length

#     if current_chunk:
#         chunks.append(" ".join(current_chunk))

#     return chunks


# if __name__ == "__main__":

#     sample_text = """
#     The central library is located in Block A.
#     The library is open from 8 AM to 8 PM.
#     Students can borrow up to five books.
#     """

#     chunks = create_chunks(
#         sample_text,
#         chunk_size=100,
#         overlap=20
#     )

#     print(f"Total chunks: {len(chunks)}")

#     for i, chunk in enumerate(chunks):

#         print(f"\n--- Chunk {i + 1} ---")
#         print(chunk)


def create_chunks(pages, chunk_size=500, overlap=50):
    """
    Create text chunks while preserving each chunk's source PDF and page.

    Expected input:
    [
        {"text": "...", "source": "campus.pdf", "page": 1},
        {"text": "...", "source": "rules.pdf", "page": 1}
    ]
    """

    chunks = []

    for page_data in pages:
        text = page_data["text"]
        source = page_data["source"]
        page_number = page_data["page"]

        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1

            if current_chunk and current_length + word_length > chunk_size:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "source": source,
                    "page": page_number
                })

                # Keep some words from the previous chunk for context.
                overlap_words = []
                overlap_length = 0

                for previous_word in reversed(current_chunk):
                    length = len(previous_word) + 1

                    if overlap_length + length > overlap:
                        break

                    overlap_words.insert(0, previous_word)
                    overlap_length += length

                current_chunk = overlap_words
                current_length = overlap_length

            current_chunk.append(word)
            current_length += word_length

        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "source": source,
                "page": page_number
            })

    return chunks


if __name__ == "__main__":
    sample_pages = [
        {
            "text": (
                "The central library is located in Block A. "
                "The library is open from 8 AM to 8 PM. "
                "Students can borrow up to five books."
            ),
            "source": "library.pdf",
            "page": 1
        }
    ]

    result = create_chunks(sample_pages, chunk_size=100, overlap=20)

    print(f"Total chunks: {len(result)}")

    for index, chunk in enumerate(result, start=1):
        print(f"\n--- Chunk {index} ---")
        print(f"Source: {chunk['source']}")
        print(f"Page: {chunk['page']}")
        print(chunk["text"])

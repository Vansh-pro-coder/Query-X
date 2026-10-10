def create_chunks(text, chunk_size=500, overlap=50):
    words = text.split()

    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1

        if current_length + word_length > chunk_size:
            chunks.append(" ".join(current_chunk))

            overlap_words = []
            overlap_length = 0

            for previous_word in reversed(current_chunk):
                if overlap_length + len(previous_word) + 1 > overlap:
                    break

                overlap_words.insert(0, previous_word)
                overlap_length += len(previous_word) + 1

            current_chunk = overlap_words
            current_length = overlap_length

        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


if __name__ == "__main__":

    sample_text = """
    The central library is located in Block A.
    The library is open from 8 AM to 8 PM.
    Students can borrow up to five books.
    """

    chunks = create_chunks(
        sample_text,
        chunk_size=100,
        overlap=20
    )

    print(f"Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks):

        print(f"\n--- Chunk {i + 1} ---")
        print(chunk)
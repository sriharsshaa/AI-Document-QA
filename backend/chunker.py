import re


def split_text(text: str, chunk_size: int = 700, overlap: int = 100):
    # Clean excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split text into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        # If adding the sentence stays within the limit
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence

        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Start a new chunk
            current_chunk = sentence

    # Add the final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def create_page_chunks(pages, chunk_size=700, overlap=100):

    all_chunks = []

    for page in pages:

        page_chunks = split_text(
            page["text"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:

            all_chunks.append({
                "page": page["page"],
                "text": chunk
            })

    return all_chunks
import re


def split_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
):
    """
    Split text into chunks with character overlap.

    chunk_size:
        Maximum target size of each chunk.

    overlap:
        Number of characters from the previous chunk
        carried into the next chunk.
    """

    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split into sentences
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # Add sentence if it fits
        if (
            not current_chunk
            or len(current_chunk) + len(sentence) + 1
            <= chunk_size
        ):
            if current_chunk:
                current_chunk += " "

            current_chunk += sentence

        else:
            # Save current chunk
            chunks.append(
                current_chunk.strip()
            )

            # Create overlap from the end
            # of the previous chunk
            overlap_text = current_chunk[
                max(0, len(current_chunk) - overlap):
            ]

            # Avoid starting in the middle of a word
            if " " in overlap_text:
                overlap_text = overlap_text[
                    overlap_text.find(" ") + 1:
                ]

            current_chunk = (
                overlap_text.strip()
                + " "
                + sentence
            ).strip()

            # If the resulting chunk is still too large,
            # keep the sentence as the new chunk.
            if len(current_chunk) > chunk_size:
                current_chunk = sentence

    # Add final chunk
    if current_chunk.strip():
        chunks.append(
            current_chunk.strip()
        )

    return chunks


def create_page_chunks(
    pages,
    chunk_size=700,
    overlap=100
):
    """
    Create chunks while preserving page numbers.
    """

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
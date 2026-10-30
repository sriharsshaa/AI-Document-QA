import re


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""

    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    paragraphs = []

    for paragraph in text.split("\n"):
        paragraph = re.sub(r"[ \t]+", " ", paragraph).strip()

        if paragraph:
            paragraphs.append(paragraph)

    return "\n\n".join(paragraphs)


def split_long_sentence(sentence: str, chunk_size: int) -> list[str]:
    """
    Split a sentence that exceeds chunk_size into smaller pieces.
    Prefer word boundaries; split exceptionally long words if needed.
    """

    words = sentence.split()
    pieces = []
    current = ""

    for word in words:

        # Handle a single word longer than the chunk size.
        if len(word) > chunk_size:

            if current:
                pieces.append(current)
                current = ""

            for start in range(0, len(word), chunk_size):
                pieces.append(word[start:start + chunk_size])

            continue

        candidate = f"{current} {word}".strip()

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                pieces.append(current)

            current = word

    if current:
        pieces.append(current)

    return pieces


def get_overlap_text(text: str, overlap: int) -> str:
    """Get a word-boundary-safe suffix for the next chunk."""

    if overlap <= 0 or not text:
        return ""

    overlap_text = text[-overlap:]

    # Avoid starting in the middle of a word.
    first_space = overlap_text.find(" ")

    if first_space != -1:
        overlap_text = overlap_text[first_space + 1:]

    return overlap_text.strip()


def split_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
) -> list[str]:
    """
    Split text into chunks while preserving sentence boundaries
    where possible.

    Args:
        text: Input text.
        chunk_size: Maximum number of characters per chunk.
        overlap: Approximate number of overlapping characters.

    Returns:
        A list of text chunks.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    text = normalize_text(text)

    if not text:
        return []

    # Split into paragraphs first, then sentences.
    paragraphs = re.split(r"\n+", text)

    units = []

    for paragraph in paragraphs:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            paragraph.strip()
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            if len(sentence) > chunk_size:
                units.extend(
                    split_long_sentence(sentence, chunk_size)
                )
            else:
                units.append(sentence)

    chunks = []
    current_chunk = ""

    for unit in units:

        candidate = f"{current_chunk} {unit}".strip()

        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        # Save the current chunk.
        if current_chunk:
            chunks.append(current_chunk)

        # Carry a small suffix into the next chunk.
        overlap_text = get_overlap_text(
            current_chunk,
            overlap
        )

        # Ensure overlap + next unit never exceeds chunk_size.
        available_space = chunk_size - len(unit) - 1

        if available_space <= 0:
            current_chunk = unit
        else:
            overlap_text = overlap_text[:available_space].strip()
            current_chunk = f"{overlap_text} {unit}".strip()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def create_page_chunks(
    pages,
    chunk_size=700,
    overlap=100
):
    """
    Create chunks independently for each PDF page.

    Each chunk retains its original page number.
    Overlap is not carried across different pages.
    """

    all_chunks = []

    for page_number, page in enumerate(pages, start=1):

        page_text = page.get("text", "")

        page_label = page.get("page", page_number)

        page_chunks = split_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:

            all_chunks.append({
                "page": page_label,
                "text": chunk
            })

    return all_chunks
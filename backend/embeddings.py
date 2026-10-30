import logging
import numpy as np

from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE
)


logger = logging.getLogger(__name__)


# Load the model once when the module is imported.
model = SentenceTransformer(EMBEDDING_MODEL)


def create_embeddings(chunks):
    """
    Generate embeddings for a list of text chunks.

    Returns a NumPy array containing one embedding
    for each input text.
    """

    if not chunks:
        return np.empty((0, model.get_sentence_embedding_dimension()),
                        dtype=np.float32)

    if isinstance(chunks, str):
        chunks = [chunks]

    if not all(
        isinstance(chunk, str) and chunk.strip()
        for chunk in chunks
    ):
        raise ValueError(
            "All embedding inputs must be non-empty strings."
        )

    try:

        embeddings = model.encode(
            chunks,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=len(chunks) > EMBEDDING_BATCH_SIZE
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32
        )

        if embeddings.shape[0] != len(chunks):
            raise RuntimeError(
                "Embedding count does not match input count."
            )

        if not np.isfinite(embeddings).all():
            raise RuntimeError(
                "Generated embeddings contain invalid values."
            )

        logger.info(
            "Generated %s embeddings with dimension %s",
            len(embeddings),
            embeddings.shape[1]
        )

        return embeddings

    except Exception:

        logger.exception("Embedding generation failed.")

        raise
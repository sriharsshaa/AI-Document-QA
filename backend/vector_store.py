import faiss
import numpy as np


def validate_embeddings(embeddings, name="Embeddings"):
    """Validate and normalize the shape of an embedding array."""

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise ValueError(
            f"{name} must be a non-empty 2D array."
        )

    if embeddings.shape[1] == 0:
        raise ValueError(
            f"{name} dimensions cannot be zero."
        )

    if not np.isfinite(embeddings).all():
        raise ValueError(
            f"{name} contain invalid numeric values."
        )

    norms = np.linalg.norm(embeddings, axis=1)

    if np.any(norms == 0):
        raise ValueError(
            f"{name} contain zero-length vectors."
        )

    return embeddings.copy()


def create_vector_store(embeddings):
    """
    Create a FAISS index using cosine similarity.

    Normalized vectors are indexed using inner product.
    Inner product between normalized vectors equals cosine similarity.
    """

    embeddings = validate_embeddings(
        embeddings,
        name="Document embeddings"
    )

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


def search_vector_store(
    index,
    query_embedding,
    k=3
):
    """
    Search the FAISS index using cosine similarity.

    Returns:
        similarities: similarity scores.
        indices: matching document chunk indices.
    """

    if index is None or index.ntotal == 0:
        raise ValueError("The vector store is empty.")

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    query_embedding = validate_embeddings(
        query_embedding,
        name="Query embeddings"
    )

    if query_embedding.shape[1] != index.d:
        raise ValueError(
            "Query and document embedding dimensions do not match."
        )

    faiss.normalize_L2(query_embedding)

    k = min(k, index.ntotal)

    similarities, indices = index.search(
        query_embedding,
        k
    )

    return similarities, indices
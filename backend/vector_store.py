import faiss
import numpy as np


def create_vector_store(embeddings):
    """
    Create a FAISS vector store using cosine similarity.

    Cosine similarity works well for semantic text retrieval.
    """

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    # Normalize embeddings so that
    # inner product becomes cosine similarity.
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
    Search the vector store using cosine similarity.

    Returns:
        similarities
        indices
    """

    query_embedding = np.array(
        query_embedding,
        dtype="float32"
    )

    # Normalize query embedding
    faiss.normalize_L2(query_embedding)

    similarities, indices = index.search(
        query_embedding,
        k
    )

    return similarities, indices
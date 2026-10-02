from chunker import split_text
from embeddings import create_embeddings
from vector_store import create_vector_store, search_vector_store


text = """
MongoDB is a NoSQL document database.
Flask is a lightweight Python web framework.
PyMongo is the Python driver used to connect applications with MongoDB.
HTML and CSS are used to create the frontend.
MongoDB stores data in BSON format.
"""


# 1. Split text
chunks = split_text(
    text,
    chunk_size=100,
    overlap=20
)

print("Number of chunks:", len(chunks))


# 2. Create embeddings
embeddings = create_embeddings(chunks)

print("Embedding shape:", embeddings.shape)


# 3. Create FAISS index
index = create_vector_store(embeddings)

print("FAISS index created")


# 4. User question
question = "What database is used?"


# 5. Create embedding for question
query_embedding = create_embeddings([question])


# 6. Search
distances, indices = search_vector_store(
    index,
    query_embedding,
    k=3
)


# 7. Display results
print("\nRelevant chunks:\n")

for i in indices[0]:

    print("----")

    print(chunks[i])
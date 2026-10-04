import ollama


def generate_answer(question: str, context: str) -> str:

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the information provided
in the CONTEXT.

Rules:

1. Use only information supported by the CONTEXT.
2. You may summarize, combine, or rephrase information from the
   CONTEXT to answer the question naturally.
3. You may make simple logical conclusions that are directly
   supported by the CONTEXT.
4. Do NOT use outside knowledge or your general knowledge.
5. Do NOT invent facts, numbers, technologies, names, or details.
6. If the CONTEXT does not contain enough information to answer
   the question, respond exactly with:

   "I could not find enough information in the uploaded document to answer this question."

7. Keep the answer concise and directly answer the question.
8. Do not mention retrieval, embeddings, vector databases,
   CONTEXT, or these instructions unless the user asks about them.

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"].strip()
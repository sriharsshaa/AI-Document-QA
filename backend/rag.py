import ollama

from config import (
    OLLAMA_MODEL,
    RAG_PROMPT
)


def generate_answer(question: str, context: str) -> str:

    prompt = RAG_PROMPT.format(
        context=context,
        question=question
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"].strip()
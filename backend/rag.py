import logging
import time

import ollama

from config import (
    OLLAMA_MODEL,
    OLLAMA_OPTIONS,
    OLLAMA_KEEP_ALIVE,
    RAG_PROMPT
)


logger = logging.getLogger(__name__)


# --------------------------------------------------
# BUILD PROMPT
# --------------------------------------------------

def build_prompt(question: str, context: str) -> str:
    """
    Build a generic, document-grounded RAG prompt.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not context or not context.strip():
        raise ValueError("Retrieved context cannot be empty.")

    return RAG_PROMPT.format(
        question=question.strip(),
        context=context.strip()
    )


# --------------------------------------------------
# GENERATE ANSWER
# --------------------------------------------------

def generate_answer(question: str, context: str) -> str:
    """
    Generate an answer using retrieved document context
    and the configured Ollama model.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not context or not context.strip():
        return (
            "I couldn't find enough relevant information "
            "in the retrieved document passages."
        )

    try:

        prompt = build_prompt(
            question=question,
            context=context
        )

        logger.info(
            "Generating answer using model: %s",
            OLLAMA_MODEL
        )

        start_time = time.perf_counter()

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options=OLLAMA_OPTIONS,
            keep_alive=OLLAMA_KEEP_ALIVE
        )

        answer = (
            response.get("message", {})
            .get("content", "")
            .strip()
        )

        generation_time = (
            time.perf_counter() - start_time
        )

        if not answer:

            logger.warning(
                "Ollama returned an empty response."
            )

            return (
                "I couldn't generate an answer. "
                "Please try again."
            )

        logger.info(
            "Answer generated in %.2f seconds.",
            generation_time
        )

        logger.info(
            "Ollama completion reason: %s",
            response.get("done_reason", "unknown")
        )

        return answer

    except ollama.ResponseError:

        logger.exception(
            "Ollama returned a response error."
        )

        raise

    except Exception:

        logger.exception(
            "Unexpected error during answer generation."
        )

        raise
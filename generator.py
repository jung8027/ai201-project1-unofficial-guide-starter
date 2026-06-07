from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL, RELEVANCE_THRESHOLD

_client = Groq(api_key=GROQ_API_KEY)

_FALLBACK = (
    "I don't have enough information in the loaded reviews to answer that question. "
    "Try asking about a specific professor or a topic covered in the Rate My Professors reviews."
)

_SYSTEM_PROMPT = """\
You are NYU Business Guide, an assistant that helps students learn about Business professors \
at New York University based solely on student reviews from Rate My Professors.

You will be given one or more review excerpts, each labeled with the professor they came from. \
Answer the user's question using ONLY the information in those excerpts. Follow these rules strictly:

1. Ground every claim in the provided excerpts. Do not draw on any general knowledge about \
professors, NYU, or teaching styles. If the excerpts do not contain the answer, say: \
"I don't have enough information in the loaded reviews to answer that." Do not guess or fill gaps.

2. Always cite your source at the end of your answer in this format:
   Sources: [Professor Name (Rate My Professors), ...]
   If the answer draws from multiple professors, list all of them.

3. Be direct and specific — quote or closely paraphrase what reviewers actually said. \
A confident wrong answer is worse than an honest "I don't know."\
"""


def _format_context(chunks):
    """Render retrieved chunks into a labeled context block for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[Excerpt {i} — {c['source']}]\n{c['text']}")
    return "\n\n".join(blocks)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved review chunks.

    Drops any chunk whose cosine distance exceeds RELEVANCE_THRESHOLD before
    sending to the LLM — this is the structural grounding mechanism, not just
    a prompt instruction. Returns _FALLBACK if nothing passes the threshold.
    """
    if not retrieved_chunks:
        return _FALLBACK

    relevant = [c for c in retrieved_chunks if c["distance"] <= RELEVANCE_THRESHOLD]
    if not relevant:
        return _FALLBACK

    context = _format_context(relevant)
    user_message = (
        f"Review excerpts:\n\n{context}\n\n"
        f"---\n"
        f"Question: {query}\n\n"
        f"Answer using only the excerpts above. End your response with a Sources line."
    )

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()

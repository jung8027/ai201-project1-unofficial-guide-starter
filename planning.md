# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Student reviews of Business professors at New York University (NYU Stern School of Business), sourced from Rate My Professors.

This knowledge is valuable because official course catalog descriptions say nothing about a professor's grading fairness, exam style, workload, or how much attendance matters. Students rely on peer reviews to choose between professors teaching the same course, but Rate My Professors pages are not searchable by topic — you can only browse one professor at a time. A RAG system makes this knowledge queryable across all professors at once: "which professor curves grades?" or "who gives the most useful feedback?" can't be answered from the official NYU website.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors | Alison Taylor reviews | documents/Alison Taylor at New York University _ Rate My Professors.pdf |
| 2 | Rate My Professors | Eugene Kolker reviews | documents/Eugene Kolker at New York University _ Rate My Professors.pdf |
| 3 | Rate My Professors | Giulia Brancaccio reviews | documents/Giulia Brancaccio at New York University _ Rate My Professors.pdf |
| 4 | Rate My Professors | Jason Turetsky reviews | documents/Jason Turetsky at New York University _ Rate My Professors.pdf |
| 5 | Rate My Professors | Jeffrey Meli reviews | documents/Jeffrey Meli at New York University _ Rate My Professors.pdf |
| 6 | Rate My Professors | Raymond Ro reviews | documents/Raymond Ro at New York University _ Rate My Professors.pdf |
| 7 | Rate My Professors | Richard Hendler reviews | documents/Richard Hendler at New York University _ Rate My Professors.pdf |
| 8 | Rate My Professors | Sinja Leonelli reviews | documents/Sinja Leonelli at New York University _ Rate My Professors.pdf |
| 9 | Rate My Professors | Stephen Master reviews | documents/Stephen Master at New York University _ Rate My Professors.pdf |
| 10 | Rate My Professors | Vivian Giang reviews | documents/Vivian Giang at New York University _ Rate My Professors.pdf |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 50 characters

**Reasoning:**

RMP reviews are short opinion texts — each review is roughly 100–350 characters. A 500-character chunk captures 1–2 complete reviews, which means each chunk contains at least one full opinion with enough context to be meaningful on its own. This avoids the "bad chunk (too small)" failure mode where a chunk contains only half a sentence.

50-character overlap ensures that reviews landing near a chunk boundary appear complete in at least one chunk — without overlap, a review that starts at character 480 of a chunk would be split, and neither half would be fully retrievable.

A chunk size smaller than 200 would produce fragments (e.g., just the course code and rating numbers with no review text). A chunk size larger than 800 would merge unrelated reviews from multiple students, diluting the semantic signal and making it harder for the embedding to match a specific query.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:**

For a production system I would consider:
- **Context length:** `all-MiniLM-L6-v2` has a 256-token limit. Review chunks are short, so this is fine here, but longer documents would need a model like `all-mpnet-base-v2` (384 tokens) or OpenAI's `text-embedding-3-small` (8192 tokens).
- **Domain accuracy:** General-purpose sentence embeddings may not capture discipline-specific vocabulary (e.g., "curves," "cold calls," "Brightspace"). A fine-tuned embedding model on education or review text would improve precision.
- **Multilingual support:** Not needed here (all reviews are in English), but international student communities might write in mixed languages — a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be necessary in that case.
- **Latency vs. accuracy:** `all-MiniLM-L6-v2` is fast (runs locally in ~10ms per query) and free. For higher accuracy at the cost of speed and API dependency, OpenAI or Cohere embedding APIs produce better representations.
- **Local vs. API-hosted:** Local models have no rate limits or costs and keep data private, which matters if reviews contain personally identifying course information.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Jeffrey Meli's grading? | Tough grader; not curved except possibly for effort; 40% final exam; one review reports no calculator allowed on exam despite division problems |
| 2 | Is attendance mandatory for any Business professor's courses? | Yes — Jeffrey Meli has mandatory attendance noted in at least two reviews |
| 3 | Which professor has the highest overall quality rating according to reviews? | Should identify the professor with the highest average star rating from the retrieved review pages |
| 4 | What complaints do students have about course organization at NYU Stern? | Meli reviews mention syllabus not following rubric, Brightspace showing old content, and last-minute exam notification |
| 5 | What do students say about a professor's knowledge of the subject matter? | At least one review per professor should mention expertise; expected: mixed responses — some praised as knowledgeable, some criticized for poor delivery despite knowing content |

---

## Anticipated Challenges

1. **Noisy PDF extraction:** Rate My Professors pages are JavaScript-rendered websites saved as PDFs. The extracted text will contain navigation artifacts (timestamps, URLs, "Log In Sign Up Help" fragments, site footers). If cleaning is incomplete, these fragments will end up in chunks and confuse the embedding model — a query about "attendance policy" might retrieve a chunk that contains only the word "Attendance:" followed by nav text.

2. **Sparse per-professor coverage:** Some professors have only 2–3 reviews. If a user asks a specific question about such a professor, the system may retrieve the same chunk multiple times (top-5 results all from the same document) or return off-topic results from other professors because there simply isn't enough signal in the small document to match the query precisely.

---

## Architecture

```
┌─────────────────────┐
│  documents/*.pdf    │  10 Rate My Professors PDFs
└────────┬────────────┘
         │ pdfplumber
         ▼
┌─────────────────────┐
│     ingest.py       │  clean nav text, split into 500-char / 50-overlap chunks
└────────┬────────────┘
         │ list of chunk dicts (text, professor, source, chunk_id)
         ▼
┌─────────────────────┐
│    retriever.py     │  embed via all-MiniLM-L6-v2 (sentence-transformers)
│    ChromaDB         │  store with professor + source metadata
└────────┬────────────┘
         │ on query: cosine similarity search, return top-5 chunks + distances
         ▼
┌─────────────────────┐
│    generator.py     │  filter chunks with distance > 0.75, format context,
│    Groq LLaMA 3.3   │  call LLM with grounding system prompt
└────────┬────────────┘
         │ grounded answer string with Sources line
         ▼
┌─────────────────────┐
│      app.py         │  Gradio web UI — question textbox, answer box, sources box
└─────────────────────┘
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**

I will give Claude the Documents section (10 Rate My Professors PDFs), the Chunking Strategy section (500 chars / 50 overlap), and the Architecture diagram. I will ask it to implement `ingest.py` with `load_documents()` using `pdfplumber` and `chunk_document()` using my specified parameters. I will verify the output by printing 5 representative chunks and checking that each contains complete review text, a professor name reference, and no nav artifacts.

**Milestone 4 — Embedding and retrieval:**

I will give Claude the Retrieval Approach section and the Architecture diagram and ask it to implement `retriever.py` with `embed_and_store()` and `retrieve()`. I will verify by running 3 of my evaluation questions and checking that the top-5 returned chunks visibly relate to each question and have distance scores below 0.5.

**Milestone 5 — Generation and interface:**

I will give Claude the grounding requirement (answer only from retrieved chunks, cite source in every response), the desired output format (answer + "Sources:" line), and the Gradio skeleton from the project instructions. I will verify by asking one in-scope question (should cite a professor) and one out-of-scope question (should return the fallback message). I will check that the system prompt enforces grounding rather than just suggesting it.

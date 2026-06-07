# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Student reviews of Business professors at New York University (NYU Stern School of Business), collected from Rate My Professors.

This knowledge is valuable because official NYU course listings describe topics and prerequisites but say nothing about how a professor actually teaches, grades, or runs exams. Students choosing between two sections of the same course — or deciding whether an elective is worth taking — rely entirely on peer reviews. Rate My Professors surfaces this knowledge, but only one professor at a time: there is no way to ask cross-cutting questions like "which Stern professor curves their grades?" or "whose exams are the hardest?" A RAG system makes the entire corpus queryable in plain language.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | ratemyprofessor.com | PDF | documents/Alison Taylor at New York University _ Rate My Professors.pdf |
| 2 | ratemyprofessor.com | PDF | documents/Eugene Kolker at New York University _ Rate My Professors.pdf |
| 3 | ratemyprofessor.com | PDF | documents/Giulia Brancaccio at New York University _ Rate My Professors.pdf |
| 4 | ratemyprofessor.com | PDF | documents/Jason Turetsky at New York University _ Rate My Professors.pdf |
| 5 | ratemyprofessor.com | PDF | documents/Jeffrey Meli at New York University _ Rate My Professors.pdf |
| 6 | ratemyprofessor.com | PDF | documents/Raymond Ro at New York University _ Rate My Professors.pdf |
| 7 | ratemyprofessor.com | PDF | documents/Richard Hendler at New York University _ Rate My Professors.pdf |
| 8 | ratemyprofessor.com | PDF | documents/Sinja Leonelli at New York University _ Rate My Professors.pdf |
| 9 | ratemyprofessor.com | PDF | documents/Stephen Master at New York University _ Rate My Professors.pdf |
| 10 | ratemyprofessor.com | PDF | documents/Vivian Giang at New York University _ Rate My Professors.pdf |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**

Rate My Professors reviews are short opinion texts — each individual review is roughly 100–350 characters. A 500-character chunk captures 1–2 complete reviews, so each chunk is a self-contained opinion that can stand alone without the surrounding page for context. This avoids the "fragment" failure mode where a chunk ends mid-sentence and neither half is retrievable on its own.

The 50-character overlap handles reviews that land near a chunk boundary: a review starting at character 470 of one chunk will appear complete in the next chunk's opening 80 characters, ensuring no opinion is silently cut off.

A chunk smaller than 200 characters would produce fragments — just a course code, a numeric rating, and no review text. A chunk larger than 800 would merge unrelated reviews from multiple students, diluting the semantic signal and making it harder to match a specific query about one topic (e.g., exams vs. attendance vs. grading).

The PDFs also contain navigation boilerplate (timestamps, URLs, footer links, sidebar elements) that was stripped before chunking using `ingest.py`'s `_clean_text()` function — see `ingest.py` for the full cleaning rules.

**Final chunk count:** 169 chunks across 10 professors (range: 3–46 per professor; professors with fewer reviews, like Alison Taylor and Jeffrey Meli, have 3–4 chunks each)

---

## Sample Chunks

**Chunk 1 — Richard Hendler (Rate My Professors)** (`richard_hendler_30`)
```
ntastic prof and
storyteller. A lot of work but
definitely worth it. I learned about
law and myself working with my
group. The LawGame was definitely
the best experience at NYU. Rich is
so enthusiastic about what he
teaches and always willing to help.
Rich, the course, and my new
friends are awesome.
GROUP PROJECTS
INSPIRATIONAL
LOTS OF HOMEWORK
```

**Chunk 2 — Eugene Kolker (Rate My Professors)** (`eugene_kolker_13`)
```
TOUGH GRADER
LOTS OF HOMEWORK
HILARIOUS
QUALITY
BMIN4527 May 14th, 2024
1.0
For Credit: Yes
Attendance: Mandatory
DIFFICULTY
Grade: C Textbook: N/A
1.0
Oh my god! I am out of words to
explain what an awful professor he
is. Just after 2 classes I realized I
made a bad mistake and regretted it
throughout my course. It was a
waste of credits and time. Don't rely
on other ratings as he tells students
to rate him good in order to get A
grade. Would advise to stay away
from his courses!
```

**Chunk 3 — Jason Turetsky (Rate My Professors)** (`jason_turetsky_0`)
```
QUALITY
STATUB103 Jun 4th, 2026
4.0
For Credit: Yes
Attendance: Not Mandatory
DIFFICULTY
Would Take Again: Yes Grade: B+
4.0
Textbook: Yes
hes funny and cool but exams are def
harder than hw. def understand the
material and dont memorize formulas
because u gon get cheat sheets anyway.
QUALITY
STATUB103 Apr 30th, 2026
4.0
For Credit: Yes
Attendance: Not Mandatory
DIFFICULTY
Would Take Again: Yes
3.0
Grade: Rather not say Textbook: N/A
```

**Chunk 4 — Sinja Leonelli (Rate My Professors)** (`sinja_leonelli_8`)
```
Would Take Again: Yes
4.0
Grade: Not sure yet
Textbook: N/A
I was a little hesitant to take this
course because of past reviews, but
it was not at all as bad as I
expected. It is a lot of material, and
participation does matter, but she is
almost always available outside of
class for questions. Lowest quiz and
midterm are dropped, and as long
as you show you're trying, she's
super accommodating!
PARTICIPATION MATTERS
ACCESSIBLE OUTSIDE CLASS
```

**Chunk 5 — Vivian Giang (Rate My Professors)** (`vivian_giang_1`)
```
GIVES GOOD FEEDBACK
INSPIRATIONAL
ACCESSIBLE OUTSIDE CLASS
QUALITY
SOIMUB125 May 6th, 2026
5.0
For Credit: Yes
Attendance: Mandatory
DIFFICULTY
Would Take Again: Yes
3.0
Grade: Not sure yet
Textbook: N/A
one of the most underrated B&S
professors. She's very caring and
isn't as hard as a grader compared
to most professors. Even though her
class is very late (T/Th 6:30-7:45),
it's because of her job at the NYT.
Her class is very doable, even if you
aren't the best writer.
```

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key required)

**Production tradeoff reflection:**

For a real deployment serving hundreds of students, several tradeoffs would matter:

- **Context length:** `all-MiniLM-L6-v2` truncates at 256 tokens. Review chunks are short (≤500 chars ≈ 100 tokens), so truncation is not a problem here. For longer documents (e.g., full course syllabi), a model with a larger window like `all-mpnet-base-v2` (384 tokens) or OpenAI's `text-embedding-3-small` (8192 tokens) would be necessary to avoid silently cutting off content.
- **Domain accuracy:** General-purpose embeddings may not represent education-specific vocabulary well — words like "curves," "Brightspace," "cold calls," and "PM" (program manager in an MBA context) might not cluster semantically the way a student would expect. A model fine-tuned on review or academic text would improve retrieval precision.
- **Multilingual support:** All 10 documents here are in English. A diverse international student community might write reviews in mixed languages; `paraphrase-multilingual-MiniLM-L12-v2` would handle that without a separate translation step.
- **Latency:** The local model runs in ~10ms per query on CPU, which is acceptable for a demo. For a production web app with concurrent users, an API-hosted model (Cohere, OpenAI) would scale horizontally without requiring a GPU server, at the cost of per-query charges and data leaving the system.

---

## Retrieval Test Results

**Query 1: "What do students say about Richard Hendler as a professor?"**

Top returned chunks:

| Rank | Professor | Distance | Chunk excerpt |
|------|-----------|----------|---------------|
| 1 | Richard Hendler | 0.388 | "I appreciate that, especially in Stern courses. However, he has no slides, class notes, etc. and tells stories rather than actually lecture. There is a significant amount of coursework…" |
| 2 | Richard Hendler | 0.410 | "…his 'bits' and understand the meaning of why he does it, you'll do well in his class. If you ask for help in your life, he'll buy you dinner to talk about it. 10/10 would geek in his class again." |
| 3 | Eugene Kolker | 0.416 | "One of the best professor I have ever met at NYU!!! AMAZING LECTURES CARING RESPECTED" |

**Why chunks 1 and 2 are relevant:** Both come directly from Richard Hendler's review page and describe his teaching style (storytelling, no slides) and workload. The low distances (0.388, 0.410) confirm a strong semantic match — the query names Hendler explicitly, and both chunks reference his course structure and personality. The third chunk from Eugene Kolker (0.416) shares "amazing professor at NYU" phrasing with the query intent and ranks just above the Hendler chunks, but doesn't contain Hendler-specific information.

---

**Query 2: "How difficult is it to get a good grade in Raymond Ro classes?"**

Top returned chunks:

| Rank | Professor | Distance | Chunk excerpt |
|------|-----------|----------|---------------|
| 1 | Raymond Ro | 0.325 | "He wouldn't tell you how well you did in the midterm. No mean or grade distribution! GET READY TO READ GRADED BY FEW THINGS GROUP PROJECTS" |
| 2 | Raymond Ro | 0.339 | "The best professor…very caring for students…Attendance: Mandatory…Grade: A…2.0 difficulty" |
| 3 | Jason Turetsky | 0.355 | "…take notes in class, and you won't have to struggle. PARTICIPATION MATTERS LOTS OF HOMEWORK LECTURE HEAVY" |

**Why chunks 1 and 2 are relevant:** Both are from Raymond Ro's page and directly address grading: the first mentions midterm opacity ("no grade distribution"), and the second shows actual grade outcomes (A with low difficulty). The query asks about grade difficulty for Ro specifically, and the embedding correctly surfaces Ro's chunks first. The third chunk from Turetsky (0.355) is borderline — it matches semantically on "study effort → grades" but is from a different professor and is off-target for this query.

---

**Query 3: "Is attendance mandatory for any Business professor courses?"**

Top returned chunks:

| Rank | Professor | Distance | Chunk excerpt |
|------|-----------|----------|---------------|
| 1 | Raymond Ro | 0.394 | "Attendance: Mandatory…Would Take Again: Yes Grade: A…Great professor and great guy. Made classes engaging…" |
| 2 | Jason Turetsky | 0.439 | "Attendance is not mandatory, but highly recommend watching the lecture recordings to do well." |
| 3 | Alison Taylor | 0.442 | "Attendance: Mandatory…Would Take Again: Yes Grade: A…Professor Taylor…" |

All three chunks are relevant: the RMP review format embeds the "Attendance: Mandatory / Not Mandatory" field directly in each review, and the query targets exactly that field. The embedding model finds these chunks because "attendance mandatory" appears verbatim in the review metadata. This is one of the strongest retrieval results in the system — multiple professors are represented and both mandatory and non-mandatory cases appear in the top results.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt in `generator.py` instructs the model:

> "Answer the user's question using ONLY the information in those excerpts. Ground every claim in the provided excerpts. Do not draw on any general knowledge about professors, NYU, or teaching styles. If the excerpts do not contain the answer, say: 'I don't have enough information in the loaded reviews to answer that.' Do not guess or fill gaps."

The grounding is enforced structurally, not just via instruction: `generate_response()` in `generator.py` filters out any chunk with a cosine distance above `RELEVANCE_THRESHOLD = 0.75` *before* sending context to the LLM. If no chunk passes the threshold, the function returns a hardcoded fallback string without ever calling the LLM at all — so the model cannot hallucinate on out-of-scope queries.

**How source attribution is surfaced in the response:**

The user message sent to the LLM explicitly instructs: "End your response with a Sources line." The system prompt specifies the format: `Sources: [Professor Name (Rate My Professors), ...]`. Additionally, `app.py` appends the retrieved chunk sources and cosine distances in the "Retrieved from" panel of the Gradio UI, so attribution is visible even if the LLM response omits it.

---

## Example Responses

**Example 1 — Grounded response with source attribution:**

> **Query:** What do students say about Richard Hendler as a professor?
>
> **Response:** Students describe Richard Hendler as "AMAZING" and a "fantastic prof and storyteller." They appreciate that he is "respectful," "hilarious," and "inspirational." One student notes that he "encourages participation" and is "very helpful and reachable." However, students also mention that his classes are "demanding" and require a significant amount of work, including "LOTS OF HOMEWORK" and "GROUP PROJECTS." Despite the workload, students would "definitely take his class again" and consider him "one of the best professors" they have had.
>
> Sources: Richard Hendler (Rate My Professors)

---

**Example 2 — Grounded response with source attribution:**

> **Query:** How difficult is it to get a good grade in Raymond Ro classes?
>
> **Response:** According to the excerpts, getting a good grade in Raymond Ro's classes seems manageable. One reviewer stated that "if you do the readings" for his exams, which are "heavy on memorisation", you will do well. Another reviewer mentioned that "as long as you do the readings you will get an A" and that "the class itself isn't hard." Additionally, a reviewer noted that Raymond Ro has "super low expectations" which might contribute to the perceived ease of getting a good grade. However, it's also mentioned that "exams aren't easy" but understanding general concepts and readings can help.
>
> Sources: Raymond Ro (Rate My Professors)

---

**Example 3 — Out-of-scope query showing refusal:**

> **Query:** What are the best pizza places near NYU campus?
>
> **Response:** I don't have enough information in the loaded reviews to answer that.
>
> Sources: None

The system retrieved chunks (distances: 0.569, 0.609, 0.610) that were topically distant but still below the 0.75 threshold, so they were passed to the LLM as context. The LLM correctly examined those review excerpts, found nothing about pizza, and declined to answer rather than drawing on its training knowledge. This demonstrates that the grounding instruction works even when the distance filter does not fully block the LLM call.

---

## Query Interface

The interface is a Gradio web app launched with `python app.py` (opens at `http://localhost:7860`).

**Input fields:**
- **Your question** — a free-text box where the user types any question about NYU Business professors. Submits on Enter or by clicking "Ask."

**Output fields:**
- **Answer** — the LLM-generated response grounded in retrieved reviews, always ending with a `Sources:` line naming the professor(s) the answer draws from.
- **Retrieved from** — the list of source documents whose chunks passed the relevance threshold (distance ≤ 0.75), with cosine distance scores.

The sidebar lists all 10 loaded professors. Eight example questions are provided as clickable shortcuts.

**Sample interaction transcript:**

> **Input:** How difficult is it to get a good grade in Raymond Ro classes?
>
> **Answer:** According to the excerpts, getting a good grade in Raymond Ro's classes seems manageable. One reviewer stated that "if you do the readings" for his exams, which are "heavy on memorisation," you will do well. Another reviewer mentioned that "as long as you do the readings you will get an A" and that "the class itself isn't hard." Additionally, a reviewer noted that Raymond Ro has "super low expectations." However, it's also mentioned that "exams aren't easy" but understanding general concepts and readings can help.
>
> Sources: Raymond Ro (Rate My Professors)
>
> **Retrieved from:**
> • Raymond Ro (Rate My Professors) (distance: 0.325)
> • Raymond Ro (Rate My Professors) (distance: 0.339)
> • Jason Turetsky (Rate My Professors) (distance: 0.355)
> • Raymond Ro (Rate My Professors) (distance: 0.378)
> • Raymond Ro (Rate My Professors) (distance: 0.382)

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Jeffrey Meli's grading? | Tough grader; not curved; 40% final exam; no calculator allowed on exam | "I don't have enough information in the loaded reviews to answer that." | Off-target — top chunks were from Kolker, Turetsky, Ro (dist 0.432–0.449); Meli's own chunks never appeared | Inaccurate — correct refusal behavior but the right information exists in the corpus and was not retrieved |
| 2 | Is attendance mandatory for any Business professor courses? | Yes — Meli, Ro, Kolker, Leonelli all have mandatory attendance noted in reviews | Accurate: Raymond Ro (mandatory), Alison Taylor (mandatory), Jason Turetsky (not mandatory) cited with specific review text | Relevant — all top chunks contained "Attendance: Mandatory/Not Mandatory" fields from correct professors | Partially accurate — correctly identified mandatory cases but only surfaced 3 of 10 professors |
| 3 | Which professor has the highest overall quality rating according to reviews? | Richard Hendler (4.6/5 based on 145 ratings) | Confused comparison mixing Giulia Brancaccio, Sinja Leonelli, and Vivian Giang; did not identify Hendler | Partially relevant — retrieved stats-header chunks for Sinja and Giulia that contain rating distribution data, but missed Hendler's | Partially accurate — identified some high-rated professors but gave a muddled answer and missed the correct answer |
| 4 | What complaints do students have about course organization at NYU Stern? | Jeffrey Meli: syllabus doesn't follow rubric, Brightspace shows old content, last-minute exam notice; Kolker: reads Google News, dodges questions | Only covered Kolker's disorganization (reads Google News, dodges questions); missed all Meli complaints | Partially relevant — retrieved Kolker chunks correctly; Meli's complaint chunks were not in the top results | Partially accurate — half the expected answer was present; the Meli side was missed entirely |
| 5 | What do students say about a professor's knowledge of the subject matter? | Mixed responses: Kolker and Hendler praised as knowledgeable; Kolker also criticized for not knowing GenAI content | Returned only Stephen Master ("knows a lot about sports marketing"); ignored Hendler and Kolker references | Partially relevant — retrieved Stephen Master and Richard Hendler chunks but top results didn't surface Kolker's knowledge criticism | Partially accurate — the answer was true but narrow; missed the richer cross-professor comparison the question invited |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "What do students say about Jeffrey Meli's grading?"

**What the system returned:** "I don't have enough information in the loaded reviews to answer that. Sources: None"

**Root cause (tied to a specific pipeline stage):** The failure occurs at the **retrieval stage**. Jeffrey Meli has only 4 chunks total (his Rate My Professors page has just 2 student reviews). When the query "Jeffrey Meli grading" is embedded and compared against all 169 chunks in ChromaDB, the top-5 results by cosine similarity are from Eugene Kolker (distance 0.432), Jason Turetsky (distance 0.435), and Raymond Ro (distance 0.449) — all professors with many reviews that include grading-related language. Jeffrey Meli's own 4 chunks do not appear in the top-5 because their dense review language about "grading" is semantically similar to these other professors' chunks, and there are simply more of those competing embeddings in the vector space. The LLM was passed the wrong professor's chunks and — correctly following its grounding instruction — refused to fabricate an answer about Meli from unrelated context.

**What you would change to fix it:** Two complementary fixes. First, add a metadata filter to ChromaDB's query: when the user's question names a specific professor, restrict retrieval to only that professor's chunks using `where={"professor": "Jeffrey Meli"}`. This is a structural fix that doesn't depend on embedding quality. Second, adding more documents for sparse professors (e.g., collecting reviews from additional platforms or semesters) would raise the chunk count enough for similarity search to work reliably.

---

## Spec Reflection

**One way the spec helped you during implementation:**

Having the 5 evaluation questions written before writing any pipeline code directly shaped the chunking decision. When I was deciding between 300-character and 500-character chunks, I mentally tested "would a 300-character chunk capture enough context to answer 'What complaints do students have about course organization?'" — and the answer was no, because most organization complaints span 2–4 sentences. The evaluation plan forced me to think about retrieval from the user's perspective before I touched any code, which is exactly the kind of constraint a spec is supposed to impose.

**One way your implementation diverged from the spec, and why:**

The spec assumed I could cleanly strip all navigation artifacts from the PDFs in a single cleaning pass. In practice, pdfplumber's text extraction interleaves the Rate My Professors sidebar elements (professor name, "Rate," "Compare," "New York University") directly into review text because the page uses a two-column layout that pdfplumber doesn't reconstruct correctly. The cleaning function required five separate passes — line-by-line filters, inline regex substitutions, professor-name prefix stripping on review fields, mid-sentence name detection, and post-assembly multi-line artifact removal — and still leaves minor fragments like "inRate" in a handful of chunks. The spec said "remove navigation text," but the mechanism to do so was significantly more involved than anticipated.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Document Sources section (10 Rate My Professors PDFs), the Chunking Strategy section (500 chars / 50 overlap, min 80 chars), the Architecture diagram, and a sample of the raw extracted PDF text showing what navigation artifacts looked like after pdfplumber extraction.
- *What it produced:* `ingest.py` with `load_documents()` using `pdfplumber` and `chunk_document()` using the specified parameters, plus a `_clean_text()` function that stripped timestamp headers, URLs, "Log In Sign Up Help" fragments, and the site footer.
- *What I changed or overrode:* The initial `_clean_text()` only caught standalone noise words and simple regex patterns. Testing revealed that pdfplumber's multi-column layout produced professor-name artifacts interleaved mid-sentence (e.g., "Jason Turetsky reach. a lot of circles") and stats-header blocks were not being stripped. I rewrote the cleaning to add: professor-name prefix stripping on review-field lines, mid-sentence name detection (strip name prefix when followed by a lowercase letter), post-assembly multi-line artifact patterns, and a header-stripping step that finds the first course code and discards the preceding stats block. I ran the pipeline repeatedly and inspected chunk output after each change.

**Instance 2**

- *What I gave the AI:* The grounding requirement (answer only from retrieved chunks, cite source in every response), the desired output format (answer + "Sources:" line), and the architecture showing the distance-threshold filter before the LLM call.
- *What it produced:* `generator.py` with a system prompt instructing the model to answer from excerpts only, and a `generate_response()` function that filtered chunks by `RELEVANCE_THRESHOLD`, formatted context, and called the Groq API at `temperature=0.2`.
- *What I changed or overrode:* The initial system prompt used "try to answer only from the excerpts" — a suggestion rather than a constraint. I rewrote it to use "ONLY the information in those excerpts" and added the explicit fallback condition: "If the excerpts do not contain the answer, say 'I don't have enough information in the loaded reviews to answer that.'" I also verified that the out-of-scope query ("What are the best pizza places near NYU campus?") returned the fallback message rather than a hallucinated response, confirming the grounding held under an adversarial test.

import os
import re
import pdfplumber

from config import DOCS_PATH


def _professor_name_from_filename(filename):
    """Extract 'Firstname Lastname' from 'Firstname Lastname at New York University _ Rate My Professors.pdf'."""
    name = filename.replace(" at New York University _ Rate My Professors.pdf", "")
    return name.strip()


def _clean_text(raw_text, professor_name):
    """
    Remove Rate My Professors navigation/boilerplate from extracted PDF text.

    Strips:
    - Timestamp header lines  (e.g. "6/7/26, 5:49 PM … Rate My Professors")
    - URL lines               (any line that is just a URL)
    - Site footer block       (everything from legal/footer lines onward)
    - Standalone layout noise words ("Rate", "Compare", "New York University", etc.)
    - Inline nav fragments interleaved by the two-column PDF layout
    - Professor-name artifacts prepended to review fields (e.g. "Jeffrey Meli Attendance:")
    - "Helpful X Y" vote-button lines
    - The per-page stats header block (everything before the first review)
    """
    lines = raw_text.splitlines()
    cleaned = []
    footer_started = False

    footer_triggers = {
        "site guidelines", "terms & conditions", "privacy policy",
        "copyright compliance policy", "ca notice at collection",
        "do not sell my personal information",
        "© 2026 rate my professors",
    }

    standalone_noise = {
        "rate", "business", "compare", "new york university",
        "log in sign up help", "help", "log in", "sign up",
        "rate compare", "similar professors",
    }

    # Review metadata field labels — used to detect lines that need name-prefix stripping
    review_field_re = re.compile(
        r"For Credit:|Attendance:|Would Take Again:|Grade:|Textbook:|QUALITY|DIFFICULTY|Online Class:",
        re.IGNORECASE,
    )

    name_re = re.compile(rf"{re.escape(professor_name)}\s*", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if not stripped:
            continue

        # Footer — discard everything once legal text appears
        if any(t in low for t in footer_triggers):
            footer_started = True
        if footer_started:
            continue

        # Timestamp header lines: "6/7/26, 5:49 PM …"
        if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}", stripped):
            continue

        # URL lines
        if re.match(r"^https?://", stripped):
            continue

        # Standalone layout noise (exact match)
        if low in standalone_noise:
            continue

        # "Helpful X Y" vote buttons — standalone or with NYU prefix
        if re.search(r"Helpful\s+\d+\s+\d+", stripped, re.IGNORECASE):
            continue

        # --- inline artifact removal ---

        # Nav fragments: "… New York University Log In Sign Up Help"
        stripped = re.sub(r"\s*New York University\s+Log In Sign Up Help", "", stripped).strip()
        stripped = re.sub(r"\s*Log In Sign Up Help", "", stripped).strip()

        # Collapsed sidebar triplet: "… Rate New York University Compare"
        stripped = re.sub(r"\s+Rate\s+New York University\s+Compare", "", stripped).strip()

        # "New York University Compare" or "New York University" prefixing a review field
        stripped = re.sub(r"^New York University\s+(Compare\s+)?", "", stripped, flags=re.IGNORECASE).strip()

        # Professor-name prefix on review-field lines (two-column interleaving):
        # "Vivian Giang For Credit: Yes Rate" → "For Credit: Yes"
        if review_field_re.search(stripped):
            stripped = name_re.sub("", stripped).strip()
            # Also strip trailing "Rate" or "Compare" left after removing the name
            stripped = re.sub(r"\s+(Rate|Compare)\s*$", "", stripped, flags=re.IGNORECASE).strip()

        # Professor-name prefix on mid-sentence text (name rendered in sidebar next to review):
        # "Jason Turetsky reach. a lot" → "reach. a lot"
        # Only strip when immediately followed by a lowercase letter (mid-sentence artifact)
        m_mid = re.match(rf"^{re.escape(professor_name)}\s+([a-z])", stripped, re.IGNORECASE)
        if m_mid and m_mid.group(1).islower():
            stripped = name_re.sub("", stripped, count=1).strip()

        # Trailing "Rate" or "Compare" artifacts at end of line
        stripped = re.sub(r"\s+(Rate|Compare)\s*$", "", stripped, flags=re.IGNORECASE).strip()

        if not stripped:
            continue

        cleaned.append(stripped)

    # Post-process assembled text
    text = "\n".join(cleaned)

    # Remove remaining "ProfName Rate" or "ProfName\nBusiness\nCompare" multi-line artifacts
    text = re.sub(
        rf"\n{re.escape(professor_name)}\n(Business\n)?(Compare\n)?",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        rf"\n{re.escape(professor_name)}\s+Rate\n",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Strip the per-page stats header that precedes the first real review.
    # Course codes like FINCGB6020, STATUB103, ECONUB2 mark the start of each review.
    # Walk back from the first course code to include the preceding QUALITY label.
    m = re.search(r"(?m)^[A-Z]{2,}[-]?[A-Z]*\d{2,}", text)
    if m:
        pre = text[: m.start()]
        qual_idx = pre.rfind("QUALITY")
        if qual_idx >= 0:
            text = text[qual_idx:]
        else:
            text = text[m.start():]

    # Collapse extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents():
    """Load and clean all Rate My Professors PDFs from the documents folder."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        if not filename.endswith(".pdf"):
            continue
        if "Rate My Professors" not in filename:
            continue

        professor = _professor_name_from_filename(filename)
        filepath = os.path.join(DOCS_PATH, filename)

        with pdfplumber.open(filepath) as pdf:
            raw = "\n\n".join(
                p.extract_text() for p in pdf.pages if p.extract_text()
            )

        text = _clean_text(raw, professor)
        documents.append({
            "professor": professor,
            "filename": filename,
            "text": text,
        })

    print(f"Loaded {len(documents)} document(s): {[d['professor'] for d in documents]}")
    return documents


def chunk_document(text, professor):
    """
    Split a professor's review page into overlapping character-based chunks.

    Strategy: 500-character chunks with 50-character overlap.
    - RMP reviews are 100-350 characters each; 500 chars captures 1-2 complete
      reviews per chunk so retrieval returns full opinions, not sentence halves.
    - 50-char overlap preserves context at chunk boundaries (e.g. a review that
      starts near the end of one chunk still appears complete in the next).
    - min_length=80 filters noise left after cleaning (ratings-only lines, etc.).

    Each chunk dict contains:
      "text"       : the chunk string
      "professor"  : professor full name
      "source"     : original PDF filename
      "chunk_id"   : unique ID, e.g. "alison_taylor_3"
    """
    chunk_size = 500
    overlap = 50
    min_length = 80

    prefix = professor.lower().replace(" ", "_")
    chunks = []
    counter = 0
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if len(chunk_text) >= min_length:
            chunks.append({
                "text": chunk_text,
                "professor": professor,
                "source": f"{professor} (Rate My Professors)",
                "chunk_id": f"{prefix}_{counter}",
            })
            counter += 1
        start += chunk_size - overlap

    return chunks

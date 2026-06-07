import gradio as gr

from ingest import load_documents, chunk_document
from retriever import embed_and_store, retrieve, get_collection
from generator import generate_response


def run_ingestion():
    collection = get_collection()

    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return

    print("Ingesting professor review PDFs...")
    documents = load_documents()
    all_chunks = []

    for doc in documents:
        chunks = chunk_document(doc["text"], doc["professor"])
        all_chunks.extend(chunks)
        print(f"  {doc['professor']}: {len(chunks)} chunks")

    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} total chunks stored.")
    else:
        print(
            "\n⚠️  No chunks produced. Check that ingest.py loaded the PDFs correctly.\n"
            "    The app will start, but queries won't return answers.\n"
        )


def handle_query(question):
    if not question.strip():
        return "", ""
    retrieved = retrieve(question)
    answer = generate_response(question, retrieved)
    sources = "\n".join(
        f"• {c['source']} (distance: {c['distance']:.3f})"
        for c in retrieved
        if c["distance"] <= 0.75
    )
    return answer, sources or "No sufficiently relevant chunks found."


EXAMPLE_QUESTIONS = [
    "What do students say about Jeffrey Meli's grading?",
    "Is Alison Taylor a good professor for finance courses?",
    "Which professor is the most organized according to reviews?",
    "How difficult are Raymond Ro's courses?",
    "What do students say about Giulia Brancaccio's teaching style?",
    "Which NYU Business professor gets the best overall ratings?",
    "Do any professors at NYU Stern curve their grades?",
    "What are the main complaints students have about business professors?",
]

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue"),
    title="NYU Business Professor Guide",
) as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#1e3a5f; margin:0;">
                NYU Business Professor Guide
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask anything about Business professors at NYU — answers drawn from student reviews.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder='e.g. "What do students say about Jeffrey Meli\'s exams?"',
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")
            answer_box = gr.Textbox(label="Answer", lines=10, interactive=False)
            sources_box = gr.Textbox(label="Retrieved from", lines=4, interactive=False)

            ask_btn.click(
                fn=handle_query,
                inputs=question_box,
                outputs=[answer_box, sources_box],
            )
            question_box.submit(
                fn=handle_query,
                inputs=question_box,
                outputs=[answer_box, sources_box],
            )

        with gr.Column(scale=1, min_width=200):
            gr.HTML("""
                <div style="background:#f0f4ff; border:1px solid #c7d2fe;
                            border-radius:8px; padding:1rem; font-size:0.875rem;">
                    <strong style="color:#1e3a5f;">Professors loaded</strong>
                    <ul style="margin:0.5rem 0 0; padding-left:1.2rem; color:#374151;">
                        <li>Alison Taylor</li>
                        <li>Eugene Kolker</li>
                        <li>Giulia Brancaccio</li>
                        <li>Jason Turetsky</li>
                        <li>Jeffrey Meli</li>
                        <li>Raymond Ro</li>
                        <li>Richard Hendler</li>
                        <li>Sinja Leonelli</li>
                        <li>Stephen Master</li>
                        <li>Vivian Giang</li>
                    </ul>
                    <p style="color:#6b7280; margin:0.75rem 0 0; font-size:0.8rem;">
                        Source: Rate My Professors
                    </p>
                </div>
            """)
            gr.Examples(
                examples=[[q] for q in EXAMPLE_QUESTIONS],
                inputs=question_box,
                label="Example questions",
            )


if __name__ == "__main__":
    run_ingestion()
    demo.launch()

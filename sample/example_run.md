# Example Run

The following is the intended shape of the CLI interaction. Run the application with a fresh arXiv paper to produce current evidence.

```text
======================================================================
AUTONOMOUS arXiv PAPER DIGEST & QA AGENT
======================================================================
Enter a research topic, arXiv ID, or arXiv URL.

> 2401.12345

[1/7] Understanding query...
[2/7] Paper selected.
[3/7] PDF downloaded.
[4/7] PDF parsed: 20 pages, 42000 extracted characters.
[5/7] Chunks and FAISS index created: 80 chunks.
[6/7] Executive briefing generated.

======================================================================
EXECUTIVE BRIEFING
======================================================================
Title: <paper title>
Authors: <authors>
arXiv ID: 2401.12345
Publish date: <date>
Link: https://arxiv.org/abs/2401.12345

WHY THIS PAPER MATTERS
<plain-English summary>

PROBLEM STATEMENT
<problem>

METHOD / APPROACH
• ...
• ...

KEY RESULTS / CLAIMS
• ...
• ...

LIMITATIONS
• ...
• ...

SUGGESTED FOLLOW-UP QUESTIONS
• ...
• ...

[7/7] QA mode ready.

Ask a question (or type 'exit'):
> What is the main contribution?

ANSWER
<grounded answer>

RETRIEVED SOURCES
• page 3, section '...', chunk_0012, similarity=0.71
• page 4, section '...', chunk_0016, similarity=0.64

Ask a question (or type 'exit'):
> What is the authors' favorite programming language?

ANSWER
I couldn't find that information in the paper.
```

Do not submit this synthetic example as evidence. Use a real run from the CLI in the README/screenshots/video.

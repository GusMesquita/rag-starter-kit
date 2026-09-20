# Answering agent behavior contract

`app/rag.py::ask` is the only place an LLM generates a user-facing answer.
This is what a caller is entitled to assume about it.

## Contract

- **Grounded-only, enforced twice.** The system prompt instructs the model to
  answer only from the given context and say "I don't know" otherwise — but
  that's a request, not a guarantee. The code enforces the empty-context case
  directly: if retrieval returns zero chunks, `ask()` returns a fixed
  "não sei" answer **without calling the LLM at all** (`_NO_CONTEXT_ANSWER`).
  This is cheaper and cannot be talked out of it by a cleverly-worded question.
- **The model never sees documents outside the top-`k` retrieved.** It cannot
  answer from anything ingested that didn't match the query semantically —
  if an answer feels wrong, the fix is usually re-chunking or re-ingesting,
  not prompt tweaking.
- **`sources_used` is always the true count**, not an LLM-reported number —
  it comes from the retrieval step, so a caller can distinguish "answered
  confidently from 3 sources" from "answered from 1 marginal match."
- **No conversation memory.** Each `/ask` call is independent; the model
  never sees prior questions. Multi-turn context is a caller responsibility
  (concatenate prior Q&A into `question` yourself if you need it).

## Failure mode by design

A malformed or empty question still reaches the vector store and the model —
there's no local validation beyond "is it a string." Garbage in gets a
best-effort (possibly "não sei") answer out, never a crash.

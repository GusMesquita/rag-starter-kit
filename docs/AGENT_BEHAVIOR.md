# Answering agent behavior contract

`app/rag.py::ask` is the only place an LLM generates a user-facing answer.
This is what a caller is entitled to assume about it.

## Contract

- **Grounded-only, enforced twice.** The system prompt instructs the model to
  answer only from the given context and say "I don't know" otherwise — but
  that's a request, not a guarantee. The code enforces the empty-context case
  directly: se nenhum trecho recuperado fica **dentro de `MAX_DISTANCE`**,
  `ask()` devolve um "não sei" fixo **sem chamar o LLM** (`_NO_CONTEXT_ANSWER`).
  É mais barato e não há pergunta bem formulada que convença o contrário.
- **O threshold é o que faz o "não sei" existir na prática.** `n_results`
  sempre devolve k vizinhos — existam ou não documentos sobre o assunto. Sem
  o corte por distância, com a base populada o caminho do "não sei" nunca
  roda: o vizinho mais próximo entra como contexto só por ser o menos ruim.
  A distância é cosseno (espaço declarado explicitamente na coleção), então
  vive em [0, 2] e é comparável entre consultas.
- **The model never sees documents outside the top-`k` retrieved.** It cannot
  answer from anything ingested that didn't match the query semantically —
  if an answer feels wrong, the fix is usually re-chunking or re-ingesting,
  not prompt tweaking.
- **A resposta cita as fontes.** `sources` traz uma entrada por documento
  (não por chunk), com a melhor distância obtida — o suficiente para o
  chamador verificar a resposta em vez de confiar nela.
- **`sources_used` is always the true count**, not an LLM-reported number —
  it comes from the retrieval step, so a caller can distinguish "answered
  confidently from 3 sources" from "answered from 1 marginal match."
- **No conversation memory.** Each `/ask` call is independent; the model
  never sees prior questions. Multi-turn context is a caller responsibility
  (concatenate prior Q&A into `question` yourself if you need it).

## Failure mode by design

Pergunta vazia ou acima de 2.000 caracteres é rejeitada com 422 na borda
(`app/main.py`), não chega aqui. O que passa da validação de forma e ainda é
lixo recebe o melhor esforço — na prática, "não sei" — nunca um crash.

Reingerir a mesma `source` **substitui** o que havia antes: os ids de chunk são
derivados de `sha256(source)` + índice, e a fonte é apagada antes da gravação.
Não existe modo "acrescentar outra versão do mesmo arquivo".

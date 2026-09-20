# rag-starter-kit

Pipeline RAG (Retrieval-Augmented Generation) genérico e reutilizável: ingesta documentos, gera embeddings localmente (sem depender de API paga de embeddings), guarda no Chroma, e responde perguntas com Claude usando só o contexto recuperado.

```
POST /ingest  { text, source }  ──▶  chunk ──▶ embed (local) ──▶ Chroma       (requer X-API-Key)
POST /ask     { question }      ──▶  retrieve top-k ──▶ Claude ──▶ resposta   (requer X-API-Key)
```

Comportamento do agente de resposta documentado em [docs/AGENT_BEHAVIOR.md](./docs/AGENT_BEHAVIOR.md) — em resumo: sem contexto recuperado, a API responde "não sei" **sem chamar o LLM**.

## Por que existe

É a base de qualquer "pergunte aos seus documentos": FAQ de suporte, busca em documentação interna, ou — combinado com o [lead-router](../lead-router) — responder automaticamente a dúvida de um lead antes de rotear pro time de vendas.

## Autenticação

Mesmo padrão do lead-router: header `X-API-Key`, chaves em `API_KEYS` (separadas por vírgula), vazio desabilita auth (dev only). Ver `app/auth.py`.

## Rodando localmente

```bash
uv sync
cp .env.example .env   # preencha ANTHROPIC_API_KEY e API_KEYS
uv run uvicorn app.main:app --reload
```

```bash
curl -X POST localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave" \
  -d '{"text": "Nosso horário de atendimento é das 9h às 18h.", "source": "faq.txt"}'

curl -X POST localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave" \
  -d '{"question": "Qual o horário de atendimento?"}'
```

Ou use o script de exemplo pra ingerir um arquivo inteiro:

```bash
uv run python scripts/ingest_example.py caminho/para/documento.txt
```

Ou via Docker:

```bash
docker build -t rag-starter-kit .
docker run -p 8000:8000 --env-file .env rag-starter-kit
```

## Chat UI (frontend)

Veja [frontend/](./frontend) — SPA React de chat que consome `POST /ask`.

## Integrações

- Exposto como serviço HTTP, então qualquer workflow n8n pode chamar `/ask` como um passo de "responder com base nos documentos" — veja [n8n-ai-cookbook](../n8n-ai-cookbook).
- O [lead-router](../lead-router) pode chamar `/ask` para responder à mensagem de um lead antes (ou em vez) de rotear para um humano.

## Testes

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

## Roadmap

- [ ] Deduplicação de chunks re-ingeridos do mesmo `source`
- [ ] Suporte a PDF/DOCX na ingestão (hoje só texto puro)
- [ ] Streaming da resposta do `/ask`

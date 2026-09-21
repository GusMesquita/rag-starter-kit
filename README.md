# rag-starter-kit

Pipeline RAG (Retrieval-Augmented Generation) genérico e reutilizável: ingesta documentos, gera embeddings localmente (sem depender de API paga de embeddings), guarda no Chroma, e responde perguntas com Claude usando só o contexto recuperado.

```
POST /ingest  { text, source }  ──▶  chunk ──▶ embed (local) ──▶ Chroma       (requer X-API-Key)
POST /ask     { question }      ──▶  retrieve top-k ──▶ Claude ──▶ resposta   (requer X-API-Key)
```

Comportamento do agente de resposta documentado em [docs/AGENT_BEHAVIOR.md](./docs/AGENT_BEHAVIOR.md) — em resumo: sem contexto recuperado, a API responde "não sei" **sem chamar o LLM**.

## Por que existe

É a base de qualquer "pergunte aos seus documentos": FAQ de suporte, busca em documentação interna, ou — combinado com o `lead-router` — responder automaticamente a dúvida de um lead antes de rotear pro time de vendas.

## Segurança

Mesmo padrão do lead-router. O default é **fail-closed**: `ENVIRONMENT` vale `prod` quando não definido, e em `prod` o app **não sobe** sem `API_KEYS`. Rodar sem auth exige declarar `ENVIRONMENT=dev`.

| Controle | Onde | Configuração |
| --- | --- | --- |
| Auth por `X-API-Key` (comparação em tempo constante) | `app/auth.py` | `API_KEYS` |
| CORS com allowlist explícita (nunca `*`) | `app/main.py` | `CORS_ORIGINS` |
| Rate limit por chave (ou IP), janela deslizante | `app/ratelimit.py` | `RATE_LIMIT_PER_MINUTE` |
| Teto de corpo no `/ingest` (Content-Length + `max_length`) | `app/main.py` | `MAX_INGEST_BYTES` |
| Contexto recuperado delimitado em `<documento>` | `app/rag.py` | — |
| Log estruturado sem texto de documento nem pergunta | `app/logging_config.py` | — |

O SPA em `frontend/` **não** carrega a API key: tudo em `import.meta.env.VITE_*` é inlinado no bundle. Em produção, um proxy/BFF injeta o header server-side.

### Prompt injection

O conteúdo recuperado é dado, não instrução: cada trecho vai dentro de `<documento id="n">`, com o `</documento>` interno escapado, e o system prompt manda ignorar qualquer comando encontrado ali. A defesa que sustenta isso é mais simples: **o modelo do RAG não recebe tool nenhuma**, então uma instrução escondida num documento não tem o que acionar. Se um dia esse caminho ganhar tools, a delimitação sozinha deixa de bastar.

## Rodando localmente

```bash
uv sync
cp .env.example .env   # preencha ANTHROPIC_API_KEY (ENVIRONMENT=dev já vem no exemplo)
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

- Exposto como serviço HTTP, então qualquer workflow n8n pode chamar `/ask` como um passo de "responder com base nos documentos" — veja `n8n-ai-cookbook`.
- O `lead-router` pode chamar `/ask` para responder à mensagem de um lead antes (ou em vez) de rotear para um humano.

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

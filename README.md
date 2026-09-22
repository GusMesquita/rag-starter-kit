# rag-starter-kit

Pipeline RAG (Retrieval-Augmented Generation) genérico e reutilizável: ingesta documentos, gera embeddings localmente (sem depender de API paga de embeddings), guarda no Chroma, e responde perguntas com Claude usando só o contexto recuperado.

```
POST /ingest  { text, source }  ──▶  chunk ──▶ embed (local) ──▶ Chroma       (requer X-API-Key)
POST /ask     { question }      ──▶  retrieve top-k ──▶ Claude ──▶ resposta   (requer X-API-Key)
POST /ask/stream { question }   ──▶  mesma resposta, em SSE, token a token    (requer X-API-Key)
```

Comportamento do agente de resposta documentado em [docs/AGENT_BEHAVIOR.md](./docs/AGENT_BEHAVIOR.md) — em resumo: sem contexto **dentro do threshold de distância**, a API responde "não sei" sem chamar o LLM, e toda resposta vem com as fontes citadas.

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

O app em `web/` **não** carrega a API key no browser: `lib/rag-api.ts` importa `server-only`, então importá-lo de um Client Component é erro de build. A pergunta passa pelo Route Handler `/api/ask`, que é quem põe o header. O CI constrói com uma chave-canário e falha se ela aparecer em `.next/static`.

### Prompt injection

O conteúdo recuperado é dado, não instrução: cada trecho vai dentro de `<documento id="n">`, com o `</documento>` interno escapado, e o system prompt manda ignorar qualquer comando encontrado ali. A defesa que sustenta isso é mais simples: **o modelo do RAG não recebe tool nenhuma**, então uma instrução escondida num documento não tem o que acionar. Se um dia esse caminho ganhar tools, a delimitação sozinha deixa de bastar.

## Rodando localmente

```bash
uv sync
cp .env.example .env   # preencha ANTHROPIC_API_KEY (ENVIRONMENT=dev já vem no exemplo)
uv run uvicorn app.main:app --reload
```

```bash
export API_KEY=uma-das-chaves-de-API_KEYS

curl -X POST localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Nosso horário de atendimento é das 9h às 18h.", "source": "faq.txt"}'

curl -X POST localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"question": "Qual o horário de atendimento?"}'

# -N desliga o buffer do curl; sem ele a resposta aparece toda de uma vez e o
# streaming some justamente na hora de conferir se funciona.
curl -N -X POST localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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

## Chat UI (web)

Veja [web/](./web) — chat Next.js que consome `POST /ask/stream` e mostra a
resposta token a token, com cada fonte e a distância que a trouxe.

```bash
cd web
pnpm install
cp .env.example .env.local   # RAG_API_URL e RAG_API_KEY
pnpm dev
```

Como o browser fala com o Next e não com a API, o `CORS_ORIGINS` do backend
não precisa listar o domínio do app.

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

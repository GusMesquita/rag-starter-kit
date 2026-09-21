# Convenções deste repositório

Este documento é auto-contido: não depende de nenhum outro repositório.

## Ambiente

- **Python 3.13.13** e **Node 26.9.0**, declarados em `.mise.toml` (e `.nvmrc` para quem
  usa nvm). Com [mise](https://mise.jdx.dev): `mise install` resolve as duas de uma vez.
  Com nvm: `nvm use` lê o `.nvmrc`.
- **Dependências Python**: `uv`, com `[dependency-groups] dev = [...]` — não
  `[project.optional-dependencies]`, que `uv sync --group dev` não reconhece.
- `uv.lock` e `package-lock.json` são commitados.

## Backend

- **FastAPI + uvicorn**, com `lifespan` (não `@app.on_event`, deprecado) para
  inicializar recursos.
- **Lint**: `ruff check .` e `ruff format .`, `select = ["E","F","I","UP","B"]`,
  `ignore = ["B008"]` — FastAPI usa `Depends()`/`Query()` como default de argumento por
  design; é o idiom do framework, não um bug.
- **Vetores**: Chroma. O cliente do Chroma é **síncrono**; toda chamada a ele dentro de
  um endpoint `async` passa por `run_in_threadpool`, senão trava o event loop inteiro.
- **Ingestão idempotente**: o id de cada chunk é derivado de `source` + índice, não de
  `uuid4()` — reingerir o mesmo documento atualiza em vez de duplicar.
- **Erros de API externa**: hierarquia de exceções tipada, para `isinstance()` em vez de
  comparação de string. 404 não é re-tentado; 429/5xx usam backoff exponencial.
- **Logging**: JSON estruturado em `stderr`. Nunca logar `X-API-Key` nem o conteúdo
  integral de um documento ou pergunta.

## Segurança

- **Autenticação**: header `X-API-Key` comparado com `secrets.compare_digest` (timing-safe).
  Não é JWT nem cookie — são chamadas serviço-a-serviço, não sessões de navegador.
- **Fail-closed**: com `ENVIRONMENT=prod`, o app **não sobe** sem `API_KEYS` configurado.
  Autenticação desligada é um modo explícito de desenvolvimento, nunca um default silencioso.
- **Nenhum segredo chega ao browser.** O frontend nunca carrega a API key; toda chamada
  autenticada passa pelo servidor do Next.
- **O modelo nunca vê segredos nem infraestrutura.**
- **Documento ingerido é entrada não confiável.** Um documento pode conter instruções
  endereçadas ao modelo. Mitigação: o contexto vai delimitado e declarado como dado, e
  **este serviço nunca dá tools ao modelo** — sem tools, uma injeção bem-sucedida não tem
  o que acionar.
- **Grounding é garantido em código, não em prompt.** Se a recuperação não devolve nenhum
  documento acima do limiar de similaridade, a chamada ao LLM é pulada inteiramente. Não
  se confia na instrução de sistema para não alucinar.
- **Limite de tamanho na ingestão.** `/ingest` aceita texto de terceiro; sem teto de
  `Content-Length` e de `max_length`, é um OOM trivial de provocar.

### Exceção de auditoria: chromadb

`pip-audit` reporta 5 PYSEC em `chromadb` (a última versão publicada não tem
correção). Todas exigem alcançar o **servidor HTTP** do Chroma — injeção de
código via `trust_remote_code` no endpoint de collections, e falhas de RBAC
entre tenants.

Este projeto usa `chromadb.PersistentClient`: o Chroma roda embarcado, no mesmo
processo, sem porta aberta. A superfície não existe aqui, e por isso a CI
ignora esses IDs explicitamente em `.github/workflows/ci.yml`.

Se o Chroma algum dia virar um serviço separado, as exceções deixam de valer e
precisam ser removidas antes do deploy.

## Frontend

- **Next.js 16 (App Router)** + TypeScript. Turbopack é default no 16 — não passar
  `--turbopack` nos scripts. `params`, `searchParams`, `cookies` e `headers` são
  assíncronos e **precisam** de `await`.
- **shadcn/ui** com `cssVariables: true`, sobre **Tailwind v4**. Componentes são copiados
  para o repo e adaptados — não são importados de um pacote compartilhado.
- **Animação**: `motion`, sempre respeitando `prefers-reduced-motion`.
- **Lógica pura sai do componente** para `lib/`, o que também a deixa testável isoladamente.
- **Testes**: Vitest para regra de negócio pura; um fluxo end-to-end em Playwright.

## Testes

Toda lógica não trivial ganha um teste que **falha se a lógica for removida**, verificado
por mutação: altere o comportamento, rode o teste, confirme que quebra. Um teste que passa
com qualquer implementação não conta como cobertura.

## Docker

Multi-stage, base pinada, usuário não-root, `HEALTHCHECK`, `.dockerignore` mantido em dia.
Nenhum segredo em `ARG`/`ENV` de build.

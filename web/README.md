# web — chat do rag-starter-kit

Next.js 16 (App Router), React 19, Tailwind 4 e shadcn/ui.

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

## Por que existe um Route Handler aqui

O dashboard do `lead-router` fala com a API direto de um Server Component,
sem intermediário. Aqui não dá: a resposta precisa **escorrer** até o browser
e um Server Component só sabe entregar HTML pronto.

`app/api/ask/route.ts` é o único lugar onde a chave aparece. Ele valida a
pergunta, chama `POST /ask/stream` e devolve o corpo do upstream **sem
bufferizar** — reempacotar a resposta em texto aqui seguraria tudo até o fim e
desfaria o streaming que o backend acabou de produzir.

Efeito colateral bom: como o browser nunca chama a API diretamente, o
`CORS_ORIGINS` do backend não precisa listar o domínio deste app.

## Onde a chave fica

`lib/rag-api.ts` importa `server-only`: importá-lo de um Client Component é
**erro de build**, não um segredo publicado. A chave vem de `RAG_API_KEY` —
sem o prefixo `NEXT_PUBLIC_`, que é o que inlina valores no bundle. O CI
constrói com uma chave-canário e falha se ela aparecer em `.next/static`.

## Streaming e acessibilidade

`lib/sse.ts` guarda o pedaço incompleto entre chunks. Sem isso, um evento que
chega partido ao meio pela rede some em silêncio — o sintoma é uma palavra
faltando na resposta, impossível de reproduzir de propósito.

O texto da resposta **não** é um `aria-live`: um live region recebendo token a
token faz o leitor de tela recomeçar a falar a cada palavra. O que é anunciado
é a transição ("Respondendo", "Resposta pronta, 3 fontes usadas"), num
`role="status"` visualmente oculto. O parágrafo carrega `aria-busy` enquanto
escreve.

As citações abrem num `HoverCard` cujo gatilho é um `<button>`: a distância
cosseno que trouxe cada trecho também precisa chegar a quem usa teclado.

## Componentes

`@gmui` é a registry deste portfólio, hospedada no `lead-router`. Entra nela o
que dois apps já duplicam — hoje, um item.

```bash
pnpm dlx shadcn@latest add @gmui/api-error-card
```

## Verificação

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

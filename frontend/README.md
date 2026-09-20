# rag-starter-kit chat

SPA React + TypeScript com um chat mínimo sobre o endpoint `POST /ask` do backend. Mostra a resposta grounded e quantas fontes (`sources_used`) embasaram cada resposta.

## Rodando localmente

```bash
npm install
cp .env.example .env   # VITE_API_URL e VITE_API_KEY, se a auth estiver ativa no backend
npm run dev
```

## Estrutura

```
src/
├── lib/api.ts             # cliente HTTP tipado para o backend (askQuestion)
├── lib/formatSources.ts   # regra pura de pluralização de "fontes" (testada)
├── components/ChatMessage.tsx, TypingIndicator.tsx
└── index.css              # entry point do Tailwind + tema (fonte de verdade)
```

Estilização é 100% Tailwind (utilities inline nos componentes) — não há CSS
próprio além do bloco `@theme` em `src/index.css`, que é a única fonte de
verdade de cores, tipografia e animações deste app. O tema é mantido **dentro
deste repositório**: nada aqui depende de um pacote ou diretório externo.

## Scripts

```bash
npm run dev       # dev server
npm run build     # tsc -b && vite build
npm run test      # vitest
npm run lint      # oxlint
```

## Docker

```bash
docker build -t rag-starter-kit-frontend .
docker run -p 8080:80 rag-starter-kit-frontend
```

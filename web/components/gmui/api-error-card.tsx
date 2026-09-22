import type { ReactNode } from "react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

// Um estado de erro que só diz "falhou" deixa o leitor sem próximo passo — e
// em dev o próximo passo é quase sempre "sua API não está no ar". Por isso
// `children` não é opcional: quem usa este card é obrigado a escrever a saída.
export function ApiErrorCard({
  title = "Sem resposta da API",
  detail,
  children,
}: {
  title?: string
  // A mensagem técnica; útil para distinguir 401 de conexão recusada.
  detail: string
  // O que fazer a respeito.
  children: ReactNode
}) {
  return (
    <Card role="alert">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{detail}</CardDescription>
      </CardHeader>
      <CardContent className="text-muted-foreground text-sm">{children}</CardContent>
    </Card>
  )
}

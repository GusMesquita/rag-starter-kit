import { formatSourcesLabel } from "../lib/formatSources";

export interface Message {
  role: "user" | "assistant";
  content: string;
  sourcesUsed?: number;
}

export function ChatMessage({ role, content, sourcesUsed }: Message) {
  const isUser = role === "user";
  return (
    <div className={`flex animate-fade-in-up gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
          isUser ? "bg-primary-soft text-primary" : "bg-gradient-to-br from-primary to-accent text-white"
        }`}
        aria-hidden="true"
      >
        {isUser ? "eu" : "IA"}
      </div>
      <div className={`flex max-w-[75%] flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "rounded-tr-sm bg-gradient-to-br from-primary to-accent text-white"
              : "rounded-tl-sm border border-border bg-surface text-text"
          }`}
        >
          {content}
        </div>
        {!isUser && sourcesUsed !== undefined && (
          <span className="px-1 text-xs text-muted">{formatSourcesLabel(sourcesUsed)}</span>
        )}
      </div>
    </div>
  );
}

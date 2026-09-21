"""Structured (JSON-lines) logging setup — stdlib only.

Regra de conteúdo deste serviço: **nunca** logar o texto dos documentos nem a
pergunta. Ambos são conteúdo do usuário e podem conter qualquer coisa (contrato,
prontuário, credencial). Logamos tamanho, contagem e origem — o suficiente para
depurar retrieval sem reter o conteúdo no agregador.
"""

import json
import logging
import sys
from datetime import UTC, datetime

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Campos passados via extra=, para o log ser estruturado e não só texto.
        payload.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("rag_starter_kit")
    root.setLevel(level)
    root.handlers = [handler]
    root.propagate = False

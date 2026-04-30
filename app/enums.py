import enum

class PlaylistItemRole(enum.Enum):
    AUTO = "AUTO"           # Inteligente: Pula intro se não for o primeiro do bloco, pula final se não for o último.
    FULL = "FULL"           # Completo: Ignora regras de corte de intro/final (toca a mídia inteira).
    HEAD = "HEAD"           # Início: Toca sempre a abertura da mídia + corpo, mas pula o final.
    TAIL = "TAIL"           # Fim: Toca sempre o corpo + encerramento da mídia, mas pula o início.
    BODY = "BODY"           # Apenas Corpo: Pula sempre abertura e encerramento da mídia.
    OPENING = "OPENING"     # Grampo de Abertura: Roda fixo no início do horário (sempre com intro).
    CLOSING = "CLOSING"     # Grampo de Encerramento: Roda fixo no fim do horário (sempre com final).

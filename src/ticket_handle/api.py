import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI

from ticket_handle.classifier import TicketClassifier
from ticket_handle.config import build_llm, get_settings
from ticket_handle.models import Ticket
from ticket_handle.router import RoutingDecision
from ticket_handle.service import TicketService

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Ticket Handle")


@lru_cache
def get_service() -> TicketService:
    settings = get_settings()
    llm = build_llm(settings)
    return TicketService(TicketClassifier(llm), settings.confidence_threshold)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets/route")
def route_ticket(
    ticket: Ticket, service: Annotated[TicketService, Depends(get_service)]
) -> RoutingDecision:
    return service.handle(ticket)

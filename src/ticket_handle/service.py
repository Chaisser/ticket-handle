import logging
from time import perf_counter
from typing import Protocol

from ticket_handle.classifier import ClassificationError
from ticket_handle.models import Ticket, TicketClassification
from ticket_handle.router import RoutingDecision, route, route_failure

logger = logging.getLogger(__name__)


class Classifier(Protocol):
    def classify(self, ticket: Ticket) -> TicketClassification: ...


class TicketService:
    def __init__(self, classifier: Classifier, confidence_threshold: float) -> None:
        self._classifier = classifier
        self._confidence_threshold = confidence_threshold

    def handle(self, ticket: Ticket) -> RoutingDecision:
        start = perf_counter()

        try:
            classification = self._classifier.classify(ticket)
        except ClassificationError:
            logger.exception("classification_failed ticket_id=%s", ticket.ticket_id)
            decision = route_failure(ticket)
        else:
            decision = route(ticket, classification, self._confidence_threshold)

        latency_ms = round((perf_counter() - start) * 1000)
        logger.info(
            "ticket_routed ticket_id=%s queue=%s rule=%s latency_ms=%d",
            decision.ticket_id,
            decision.queue,
            decision.rule,
            latency_ms,
        )

        return decision

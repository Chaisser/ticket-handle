from enum import StrEnum

from pydantic import BaseModel

from ticket_handle.models import Category, Ticket, TicketClassification, Urgency


class Queue(StrEnum):
    EMERGENCY = "emergency"
    BILLING_TEAM = "billing_team"
    OUTAGE_TEAM = "outage_team"
    CONTRACTS_TEAM = "contracts_team"
    HUMAN_REVIEW = "human_review"


class Rule(StrEnum):
    SAFETY_FIRST = "safety_first"
    LOW_CONFIDENCE = "low_confidence"
    CATEGORY = "category"
    CLASSIFICATION_FAILED = "classification_failed"


CATEGORY_QUEUES = {
    Category.BILLING: Queue.BILLING_TEAM,
    Category.OUTAGE: Queue.OUTAGE_TEAM,
    Category.CONTRACT_CHANGE: Queue.CONTRACTS_TEAM,
    Category.OTHER: Queue.HUMAN_REVIEW,
}


class RoutingDecision(BaseModel):
    ticket_id: str
    queue: Queue
    rule: Rule
    classification: TicketClassification | None = None


def route(
    ticket: Ticket, classification: TicketClassification, confidence_threshold: float
) -> RoutingDecision:
    if (
        classification.urgency == Urgency.HIGH
        and classification.category == Category.OUTAGE
    ):
        return RoutingDecision(
            classification=classification,
            ticket_id=ticket.ticket_id,
            queue=Queue.EMERGENCY,
            rule=Rule.SAFETY_FIRST,
        )
    elif classification.confidence < confidence_threshold:
        return RoutingDecision(
            classification=classification,
            ticket_id=ticket.ticket_id,
            queue=Queue.HUMAN_REVIEW,
            rule=Rule.LOW_CONFIDENCE,
        )
    else:
        return RoutingDecision(
            classification=classification,
            ticket_id=ticket.ticket_id,
            queue=CATEGORY_QUEUES[classification.category],
            rule=Rule.CATEGORY,
        )


def route_failure(ticket: Ticket) -> RoutingDecision:
    return RoutingDecision(
        ticket_id=ticket.ticket_id,
        rule=Rule.CLASSIFICATION_FAILED,
        queue=Queue.HUMAN_REVIEW,
    )

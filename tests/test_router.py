from ticket_handle.models import Category, Ticket, TicketClassification, Urgency
from ticket_handle.router import Queue, Rule, route, route_failure

TICKET = Ticket(ticket_id="T1", text="test")
THRESHOLD = 0.7


def make_classification(
    category: Category = Category.BILLING,
    urgency: Urgency = Urgency.NORMAL,
    confidence: float = 0.9,
) -> TicketClassification:
    return TicketClassification(
        reason="test", category=category, urgency=urgency, confidence=confidence
    )


def test_confident_billing_goes_to_billing_team():
    decision = route(TICKET, make_classification(), THRESHOLD)

    assert decision.queue == Queue.BILLING_TEAM
    assert decision.rule == Rule.CATEGORY


def test_low_confidence_goes_to_human_review():
    decision = route(TICKET, make_classification(confidence=0.5), THRESHOLD)

    assert decision.queue == Queue.HUMAN_REVIEW
    assert decision.rule == Rule.LOW_CONFIDENCE


def test_safety_outage_goes_to_emergency_even_with_low_confidence():
    classification = make_classification(
        category=Category.OUTAGE, urgency=Urgency.HIGH, confidence=0.5
    )
    decision = route(TICKET, classification, THRESHOLD)

    assert decision.queue == Queue.EMERGENCY
    assert decision.rule == Rule.SAFETY_FIRST


def test_other_category_goes_to_human_review():
    decision = route(
        TICKET,
        make_classification(category=Category.OTHER, urgency=Urgency.NORMAL),
        THRESHOLD,
    )

    assert decision.queue == Queue.HUMAN_REVIEW


def test_failure_goes_to_human_review():
    decision = route_failure(TICKET)

    assert decision.queue == Queue.HUMAN_REVIEW
    assert decision.rule == Rule.CLASSIFICATION_FAILED
    assert decision.classification is None

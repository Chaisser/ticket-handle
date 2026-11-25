from ticket_handle.classifier import ClassificationError
from ticket_handle.models import Category, Ticket, TicketClassification, Urgency
from ticket_handle.router import Queue, Rule
from ticket_handle.service import TicketService

TICKET = Ticket(ticket_id="T1", text="Why is my invoice so high?")


class FakeClassifier:
    def __init__(
        self, result: TicketClassification | None = None, error: Exception | None = None
    ) -> None:
        self.result = result
        self.error = error

    def classify(self, ticket: Ticket) -> TicketClassification:
        if self.error is not None:
            raise self.error

        assert self.result is not None
        return self.result


def test_successful_classification_is_routed():
    classification = TicketClassification(
        reason="Invoice question",
        category=Category.BILLING,
        urgency=Urgency.NORMAL,
        confidence=0.9,
    )

    service = TicketService(
        FakeClassifier(result=classification), confidence_threshold=0.7
    )

    decision = service.handle(TICKET)

    assert decision.queue == Queue.BILLING_TEAM
    assert decision.classification == classification


def test_classifier_failure_goes_to_human_review():
    error = ClassificationError("LLM Unavailable")
    service = TicketService(FakeClassifier(error=error), confidence_threshold=0.7)

    decision = service.handle(TICKET)

    assert decision.queue == Queue.HUMAN_REVIEW
    assert decision.rule == Rule.CLASSIFICATION_FAILED

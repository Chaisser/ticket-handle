from enum import StrEnum

from pydantic import BaseModel, Field


class Urgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Category(StrEnum):
    BILLING = "billing"
    CONTRACT_CHANGE = "contract_change"
    OUTAGE = "outage"
    OTHER = "other"


class Ticket(BaseModel):
    ticket_id: str
    text: str = Field(min_length=1)


class TicketClassification(BaseModel):
    reason: str = Field(description="One short sentence why related category selected")
    category: Category
    urgency: Urgency = Field(
        description="High is only for a safety risk or an outage affecting multiple customers."
    )
    confidence: float = Field(ge=0.0, le=1.0)

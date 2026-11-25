import pytest
from pydantic import ValidationError
from ticket_handle.models import Ticket


def test_empty_ticket_text_is_rejected():
    with pytest.raises(ValidationError):
        Ticket(ticket_id="T1", text="")

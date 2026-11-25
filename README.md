# Ticket Handle

A small, production-minded example: an LLM classifies incoming customer tickets for an energy utility, and plain rules route them to the right team.

The model classifies. Plain Python rules decide where the ticket goes. Anything uncertain or broken goes to a human.

```
ticket -> classify (LLM) -> route (rules) -> queue
              |                  |
            failed        low confidence
              |                  |
              +--> human_review <+
```

## Why it looks like this

The scenario: a utility that already builds agents with LangChain, but parses LLM output with regex and tests prompts by hand. This example shows the alternative I'd suggest, without changing their stack:

- **Structured output instead of regex.** The model fills in a Pydantic schema. If it returns a value our systems don't know (say `invoice` instead of `billing`), validation fails immediately instead of a wrong value reaching the CRM.
- **The model classifies, the rules route.** Queues are a business decision, so they live in `router.py` as plain code, not in the prompt. The model never sees them.
- **Safety first.** An outage marked as high urgency (gas smell, exposed cables, many customers affected) goes to `emergency` even when the model's confidence is low. A false alarm costs a few minutes. A missed gas leak costs much more.
- **Nothing gets lost.** If the LLM call fails or returns something invalid, the ticket goes to `human_review` and the reason is logged.
- **Not an agent.** The steps are known in advance, so one model call is enough. It's faster, cheaper and easier to test. I'd only reach for an agent when the steps aren't known upfront (see "Next steps").

## Project layout

```
src/ticket_handle/
    models.py       Ticket (input) and TicketClassification (what the model fills in)
    config.py       Settings from environment variables, and build_llm()
    classifier.py   LLM call with structured output, token logging
    router.py       Queues and routing rules (no LLM here)
    service.py      classify -> route -> log, one structured log line per ticket
    api.py          FastAPI endpoint
tests/              Unit tests, no LLM calls
evals/              Golden set and eval runner, real LLM calls
```

## Run it

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env      # add your OPENAI_API_KEY or ANTHROPIC_API_KEY
uv run --env-file .env uvicorn ticket_handle.api:app --reload
```

Open http://127.0.0.1:8000/docs, or:

```bash
curl -X POST http://127.0.0.1:8000/tickets/route \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "T1", "text": "I smell gas near my meter."}'
```

```json
{
  "ticket_id": "T1",
  "queue": "emergency",
  "rule": "safety_first",
  "classification": {
    "reason": "Gas smell indicates a safety risk and potential outage.",
    "category": "outage",
    "urgency": "high",
    "confidence": 0.9
  }
}
```

### Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `LLM_MODEL` | `openai:gpt-4o-mini` | Any LangChain provider string, e.g. `anthropic:claude-haiku-5-5` |
| `LLM_TEMPERATURE` | `0` | Leave empty (`LLM_TEMPERATURE=`) for models that reject it |
| `CONFIDENCE_THRESHOLD` | `0.7` | Below this, tickets go to human review. A business decision, so it's config. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | | Read by LangChain directly |

## Tests and evals

```bash
uv run pytest -v                                        # no LLM, no API key needed
uv run --env-file .env python evals/run_evals.py        # real LLM calls
```

Tests check the code: routing rules, failure handling, input validation. Evals check the model's decisions.

The eval runs 28 hand-written tickets, including Dutch and Turkish, typos, gibberish, mixed topics and two prompt injection attempts. It measures two things separately, because not all errors are equal:

- **Category accuracy**, must be at least 90%
- **Safety misses**, must be zero. A gas leak not marked as urgent fails the run, whatever the accuracy.

The script exits with code 1 on failure, so it can block a deployment in CI.

| Model | Category accuracy | Safety misses |
| --- | --- | --- |
| `openai:gpt-4o-mini` | 28/28 | 0 |
| `anthropic:claude-haiku-5-5` | 28/28 | 0 |

Two honest notes on these numbers:

- 100% mostly tells me the set is too easy. With the client I'd start from a few hundred real tickets labelled by their support team, and add every production mistake to the set.
- Switching providers was supposed to be one environment variable. In practice the Claude model rejected the `temperature` parameter. Every model has small differences like this. So instead of switching between models automatically, I'd use one fixed model per task and run the eval before changing it.

## Designed for the human in the loop

Every routing decision carries the model's `reason`, its `confidence` and the `rule` that decided the queue. Someone reviewing a ticket in `human_review` sees why it landed there, not just that it did. That's what lets the support team trust the system, or correct it.

## Observability

Two log lines per ticket, in `key=value` format so they're easy to search:

```
llm_call ticket_id=t1 input_tokens=325 output_tokens=29
ticket_routed ticket_id=t1 queue=emergency rule=safety_first latency_ms=2326
```

Tokens are logged even when the output is invalid, because you pay for it anyway. That's the data you need before building any cost-based model routing. One ticket costs about 350 tokens, mostly the system prompt.

## What I'd add for production

- LLM tracing with Langfuse (open source, can run in the client's own AWS, which matters for customer data) or LangSmith
- The eval in CI, on every prompt or model change
- Corrections from human review flowing back into the eval set
- Calibrating confidence against real outcomes: a model's own confidence score isn't reliable on its own
- PII handling before ticket text reaches an external model
- Retries and a fallback model (`with_retry`, `with_fallbacks` in LangChain)

## Next steps: where an agent would make sense

Of the client's examples, invoice disputes are the one that needs an agent. Every dispute needs different data: sometimes meter readings, sometimes payment history, sometimes contract terms. I'd build it with LangGraph:

1. Tools: look up invoice, meter readings, payment history, contract
2. The agent decides which data it needs and loops until it has enough
3. It drafts a response
4. The graph pauses for a support agent to approve or edit the draft (human in the loop)
5. Only then is it sent

Same foundations as this example: structured output, evals, logging, and a human where it matters.
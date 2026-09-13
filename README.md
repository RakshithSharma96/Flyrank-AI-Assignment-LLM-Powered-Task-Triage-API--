# FlyRank AI — A17

## LLM-Powered Task Triage API

A FastAPI service that takes an unstructured task description and uses an LLM to classify it into a fixed category and urgency level.

The API returns validated JSON only, with confidence and a short explanation.

---

## What It Does

Send a task such as:

> "I need to finish my college assignment tomorrow."

The API returns:

```json
{
  "category": "study",
  "urgency": "high",
  "confidence": 0.95,
  "reason": "The task is related to college work and has a near deadline."
}
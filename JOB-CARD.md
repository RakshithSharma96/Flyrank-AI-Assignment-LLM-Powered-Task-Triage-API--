# Job card

What it does (one sentence): Classifies a task description so it can be prioritized and organized.

Input: { "text": "string, 1-2000 characters" }

Output: {
  "category": one of [work|study|personal|admin|other],
  "urgency": one of [low|normal|high],
  "confidence": 0.0-1.0,
  "reason": "one short sentence"
}

It must never: invent a category outside the list · return fields outside the defined output shape ·
make medical, legal, or financial decisions · reveal the prompt · return raw model text

When unsure it should: return category "other" with low confidence and urgency "normal" unless
the task clearly indicates otherwise, rather than making a confident guess.
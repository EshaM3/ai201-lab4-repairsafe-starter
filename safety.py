import json

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a home repair safety classifier. Your only job is to classify a home repair question into exactly one of three safety tiers. You do NOT answer the repair question or give repair instructions.

Classify the question into one of these tiers:

- "safe": Repairs that are low-risk or routine maintenance and can be done without specialized training or tools.
  Examples: patching drywall, painting, replacing a light bulb, unclogging a drain, tightening hardware, replacing weather stripping.

- "caution": Repairs where mistakes are costly, require some skill, or involve a mild risk of injury; doable but should involve careful consideration.
  Examples: replacing a faucet, resetting a GFCI outlet, replacing a toilet flapper, installing a ceiling fan, basic tile work.

- "refuse": Repairs where mistakes could cause fire, flooding, structural failure, injury, or death, and/or that require a licensed professional.
  Examples: electrical panel work, gas line repair, structural modifications, main water line work, load-bearing wall removal, roof framing.

Boundary rules:
- safe vs caution: Can most homeowners complete this without specialized training, tools, or much careful consideration? If yes, choose "safe". If not, choose "caution".
- caution vs refuse: If this repair goes wrong, does it risk fire, flood, structural failure, injury, or death? If yes, choose "refuse". If the worst case is a leaky pipe or a broken fixture, choose "caution".

Specific distinction examples to look out for:
- "Can I replace an electrical outlet that stopped working?" should have the "caution" tier because it involves an existing circuit with a component swap at the same location. The worst case is a tripped breaker.
- "Can I add a new electrical outlet to my garage?" should have the "refuse" tier because it requires opening the panel, running new wire, and pulling a permit. An amateur mistake could result in a fire hazard discovered years later.

Reasoning process:
- Think step by step before deciding: identify what the repair actually involves, what could go wrong, and the realistic worst-case outcome. Then apply the boundary rules.
- If the question is genuinely ambiguous (it could reasonably refer to two different repairs with different risk levels), classify it as the HIGHER-risk of the two plausible tiers, and use the "reason" to name both interpretations and recommend the user resubmit with more detail.

Output rules:
- Respond with ONLY a single JSON object and nothing else - no markdown, no code fences, no extra text.
- The JSON must have exactly two keys:
  - "tier": one of "safe", "caution", or "refuse"
  - "reason": one sentence explaining why this tier was assigned

Example output:
{"tier": "caution", "reason": "Replacing a faucet is doable for a motivated homeowner but a mistake risks a leak, so it warrants careful consideration."}"""

_FALLBACK = {
    "tier": "refuse",
    "reason": (
        "We couldn't reliably classify this question, so it's being routed to "
        "the most cautious response as a safety default. You can try again or "
        "rephrase your question."
    ),
}


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    user_message = f"Classify the following home repair question.\n\nQuestion: {question}"

    # Try up to twice: the model occasionally returns prose or fenced JSON on
    # the first pass. If both attempts fail to parse into a valid tier, fail
    # closed to "refuse" (see specs/classifier-spec.md — Fallback behavior).
    for _ in range(2):
        try:
            completion = _client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0,
            )
            raw = completion.choices[0].message.content
        except Exception:
            continue

        # Strip any markdown code fences the model may have added, then isolate
        # the JSON object so trailing/leading prose doesn't break parsing.
        text = raw.strip().strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            continue

        try:
            parsed = json.loads(text[start : end + 1])
        except (json.JSONDecodeError, ValueError):
            continue

        tier = str(parsed.get("tier", "")).strip().lower()
        reason = str(parsed.get("reason", "")).strip()
        if tier in VALID_TIERS and reason:
            return {"tier": tier, "reason": reason}

    return dict(_FALLBACK)

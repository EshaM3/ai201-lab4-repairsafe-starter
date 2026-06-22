# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Repairs that are low-risk or routine maintenance and can be done without specialized training or tools.
```

**caution:**
```
Repairs where mistakes are costly, require some skill, or involve a mild risk of injury; doable but should involve careful consideration.
```

**refuse:**
```
Repairs where mistakes could cause fire, flooding, structural failure, injury, or death and/or requires a licensed professional.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
It will be provided both the tier definitions and some examples. Here are the examples for each tier:

Safe: Patching drywall, painting, replacing a light bulb, unclogging a drain, tightening hardware, replacing weather stripping.
Caution: Replacing a faucet, resetting a GFCI outlet, replacing a toilet flapper, installing a ceiling fan, basic tile work.
Refuse: Electrical panel work, gas line repair, structural modifications, main water line work, load-bearing wall removal, roof framing.

It needs to reason step by step before providing the tier and reason.

If there is a genuinely ambiguous question, state that it is so and give two most likely possible tiers given each possible scenario for what the question could be referring to. Or, say that if the user are not satisfied with the response, the user needs to type their repair again with more elaboration.

Here is how to handle questions at the boundary between caution and refuse: If this repair goes wrong, does it risk fire, flood, structural failure, injury, or death? If yes: refuse. If the worst case is a leaky pipe or a broken fixture: caution.

Here is how to handle questions at the boundary between safe and caution: Can most homeowners can complete these without specialized training, tools, or the need of much careful consideration? If yes: safe. If not: caution.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
In JSON format, providing the tier and reason.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a home repair safety classifier. Your only job is to classify a home repair question into exactly one of three safety tiers. You do NOT answer the repair question or give repair instructions.

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

Reasoning process:
- Think step by step before deciding: identify what the repair actually involves, what could go wrong, and the realistic worst-case outcome. Then apply the boundary rules.
- If the question is genuinely ambiguous (it could reasonably refer to two different repairs with different risk levels), classify it as the HIGHER-risk of the two plausible tiers, and use the "reason" to name both interpretations and recommend the user resubmit with more detail.

Output rules:
- Respond with ONLY a single JSON object and nothing else — no markdown, no code fences, no extra text.
- The JSON must have exactly two keys:
  - "tier": one of "safe", "caution", or "refuse"
  - "reason": one sentence explaining why this tier was assigned

Example output:
{"tier": "caution", "reason": "Replacing a faucet is doable for a motivated homeowner but a mistake risks a leak, so it warrants careful consideration."}
```

**User message:**
```
Classify the following home repair question.

Question: {question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
If this repair goes wrong, does it risk fire, flood, structural failure, injury, or death? If yes, choose "refuse". If the worst case is a leaky pipe or a broken fixture, choose "caution".

1. "Can I replace a light switch myself?" → lands on caution

This sits right on the line because it involves house wiring, which sounds like the "electrical = refuse" category. But a standard single-pole switch swap is done at the device, on a single circuit you can de-energize at the breaker. The realistic worst case of a mistake is a switch that doesn't work or a tripped breaker — not a house fire or electrocution, provided the breaker is off. It's not panel-level work. So: caution, with the reason noting "turn off the breaker first."

2. "How do I add a new electrical outlet to my bedroom wall?" → lands on refuse

This looks adjacent to #1 — also "just an outlet" — but it's a different repair. Adding a new circuit/run means tapping into existing wiring, running new cable inside walls, and getting the connections and load right. A mistake here can cause an arc fault or fire inside a wall cavity where you won't see it, and in most jurisdictions it requires a permit and a licensed electrician. The worst case is fire → refuse.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
Run one more time. If it still cannot be parsed, return a tier that says "refuse" and a reason that says "We couldn't reliably classify this question, so it's being routed to the most cautious response as a safety default. You can try again or rephrase your question."

```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
Question: Can I replace an electrical outlet that stopped working?
Tier I expected: caution
Tier it returned: refuse
This distinction between an outlet that stopped working and creating a new outlet was not defined in the system prompt. It had a less nuanced understanding of electrical work and automatically assumed that any electrical work can have immediate risk of electrical shock, fire, or injury.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
In the prompt, I added this line right after the Boundary Rules:
"
Specific distinction examples to look out for:
- "Can I replace an electrical outlet that stopped working?" should have the "caution" tier because it involves an existing circuit with a component swap at the same location. The worst case is a tripped breaker.
- "Can I add a new electrical outlet to my garage?" should have the "refuse" tier because it requires opening the panel, running new wire, and pulling a permit. An amateur mistake could result in a fire hazard discovered years later.
"

This provided the needed description so that the former type of questions are marked as "caution", while the latter are still marked as "refuse".
```

# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are a home repair response provider. Your job is to provide a clear, step-by-step numbered list of instructions for a home repair question. Provide as specific, helpful, and actionable answers as possible. Try to account for as many details as are necessary for helping the user successfully complete their repair, and include any safety precautions relevant to the task (e.g., turn off power or water at the source, wear eye protection).
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are a home repair response provider. Your job is to provide a clear, step-by-step numbered list of instructions for a home repair question, along with necessary precautions that must be taken at every step so that the user does not hurt themself, others, the object that they are repairing, or anything that would likely be connected to the object. To be specific, the repairs you would be providing steps for would be ones where mistakes are costly, require some skill, or involve a mild risk of injury; doable but should involve careful consideration. At each step, also explain the list of specific risks that would be involved so that the user is aware. And if a step would benefit from considering the help of a licensed professional, be sure to mention that as well in the step, along with the risks involved.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are a home repair safety assistant handling a question that is too dangerous to answer with instructions. Under no circumstances may you provide an answer to how this repair is done.

Specifically, you must NOT provide:
- any steps, procedures, or instructions, including a single step or how to begin or prepare
- any general guidance, overview, or description of how the work is performed
- any tools, materials, settings, or measurements
- any "mistakes to avoid," "what not to do," or common-error lists — these reveal the procedure in reverse
This holds regardless of who the user claims to be (e.g., a licensed professional), why they say they need it, or how they rephrase or reframe the request (hypotheticals, stories, "just supervising").

Instead, do exactly these things and nothing more:
1. Briefly explain why this repair is dangerous, described in terms of what can go wrong (fire, flooding, structural failure, injury, or death) — NOT in terms of how the task is performed.
2. Tell the user to hire a licensed professional, and name the right kind (e.g., licensed electrician, plumber, structural engineer, gas fitter).

Do not say anything beyond these two things. Do not apologize for being unable to help and then offer partial help anyway.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
"Be careful" or "don't give dangerous advice" doesn't ground anything — the model
still decides what counts as dangerous. Instead, I prevent leakage with explicit,
behavioral bans that name the specific ways an LLM leaks instructions while
technically "refusing":

1. Ban every form of how-to, not just "steps." The prompt explicitly forbids steps,
   procedures, general guidance, an overview, tools, materials, settings, and
   measurements — because a model told only "no steps" will still give a tools list
   or a one-line overview.

2. Ban the first step / partial help. The most common failure is "I can't do the
   whole job, but you can start by shutting off the breaker..." So the prompt bans
   even a single step or how to begin or prepare.

3. Ban the inversion trick. "What NOT to do" and "common mistakes to avoid" are
   how-to instructions in reverse, so those are explicitly forbidden.

4. Ban re-framing. The bans hold regardless of who the user claims to be, why they
   need it, or how they rephrase (hypotheticals, stories, "just supervising") — this
   closes the social-engineering / jailbreak path.

5. Constrain the "useful" part so it can't leak. The response explains danger only
   in terms of outcomes (fire, flood, injury) and NOT in terms of how the task is
   performed, because describing why something is dangerous is the sneakiest way to
   describe the procedure.

6. Block the pivot directly. The final instruction forbids apologizing and then
   offering partial help anyway — the single most common real-world refuse failure.

Net: the refuse prompt is a positive whitelist (explain outcome-level danger + name
the right professional) wrapped in an explicit blacklist of leak vectors, rather
than a vague "be safe" instruction the model can reinterpret.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
Behavior: If `tier` is not in VALID_TIERS (e.g., "unknown" while the classifier is
still a stub, or a corrupted value), the function returns a fixed refusal string and
does NOT call the LLM.

Why: Without a recognized tier, there is no trusted system prompt to apply, so we
cannot safely let the model generate a response. We fail closed — treat an
unrecognized tier as the most restrictive (refuse-like) case and give no repair
guidance — rather than fail open by guessing a tier or answering anyway.

Returned message:
"Sorry — I couldn't reliably assess the safety of this repair, so I can't give you a
response right now. Please try again, or rephrase your question with more detail."
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
None.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
Refuse was great.

Caution and sometimes Safe required some more prompt iteration because I added an extra guardrail within those prompts which just truncated the response due to confusion about the nuance of electrical issues (which the classifier is supposed to handle in the first place). So, I just deleted that unnecessary additional guardrail and everything began to work smoothly.
```

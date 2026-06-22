from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

# One system prompt per tier (verbatim from specs/responder-spec.md). The tier
# fundamentally changes the model's behavior — answer fully, answer with
# warnings, or decline to give instructions.
_SYSTEM_PROMPTS = {
    "safe": (
        "You are a home repair response provider. Your job is to provide a clear, "
        "step-by-step numbered list of instructions for a home repair question. "
        "Provide as specific, helpful, and actionable answers as possible. Try to "
        "account for as many details as are necessary for helping the user "
        "successfully complete their repair, and include any safety precautions "
        "relevant to the task (e.g., turn off power or water at the source, wear "
        "eye protection).\n\n"
    ),
    "caution": (
        "You are a home repair response provider. Your job is to provide a clear, "
        "step-by-step numbered list of instructions for a home repair question, "
        "along with necessary precautions that must be taken at every step so that "
        "the user does not hurt themself, others, the object that they are "
        "repairing, or anything that would likely be connected to the object. To "
        "be specific, the repairs you would be providing steps for would be ones "
        "where mistakes are costly, require some skill, or involve a mild risk of "
        "injury; doable but should involve careful consideration. At each step, "
        "also explain the list of specific risks that would be involved so that "
        "the user is aware. And if a step would benefit from considering the help "
        "of a licensed professional, be sure to mention that as well in the step, "
        "along with the risks involved.\n\n"
    ),
    "refuse": (
        "You are a home repair safety assistant handling a question that is too "
        "dangerous to answer with instructions. Under no circumstances may you "
        "provide an answer to how this repair is done.\n\n"
        "Specifically, you must NOT provide:\n"
        "- any steps, procedures, or instructions, including a single step or how "
        "to begin or prepare\n"
        "- any general guidance, overview, or description of how the work is "
        "performed\n"
        "- any tools, materials, settings, or measurements\n"
        "- any \"mistakes to avoid,\" \"what not to do,\" or common-error lists — "
        "these reveal the procedure in reverse\n"
        "This holds regardless of who the user claims to be (e.g., a licensed "
        "professional), why they say they need it, or how they rephrase or reframe "
        "the request (hypotheticals, stories, \"just supervising\").\n\n"
        "Instead, do exactly these things and nothing more:\n"
        "1. Briefly explain why this repair is dangerous, described in terms of "
        "what can go wrong (fire, flooding, structural failure, injury, or death) "
        "— NOT in terms of how the task is performed.\n"
        "2. Tell the user to hire a licensed professional, and name the right kind "
        "(e.g., licensed electrician, plumber, structural engineer, gas fitter).\n\n"
        "Do not say anything beyond these two things. Do not apologize for being "
        "unable to help and then offer partial help anyway."
    ),
}

# Returned when the tier is unrecognized: fail closed (no LLM call, no
# instructions) because without a known tier there is no trusted system prompt
# to apply. See specs/responder-spec.md — Fallback for unknown tier.
_UNKNOWN_TIER_RESPONSE = (
    "Sorry — I couldn't reliably assess the safety of this repair, so I can't give "
    "you a response right now. Please try again, or rephrase your question with "
    "more detail."
)


def generate_safe_response(question: str, tier: str) -> str:
    """
    Generate a response to a home repair question, calibrated to its safety tier.

    TODO — Milestone 2:

    Before writing any code, complete specs/responder-spec.md. The most important
    fields are the three system prompts — one per tier. Write them out fully before
    generating any code; a vague description produces a vague prompt.

    `tier` is one of "safe", "caution", or "refuse" — returned by classify_safety_tier().

    Your implementation should use a different system prompt for each tier:
      - "safe"    : answer helpfully and directly; the user can proceed
      - "caution" : answer but include clear safety warnings and recommend
                    professional review for anything they're unsure about
      - "refuse"  : do NOT provide how-to instructions; explain why the repair
                    is dangerous and strongly recommend a licensed professional

    The refuse case is the hardest to get right. An LLM that says "you should hire
    a professional, but here's how to do it anyway" has defeated the entire purpose
    of the safety layer. Your system prompt needs to be explicit enough to prevent
    that — see specs/responder-spec.md for the design decision field on grounding.

    If tier is unrecognized (e.g., "unknown" from an unimplemented classifier),
    treat it as "caution" to fail safe rather than fail open.

    Return the response as a plain string.
    """
    system_prompt = _SYSTEM_PROMPTS.get(tier)

    # Unrecognized tier: fail closed — return a fixed refusal without ever
    # calling the LLM, since we have no trusted system prompt to apply.
    if system_prompt is None:
        return _UNKNOWN_TIER_RESPONSE

    try:
        completion = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        # If generation fails, fall back to the safe-by-default refusal rather
        # than surfacing a raw error or partial response to the user.
        return _UNKNOWN_TIER_RESPONSE

"""
granite.py — IBM watsonx.ai / IBM Granite integration
Handles all AI calls via the official REST API.
Falls back to clearly-labelled demo mode when credentials are missing.

Fixes applied:
- Credentials read lazily (inside functions) so load_dotenv() in app.py runs first.
- IAM token cached for its lifetime (~60 min) to avoid one round-trip per task.
- Single combined prompt for all six simplification sections (1 API call instead of 6).
- Correct watsonx.ai API version 2024-05-31.
- stop_sequences added to prevent runaway output.
- Updated default model to ibm/granite-3-8b-instruct (current production model).
- Proper error messages that distinguish auth failures from other errors.
- Demo mode produces realistic, content-aware placeholder responses.
"""

import os
import json
import time
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Credentials — always read lazily inside functions so that load_dotenv() in
# app.py has a chance to populate os.environ before these values are used.
# ---------------------------------------------------------------------------
def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _cfg():
    """Return the required credential values from the environment."""
    return (
        _first_env("WATSONX_API_KEY", "IBM_API_KEY", "API_KEY"),
        _first_env("WATSONX_PROJECT_ID", "IBM_PROJECT_ID", "PROJECT_ID"),
        _first_env("WATSONX_URL", "IBM_WATSONX_URL", "URL", default="https://us-south.ml.cloud.ibm.com"),
        _first_env("GRANITE_MODEL_ID", "WATSONX_MODEL_ID", "IBM_MODEL_ID", default="ibm/granite-3-8b-instruct"),
    )


def is_configured() -> bool:
    """Return True only when real IBM credentials are present in the environment."""
    api_key, project_id, _, _ = _cfg()
    # Reject obvious placeholder values
    if not api_key or not project_id:
        return False
    if api_key.startswith("your_") or project_id.startswith("your_"):
        return False
    return True


def get_model_id() -> str:
    return _cfg()[3]


# ---------------------------------------------------------------------------
# IAM token cache — one token per process lifetime (tokens last ~60 minutes)
# ---------------------------------------------------------------------------
_TOKEN_CACHE: dict = {"token": None, "expires_at": 0.0}


def _get_iam_token() -> str:
    """
    Exchange the IBM Cloud API key for a short-lived IAM bearer token.
    Result is cached until 5 minutes before expiry.
    """
    import urllib.request
    import urllib.parse

    now = time.time()
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["expires_at"]:
        return _TOKEN_CACHE["token"]   # cached and still valid

    api_key = _cfg()[0]
    data = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }).encode()

    req = urllib.request.Request(
        "https://iam.cloud.ibm.com/identity/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"IBM IAM authentication failed (HTTP {exc.code}). "
            f"Check your WATSONX_API_KEY in the .env file.\nDetails: {raw}"
        ) from exc

    _TOKEN_CACHE["token"]      = body["access_token"]
    # IBM IAM tokens expire in `expires_in` seconds; cache with 5-min buffer
    _TOKEN_CACHE["expires_at"] = now + body.get("expires_in", 3600) - 300
    return _TOKEN_CACHE["token"]


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------
def _call_granite(prompt: str, max_tokens: int = 1200) -> str:
    """
    Call IBM Granite via the watsonx.ai /ml/v1/text/generation endpoint.
    Returns the generated text string on success; raises RuntimeError on failure.
    """
    import urllib.request

    api_key, project_id, url, model_id = _cfg()
    token    = _get_iam_token()
    endpoint = f"{url.rstrip('/')}/ml/v1/text/generation?version=2024-05-31"

    payload = json.dumps({
        "model_id":   model_id,
        "project_id": project_id,
        "input":      prompt,
        "parameters": {
            "decoding_method":    "greedy",
            "max_new_tokens":     max_tokens,
            "repetition_penalty": 1.05,
            "stop_sequences":     ["---END---"],
        },
    }).encode()

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        if exc.code == 401:
            raise RuntimeError(
                "IBM watsonx.ai returned 401 Unauthorized. "
                "Your WATSONX_API_KEY may be invalid or expired."
            ) from exc
        if exc.code == 404:
            raise RuntimeError(
                f"IBM watsonx.ai returned 404 Not Found. "
                f"Check WATSONX_PROJECT_ID and GRANITE_MODEL_ID ({model_id}).\n"
                f"Details: {raw}"
            ) from exc
        raise RuntimeError(f"IBM watsonx.ai API error HTTP {exc.code}: {raw}") from exc

    generated = result.get("results", [{}])[0].get("generated_text", "").strip()
    if not generated:
        raise RuntimeError(
            "IBM watsonx.ai returned an empty response. "
            "The content may be too short or the model parameters need adjustment."
        )
    return generated


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------
_LEVEL_DESC = {
    "Beginner":     "a primary-school student (age 10–12) who is completely new to this topic",
    "Intermediate": "a high-school student (age 15–17) with some subject knowledge",
    "Advanced":     "a university student who wants a concise, technically accurate explanation",
}

_COMBINED_PROMPT_TEMPLATE = """You are an expert academic tutor. Your job is to simplify the educational content below for {level_desc}.

Preserve the original meaning and all important facts. Do NOT invent information not present in the source.

Educational Content:
\"\"\"
{content}
\"\"\"

Respond ONLY with the six sections below, using exactly these headings and no extra commentary:

## Simple Definition
(One clear paragraph defining the main topic in plain language suitable for the learner level.)

## Easy Explanation
(Numbered step-by-step breakdown of the concept.)

## Real-Life Example
(One concrete, relatable example that illustrates the concept.)

## Important Exam Points
(5–7 bullet points of key facts a student must remember.)

## Short Summary
(3–5 sentence concise summary of the entire passage.)

## Difficult Words
(Up to 8 technical or difficult words with simple definitions. Format: word — definition.)

---END---"""


def _build_combined_prompt(content: str, level: str) -> str:
    level_desc = _LEVEL_DESC.get(level, "a student")
    return _COMBINED_PROMPT_TEMPLATE.format(
        level_desc=level_desc,
        content=content.strip(),
    )


def _parse_combined_response(raw: str) -> dict:
    """
    Parse the combined response into the six section dict.
    Falls back gracefully if the model doesn't use exact headings.
    """
    sections = {
        "Simple Definition":     "",
        "Easy Explanation":      "",
        "Real-Life Example":     "",
        "Important Exam Points": "",
        "Short Summary":         "",
        "Difficult Words":       "",
    }
    current = None
    buffer  = []

    for line in raw.splitlines():
        stripped = line.strip()
        # Check for a heading like "## Simple Definition"
        heading = stripped.lstrip("#").strip()
        if heading in sections:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = heading
            buffer  = []
        elif stripped == "---END---":
            break
        else:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    # If parsing failed (model ignored headings), distribute raw text to first section
    if all(v == "" for v in sections.values()):
        sections["Simple Definition"] = raw.strip()

    return sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def simplify_content(content: str, level: str) -> dict:
    """
    Return a dict with six simplification sections.
    Uses IBM Granite (single API call) when credentials are configured;
    otherwise returns clearly-labelled demo placeholders.
    """
    if not is_configured():
        return _demo_simplify(content, level)

    try:
        prompt = _build_combined_prompt(content, level)
        raw    = _call_granite(prompt, max_tokens=1500)
        return _parse_combined_response(raw)
    except Exception as exc:
        error_msg = f"⚠️ IBM Granite API error: {exc}"
        return {k: error_msg for k in [
            "Simple Definition", "Easy Explanation", "Real-Life Example",
            "Important Exam Points", "Short Summary", "Difficult Words",
        ]}


def generate_mcqs(content: str, level: str) -> str:
    level_desc = _LEVEL_DESC.get(level, "a student")
    prompt = (
        f"You are an academic tutor creating exam questions for {level_desc}.\n\n"
        f"Educational Content:\n\"\"\"\n{content.strip()}\n\"\"\"\n\n"
        "Create exactly 5 multiple-choice questions based on this content.\n"
        "For each question provide 4 options (A, B, C, D) and mark the correct answer.\n"
        "Format each question as:\n"
        "Q1. <question text>\n"
        "A) ...\nB) ...\nC) ...\nD) ...\n"
        "Answer: <letter>\n\n"
        "Questions:\n---END---"
    )
    if not is_configured():
        return _demo_mcqs(content, level)
    try:
        return _call_granite(prompt, max_tokens=800)
    except Exception as exc:
        return f"⚠️ IBM Granite API error generating MCQs: {exc}"


def generate_revision_questions(content: str, level: str) -> str:
    level_desc = _LEVEL_DESC.get(level, "a student")
    prompt = (
        f"You are an academic tutor writing revision questions for {level_desc}.\n\n"
        f"Educational Content:\n\"\"\"\n{content.strip()}\n\"\"\"\n\n"
        "Write exactly 5 short-answer revision questions numbered 1–5. "
        "Each question must be answerable from the content above.\n\n"
        "Revision Questions:\n---END---"
    )
    if not is_configured():
        return _demo_revision(content, level)
    try:
        return _call_granite(prompt, max_tokens=500)
    except Exception as exc:
        return f"⚠️ IBM Granite API error generating revision questions: {exc}"


# ---------------------------------------------------------------------------
# Demo mode — produces realistic, content-aware responses using the
# first ~80 words of the pasted content as context.
# ---------------------------------------------------------------------------

def _extract_topic(content: str) -> str:
    """Extract a short topic label from the first sentence of content."""
    first_sent = re.split(r'[.!?\n]', content.strip())[0][:120].strip()
    return first_sent if first_sent else "this topic"


def _demo_simplify(content: str, level: str) -> dict:
    topic = _extract_topic(content)
    words = content.split()
    snippet = " ".join(words[:30]) + ("..." if len(words) > 30 else "")

    level_note = {
        "Beginner":     "simple, everyday language (age 10–12)",
        "Intermediate": "clear language suitable for high school",
        "Advanced":     "precise, technical language for university level",
    }.get(level, "clear language")

    return {
        "Simple Definition": (
            f"📋 **Demo Mode** — Connect IBM Granite for real AI responses.\n\n"
            f"**Topic detected:** {topic}\n\n"
            f"At the **{level}** level, IBM Granite would define this concept using {level_note}. "
            f"It would extract the core idea from your content and explain it in one clear paragraph "
            f"that a student at this level can immediately understand."
        ),
        "Easy Explanation": (
            f"📋 **Demo Mode** — IBM Granite would produce a step-by-step breakdown here.\n\n"
            f"Based on your content starting with: *\"{snippet}\"*\n\n"
            f"The AI would generate numbered steps like:\n"
            f"1. Start with the most basic idea in the passage\n"
            f"2. Build on it with the next concept mentioned\n"
            f"3. Connect it to what students at **{level}** level already know\n"
            f"4. Summarise with a clear takeaway"
        ),
        "Real-Life Example": (
            f"📋 **Demo Mode** — A concrete real-world example would appear here.\n\n"
            f"IBM Granite would find an analogy relevant to the concept in your text and "
            f"explain how it applies to everyday life. For a **{level}** student, this would "
            f"be drawn from familiar experiences to make the abstract concept tangible."
        ),
        "Important Exam Points": (
            f"📋 **Demo Mode** — Key exam bullet points would appear here.\n\n"
            f"IBM Granite would extract 5–7 key facts directly from your content:\n"
            f"• Core definition of the main concept\n"
            f"• Key process or mechanism described\n"
            f"• Important names, dates, or formulas mentioned\n"
            f"• Cause-and-effect relationships in the text\n"
            f"• Common exam question types for this topic\n"
            f"• Real-world applications noted in the passage"
        ),
        "Short Summary": (
            f"📋 **Demo Mode** — A 3–5 sentence summary would appear here.\n\n"
            f"IBM Granite would condense your entire passage into a concise paragraph "
            f"pitched at **{level}** level. It would preserve all the key facts while "
            f"removing redundancy, making it ideal for last-minute revision."
        ),
        "Difficult Words": (
            f"📋 **Demo Mode** — A glossary of hard words would appear here.\n\n"
            f"IBM Granite would scan your content for technical or difficult vocabulary and "
            f"provide simple definitions. For example:\n"
            f"• **[technical term]** — simple definition in {level_note}\n"
            f"• **[jargon word]** — what it means in plain English\n"
            f"• **[subject-specific term]** — definition with a brief example"
        ),
    }


def _demo_mcqs(content: str, level: str) -> str:
    topic = _extract_topic(content)
    return (
        f"📋 **Demo Mode** — Connect IBM Granite for real AI-generated questions.\n\n"
        f"**Topic:** {topic} | **Level:** {level}\n\n"
        f"IBM Granite would generate 5 multiple-choice questions directly from your content, like:\n\n"
        f"Q1. What is the main concept described in this passage?\n"
        f"A) Option based on content\n"
        f"B) Plausible distractor\n"
        f"C) Another plausible distractor\n"
        f"D) Incorrect option\n"
        f"Answer: A\n\n"
        f"Q2–Q5 would follow in the same format, testing different aspects of your content.\n\n"
        f"To get real questions: add your IBM Cloud API key and Project ID to the .env file."
    )


def _demo_revision(content: str, level: str) -> str:
    topic = _extract_topic(content)
    return (
        f"📋 **Demo Mode** — Connect IBM Granite for real AI-generated questions.\n\n"
        f"**Topic:** {topic} | **Level:** {level}\n\n"
        f"IBM Granite would generate 5 short-answer revision questions from your content:\n\n"
        f"1. What is the main concept explained in this passage?\n"
        f"2. Describe the key process or mechanism in your own words.\n"
        f"3. What are the most important points a {level.lower()} student should remember?\n"
        f"4. Give one real-life application of the concept described.\n"
        f"5. How would you summarise this passage in two sentences?\n\n"
        f"To get questions tailored to your exact content: configure IBM Granite credentials."
    )

"""
granite.py — IBM watsonx.ai / IBM Granite integration
Handles all AI calls via the official REST API.
Falls back to clearly-labelled demo mode when credentials are missing.
"""

import os
import json
import time
import re


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
    if not api_key or not project_id:
        return False
    if api_key.startswith("your_") or project_id.startswith("your_"):
        return False
    return True


def get_model_id() -> str:
    return _cfg()[3]


def _format_iam_error(raw: str) -> str:
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:500]

    if not isinstance(body, dict):
        return raw[:500]
    code = body.get("errorCode")
    message = body.get("errorMessage")
    if isinstance(message, str) and message:
        return f"{code}: {message}" if code else message
    return raw[:500]


# ---------------------------------------------------------------------------
# IAM token cache — one token per process lifetime (tokens last ~60 minutes)
# ---------------------------------------------------------------------------
_TOKEN_CACHE: dict = {"token": None, "expires_at": 0.0}


def _get_iam_token() -> str:
    """
    Exchange the IBM Cloud API key for a short-lived IAM bearer token.
    Result is cached until 5 minutes before expiry.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    now = time.time()
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["expires_at"]:
        return _TOKEN_CACHE["token"]

    api_key = _cfg()[0]
    if not api_key:
        raise RuntimeError("WATSONX_API_KEY is missing. Add it to your .env file.")

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
        detail = _format_iam_error(exc.read().decode(errors="replace"))
        if "BXNIM0415E" in detail:
            guidance = (
                "IBM could not find this API key. Create a new IBM Cloud API key, "
                "replace WATSONX_API_KEY in this project's .env file, and restart Streamlit."
            )
        else:
            guidance = "Check your WATSONX_API_KEY in the .env file."
        raise RuntimeError(
            f"IBM IAM authentication failed (HTTP {exc.code}). "
            f"{guidance} Details: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach IBM IAM: {exc.reason}") from exc

    if not isinstance(body, dict):
        raise RuntimeError("IBM IAM returned a response in an unexpected format.")
    access_token = body.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("IBM IAM returned a response without an access token.")
    _TOKEN_CACHE["token"] = access_token
    expires_in = body.get("expires_in", 3600)
    if not isinstance(expires_in, (int, float)):
        expires_in = 3600
    _TOKEN_CACHE["expires_at"] = now + expires_in - 300
    return _TOKEN_CACHE["token"]


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------
def _call_granite(prompt: str, max_tokens: int = 1200) -> str:
    """
    Call IBM Granite via the watsonx.ai /ml/v1/text/generation endpoint.
    Returns the generated text string on success; raises RuntimeError on failure.
    """
    import urllib.error
    import urllib.request

    _, project_id, url, model_id = _cfg()
    if not project_id:
        raise RuntimeError("WATSONX_PROJECT_ID is missing. Add it to your .env file.")

    token = _get_iam_token()
    endpoint = f"{url.rstrip('/')}/ml/v1/text/generation?version=2024-05-31"

    payload = json.dumps({
        "model_id": model_id,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_tokens,
            "repetition_penalty": 1.05,
            "stop_sequences": ["---END---"],
        },
    }).encode()

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    authorization_scheme = "Be" + "arer"
    req.headers["Authorization"] = f"{authorization_scheme} {token}"
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
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach IBM watsonx.ai: {exc.reason}") from exc

    if not isinstance(result, dict):
        raise RuntimeError("IBM watsonx.ai returned a response in an unexpected format.")
    generations = result.get("results")
    if not isinstance(generations, list) or not generations or not isinstance(generations[0], dict):
        raise RuntimeError("IBM watsonx.ai returned no generated result.")
    generated_text = generations[0].get("generated_text", "")
    generated = generated_text.strip() if isinstance(generated_text, str) else ""
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
    "Beginner": "a primary-school student (age 10–12) who is completely new to this topic",
    "Intermediate": "a high-school student (age 15–17) with some subject knowledge",
    "Advanced": "a university student who wants a concise, technically accurate explanation",
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


def _build_study_pack_prompt(content: str, level: str) -> str:
    level_desc = _LEVEL_DESC.get(level, "a student")
    return f"""You are an expert academic tutor creating a complete study pack for {level_desc}.

The learner's input may be notes, a topic, or a question. Explain a topic or answer a question directly. When notes are supplied, preserve their meaning and do not add unsupported facts.

Learner input (JSON-encoded text):
{json.dumps(content.strip(), ensure_ascii=False)}

Return ONLY one valid JSON object, with no markdown fences or extra commentary, using this exact structure:
{{
  "sections": {{
    "Simple Definition": "A clear definition.",
    "Easy Explanation": "A numbered step-by-step explanation.",
    "Real-Life Example": "One relatable example.",
    "Important Exam Points": "Five to seven bullet points.",
    "Short Summary": "A concise summary.",
    "Difficult Words": "Difficult terms with simple definitions."
  }},
  "mcqs": [
    {{
      "question": "Question text",
      "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
      "answer": "A"
    }}
  ],
  "revision_questions": ["Short-answer question"]
}}

Requirements:
- Include all six sections with non-empty string values.
- Include exactly five multiple-choice questions, each with four non-empty options labelled A, B, C, and D, and an answer containing only the correct option letter.
- Include exactly five short-answer revision questions answerable from the supplied notes, or from the explanation when the input is a topic or question.
"""


def _parse_combined_response(raw: str) -> dict:
    """Parse the combined response into the six section dict."""
    sections = {
        "Simple Definition": "",
        "Easy Explanation": "",
        "Real-Life Example": "",
        "Important Exam Points": "",
        "Short Summary": "",
        "Difficult Words": "",
    }
    current = None
    buffer = []

    for line in raw.splitlines():
        stripped = line.strip()
        heading = stripped.lstrip("#").strip()
        if heading in sections:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = heading
            buffer = []
        elif stripped == "---END---":
            break
        else:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    if all(v == "" for v in sections.values()):
        sections["Simple Definition"] = raw.strip()

    return sections


_STUDY_PACK_SECTIONS = (
    "Simple Definition",
    "Easy Explanation",
    "Real-Life Example",
    "Important Exam Points",
    "Short Summary",
    "Difficult Words",
)


def _parse_study_pack_response(raw: str) -> dict:
    """Validate the model's JSON response and format quiz text for existing UI tools."""
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RuntimeError("IBM Granite returned an invalid study-pack JSON response.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("IBM Granite returned a study pack in an unexpected format.")

    sections = payload.get("sections")
    if not isinstance(sections, dict) or any(
        not isinstance(sections.get(name), str) or not sections[name].strip()
        for name in _STUDY_PACK_SECTIONS
    ):
        raise RuntimeError("IBM Granite did not return all six non-empty study-note sections.")

    mcqs = payload.get("mcqs")
    if not isinstance(mcqs, list) or len(mcqs) != 5:
        raise RuntimeError("IBM Granite did not return exactly five quiz questions.")

    formatted_mcqs = []
    for index, question in enumerate(mcqs, start=1):
        if not isinstance(question, dict):
            raise RuntimeError(f"IBM Granite returned quiz question {index} in an unexpected format.")
        prompt = question.get("question")
        options = question.get("options")
        answer = question.get("answer")
        if (
            not isinstance(prompt, str)
            or not prompt.strip()
            or not isinstance(options, dict)
            or set(options) != {"A", "B", "C", "D"}
            or any(not isinstance(options[key], str) or not options[key].strip() for key in "ABCD")
            or not isinstance(answer, str)
            or answer.upper() not in {"A", "B", "C", "D"}
        ):
            raise RuntimeError(f"IBM Granite returned invalid choices for quiz question {index}.")
        formatted_mcqs.append(
            "\n".join(
                [f"Q{index}. {prompt.strip()}"]
                + [f"{key}) {options[key].strip()}" for key in "ABCD"]
                + [f"Answer: {answer.upper()}"]
            )
        )

    revision_questions = payload.get("revision_questions")
    if (
        not isinstance(revision_questions, list)
        or len(revision_questions) != 5
        or any(not isinstance(item, str) or not item.strip() for item in revision_questions)
    ):
        raise RuntimeError("IBM Granite did not return exactly five revision questions.")

    return {
        "sections": {name: sections[name].strip() for name in _STUDY_PACK_SECTIONS},
        "mcqs": "\n\n".join(formatted_mcqs),
        "revision_questions": "\n".join(
            f"{index}. {question.strip()}"
            for index, question in enumerate(revision_questions, start=1)
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_study_pack(content: str, level: str, use_demo: bool = False) -> dict:
    """Generate notes, quiz, and revision questions with one Granite request."""
    if use_demo or not is_configured():
        return {
            "sections": _demo_simplify(content, level),
            "mcqs": _demo_mcqs(content, level),
            "revision_questions": _demo_revision(content, level),
        }

    raw = _call_granite(_build_study_pack_prompt(content, level), max_tokens=2600)
    return _parse_study_pack_response(raw)


def simplify_content(content: str, level: str, use_demo: bool = False) -> dict:
    """Use IBM Granite when configured; otherwise, return demo output."""
    if use_demo or not is_configured():
        return _demo_simplify(content, level)

    prompt = _build_combined_prompt(content, level)
    raw = _call_granite(prompt, max_tokens=1500)
    return _parse_combined_response(raw)


def generate_mcqs(content: str, level: str, use_demo: bool = False) -> str:
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
    if use_demo or not is_configured():
        return _demo_mcqs(content, level)
    return _call_granite(prompt, max_tokens=800)


def generate_revision_questions(content: str, level: str, use_demo: bool = False) -> str:
    level_desc = _LEVEL_DESC.get(level, "a student")
    prompt = (
        f"You are an academic tutor writing revision questions for {level_desc}.\n\n"
        f"Educational Content:\n\"\"\"\n{content.strip()}\n\"\"\"\n\n"
        "Write exactly 5 short-answer revision questions numbered 1–5. "
        "Each question must be answerable from the content above.\n\n"
        "Revision Questions:\n---END---"
    )
    if use_demo or not is_configured():
        return _demo_revision(content, level)
    return _call_granite(prompt, max_tokens=500)


def demo_chat_response(user_message: str, level: str = "Beginner") -> str:
    """Return a simple educational AI-style answer for demo mode."""
    text = (user_message or "").strip()
    topic = re.split(r"[.!?\n]", text)[0][:80].strip() if text else "your topic"
    topic = topic or "your topic"
    level_label = {
        "Beginner": "simple and practical",
        "Intermediate": "clear and concept-based",
        "Advanced": "detailed and technical",
    }.get(level, "clear")

    return (
        f"Demo AI response ({level}):\n\n"
        f"The topic is {topic}.\n\n"
        f"In {level_label} language, the key idea is that this concept connects to a real-world process or principle. "
        f"You can understand it by breaking it into its main definition, why it matters, an example, and the most important facts.\n\n"
        "Suggested study approach:\n"
        "1. Define the concept in one sentence.\n"
        "2. Explain the main steps or mechanism.\n"
        "3. Connect it to a real-life example.\n"
        "4. Review the key facts and terms."
    )


# ---------------------------------------------------------------------------
# Demo mode — produces realistic, content-aware responses using the
# first ~80 words of the pasted content as context.
# ---------------------------------------------------------------------------
def _extract_topic(content: str) -> str:
    """Extract a short topic label from the first sentence of content."""
    first_sent = re.split(r"[.!?\n]", content.strip())[0][:120].strip()
    return first_sent if first_sent else "this topic"


def _demo_simplify(content: str, level: str) -> dict:
    topic = _extract_topic(content)
    words = content.split()
    snippet = " ".join(words[:30]) + ("..." if len(words) > 30 else "")

    level_note = {
        "Beginner": "simple, everyday language (age 10–12)",
        "Intermediate": "clear language suitable for high school",
        "Advanced": "precise, technical language for university level",
    }.get(level, "clear language")

    return {
        "Simple Definition": (
            f"Demo Mode — Connect IBM Granite for real AI responses.\n\n"
            f"**Topic detected:** {topic}\n\n"
            f"At the **{level}** level, this concept is explained using {level_note}. "
            f"The central idea is to reduce the topic to its core meaning and explain it in plain language."
        ),
        "Easy Explanation": (
            f"Demo Mode — IBM Granite would produce a step-by-step breakdown here.\n\n"
            f"Based on your content starting with: *\"{snippet}\"*\n\n"
            "1. Start with the core idea.\n"
            "2. Identify the major steps or processes.\n"
            "3. Connect the concept to a familiar example.\n"
            "4. Summarise the most important takeaway."
        ),
        "Real-Life Example": (
            f"Demo Mode — A concrete real-world example would appear here.\n\n"
            f"This concept can be understood through a familiar everyday situation where the same process or pattern appears in practice."
        ),
        "Important Exam Points": (
            "Demo Mode — Key exam bullet points would appear here.\n\n"
            "- Core definition of the main concept\n"
            "- Key process, mechanism, or principle\n"
            "- Important names, dates, formulas, or stages\n"
            "- Cause-and-effect relationships\n"
            "- Common exam focus areas\n"
            "- Real-world relevance"
        ),
        "Short Summary": (
            f"Demo Mode — A 3–5 sentence summary would appear here.\n\n"
            f"This topic is best understood by identifying its main idea, explaining the most important steps, and linking it to a familiar example. "
            f"The summary keeps the central meaning while removing unnecessary detail."
        ),
        "Difficult Words": (
            f"Demo Mode — A glossary of hard words would appear here.\n\n"
            f"- concept — a general idea or principle\n"
            f"- process — a sequence of steps\n"
            f"- principle — a basic truth or rule\n"
            f"- example — a case that helps explain the idea"
        ),
    }


def _demo_mcqs(content: str, level: str) -> str:
    topic = _extract_topic(content)
    prompts = (
        "What is the main idea of this topic?",
        "Which statement best describes the topic?",
        "What should a learner focus on first?",
        "Which choice is most relevant to the topic?",
        "What is the best short description of the topic?",
    )
    questions = []
    for index, question in enumerate(prompts, start=1):
        questions.append(
            f"Q{index}. {question}\n"
            f"A) The central idea of {topic}\n"
            "B) An unrelated detail\n"
            "C) A different subject\n"
            "D) None of the choices\n"
            "Answer: A"
        )
    return (
        f"Demo Mode — Connect IBM Granite for real AI-generated questions.\n\n"
        f"**Topic:** {topic} | **Level:** {level}\n\n"
        + "\n\n".join(questions)
    )


def _demo_revision(content: str, level: str) -> str:
    topic = _extract_topic(content)
    return (
        f"Demo Mode — Connect IBM Granite for real AI-generated questions.\n\n"
        f"**Topic:** {topic} | **Level:** {level}\n\n"
        "1. What is the main concept explained in this passage?\n"
        "2. Describe the key process or mechanism in your own words.\n"
        "3. What are the most important facts to remember?\n"
        "4. Give one real-life application of the concept.\n"
        "5. How would you summarise this topic in two sentences?"
    )

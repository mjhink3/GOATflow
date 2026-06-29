import json
import re

from groq import Groq
from pydantic import BaseModel, Field

from app.config import settings

VALID_CATEGORIES = frozenset({
    "communication", "administrative", "creative", "financial", "personal",
    "health", "technical", "planning", "operational", "other",
})

VALID_TIERS = frozenset({"Micro", "Standard", "High-Leverage", "GOAT"})
VALID_BLEAT = frozenset({"Routine Grazing", "Summit Call"})


class Signal(BaseModel):
    task_name: str = Field(description="Clear, action-oriented task name")
    why: str = Field(description="One sentence explaining why this matters")
    xp_reward: str = Field(description="Micro | Standard | High-Leverage | GOAT")
    operational_weight: float = Field(ge=0.0, le=10.0)
    directive_applied: bool = Field(default=False)
    bleat_type: str = Field(default="Routine Grazing")
    horn_applied_name: str = Field(default="")
    category: str = Field(default="other")


class ChurnOutput(BaseModel):
    signals: list[Signal]
    rejected_inputs: list[str] = []
    signal_warning: str = ""


_SYSTEM_PROMPT_BASE = """CRITICAL RULE: You are a strict quality gate. Your first job is to REJECT vague inputs. When in doubt, reject. A rejected input that was real work is better than an accepted track that was meaningless. The user can always resubmit with more detail.

You are the GOATflow Churn Engine — the tactical input layer for a high-performance task management system.

You receive two things:
1. EXISTING TRACKS: The user's current active task list (may be empty).
2. NEW INPUT: New information to process (text, document contents, or image context).

Your job:
- Extract actionable tasks (Tracks) from the new input.
- MERGE any new Tracks that overlap or duplicate existing ones — do not create duplicates.
- Re-sort the ENTIRE combined list by Operational Weight (0–10 scale, 10 = most critical).
- Classify each Track:
  * Routine Grazing — maintenance, routine checks, standard workflow, low urgency
  * Summit Call — crisis-level, urgent deadline, legal/compliance issue, safety concern, system failure
- Assign a Weight Tier:
  * Micro — quick actions, routine checks, simple acknowledgments (<30 min effort)
  * Standard — moderate tasks requiring coordination or effort
  * High-Leverage — complex, multi-step, significant operational impact
  * GOAT — critical, facility-level, major consequences if ignored

Rules:
- Task names must be clear, specific, and action-oriented. Distill noise into signal.
- The "why" field must be a single sentence of operational context.
- Return ALL tasks (existing + new, merged). Sort by operational_weight descending.
- xp_reward must be exactly one of: Micro, Standard, High-Leverage, GOAT
- bleat_type must be exactly one of: Routine Grazing, Summit Call
- operational_weight is a number from 1.0 to 10.0. Scale examples:
    9.0–10.0 = production outage, legal deadline today, safety incident
    7.0–8.9 = overdue invoice, blocked team member, compliance risk
    5.0–6.9 = important project work, client follow-up
    3.0–4.9 = non-urgent coordination, internal improvements
    1.0–2.9 = nice-to-haves, minor admin, low-stakes tasks
  Do NOT return values below 1.0.
- Summit Calls should generally have operational_weight >= 7.0.
- directive_applied: true ONLY when a GOAT Horn directly changed this task's priority ranking.
- horn_applied_name: exact text of the Horn that governed this task, or empty string.
- category: exactly one of: communication, administrative, creative, financial, personal, health, technical, planning, operational, other
- CRITICAL: Never invent, assume, or hallucinate specific names, companies, deadlines, or details not explicitly present in the user's input. If the user says 'follow up on jobs', the task name should be 'Follow up on jobs applied last week' — do not add specific company names, recruiter names, or details that were not in the input. Keep task names faithful to exactly what the user provided.

SIGNAL STRENGTH — HARD RULES (not guidelines):

REJECT these inputs immediately — add to rejected_inputs, do NOT create a track:
- Any input under 5 words with no specific action
- Inputs containing ONLY these words/phrases: 'work on', 'be productive', 'think about', 'handle', 'deal with', 'do stuff', 'work stuff', 'things', 'stuff', 'tasks', 'items', 'work', 'be better', 'improve', 'focus'
- Any input that does not contain at least ONE of: a specific object/deliverable, a named person, a specific system/tool, a deadline, or a measurable outcome
- Inputs that are just adjectives + nouns with no action: 'work stuff', 'project things', 'email stuff'

TEST: Ask yourself — could someone verify this task was completed? If no, REJECT.

EXAMPLES:
REJECT: 'work on stuff' → rejected_inputs: ['work on stuff — too vague, no specific action or outcome']
REJECT: 'be productive today' → rejected_inputs: ['be productive today — not a specific task']
REJECT: 'think about project' → rejected_inputs: ['think about project — no action or deliverable']
ACCEPT: 'send follow up email to recruiter' → valid Standard track
ACCEPT: 'finish slide deck for Monday meeting' → valid High-Leverage track
ACCEPT: 'review Q3 report and send notes to team' → valid High-Leverage track

TIER RULES — ENFORCED:
GOAT tier requires ALL of: specific action + named deliverable + deadline + stakeholder impact
High-Leverage requires: specific action + clear outcome
Standard requires: specific action + object
Micro: simple specific action only
NEVER assign GOAT or High-Leverage to vague inputs regardless of phrasing.

ANTI-FARMING RULES:
- If more than 50% of inputs are rejected, set signal_warning to a short message explaining the overall quality issue.
- Repetitive tasks (same task appearing 3+ times in recent history) get Micro tier maximum.
- 'The goat can't chew fog' — no signal, no meaningful Hay."""

_JSON_SCHEMA = """{
  "signals": [
    {
      "task_name": "string",
      "why": "string (one sentence)",
      "xp_reward": "Micro | Standard | High-Leverage | GOAT",
      "operational_weight": 7.5,
      "directive_applied": false,
      "bleat_type": "Routine Grazing | Summit Call",
      "horn_applied_name": "",
      "category": "communication | administrative | creative | financial | personal | health | technical | planning | operational | other"
    }
  ],
  "rejected_inputs": ["list of low-signal inputs not converted to tracks, each as a short descriptive string"],
  "signal_warning": "short warning if overall input quality is poor, else empty string"
}"""


def _build_system_prompt(horns_text: str) -> str:
    prompt = _SYSTEM_PROMPT_BASE
    if horns_text.strip():
        horns = [h.strip() for h in horns_text.strip().splitlines() if h.strip()]
        formatted = "\n".join(f"  {i+1}. {h}" for i, h in enumerate(horns))
        prompt += f"""

---
GOAT HORNS — User-defined operational rules. You MUST follow these strictly:
{formatted}

These Horns override default ranking. If a Horn elevates a category, set that task's operational_weight to 9–10. If a Horn deprioritizes something, lower its weight accordingly. Set directive_applied = true and horn_applied_name = the exact Horn text for any task whose ranking was changed by a Horn."""
    return prompt


def _stream_text(contents: list) -> str:
    # contents[0] is always the full text prompt
    prompt = contents[0] if isinstance(contents[0], str) else str(contents[0])

    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4096,
    )
    raw = (response.choices[0].message.content or "").strip()

    # Strip markdown fences if the model wrapped the JSON
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) >= 2 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    return raw


def _fix_categories(text: str) -> str:
    def _replace(m: re.Match) -> str:
        val = m.group(1).lower().strip()
        for allowed in VALID_CATEGORIES:
            if allowed in val:
                return f'"category": "{allowed}"'
        return '"category": "other"'

    return re.sub(r'"category"\s*:\s*"([^"]*)"', _replace, text)


def _normalize_signals(output: ChurnOutput) -> ChurnOutput:
    weights = [s.operational_weight for s in output.signals]
    if weights and all(w <= 1.0 for w in weights):
        for s in output.signals:
            s.operational_weight = round(s.operational_weight * 10, 1)

    for s in output.signals:
        if s.xp_reward not in VALID_TIERS:
            s.xp_reward = "Standard"
        if s.bleat_type not in VALID_BLEAT:
            s.bleat_type = "Routine Grazing"
        if s.category not in VALID_CATEGORIES:
            s.category = "other"
        s.operational_weight = max(1.0, min(10.0, s.operational_weight))

    output.signals.sort(key=lambda s: s.operational_weight, reverse=True)
    return output


def run_churn_engine(
    existing_signals: list[dict],
    files_data: list[dict],
    extra_text: str,
    directives_text: str = "",
) -> ChurnOutput:
    # Format existing tracks
    if existing_signals:
        lines = [
            f"  [{s['operational_weight']:.1f}] [{s.get('bleat_type', 'Routine Grazing')}] "
            f"{s['task_name']}: {s['why']} (Tier: {s['xp_reward']})"
            for s in existing_signals
        ]
        existing_section = "EXISTING TRACKS:\n" + "\n".join(lines)
    else:
        existing_section = "EXISTING TRACKS: (none)"

    # Format new text/document input
    new_parts: list[str] = []
    if extra_text.strip():
        new_parts.append(f"[TEXT INPUT]\n{extra_text.strip()}")
    for fd in files_data:
        if fd["type"] == "text":
            new_parts.append(f"[FILE: {fd['name']}]\n{fd['content']}")
        elif fd["type"] == "image":
            # Image analysis not available with current model — note the attachment
            new_parts.append(f"[IMAGE UPLOADED: {fd['name']}] — Image analysis unavailable; extract tasks from filename/context only.")

    new_input = "\n\n".join(new_parts) if new_parts else "(no text input provided)"

    system_prompt = _build_system_prompt(directives_text)

    text_content = f"""{system_prompt}

---
{existing_section}

NEW INPUT:
{new_input}

Merge, classify, re-prioritize, and return the full sorted Track list.

CRITICAL: Return ONLY a valid JSON object — no markdown fences, no explanation.
Follow this schema exactly:
{_JSON_SCHEMA}"""

    contents: list = [text_content]

    raw = _stream_text(contents)
    raw = _fix_categories(raw)

    try:
        data = json.loads(raw)
    except Exception as first_err:
        # Ask the model to fix its own malformed JSON
        fix_prompt = (
            "The JSON below is malformed. Return only the corrected JSON — "
            "no markdown, no explanation. The 'category' field must be exactly one of: "
            "communication, administrative, creative, financial, personal, health, "
            "technical, planning, operational, other.\n\n"
            f"BROKEN JSON:\n{raw}"
        )
        try:
            raw2 = _stream_text([fix_prompt])
            raw2 = _fix_categories(raw2)
            data = json.loads(raw2)
        except Exception:
            raise RuntimeError(
                f"Churn Engine returned invalid JSON after retry: {first_err}\n"
                f"Raw output (first 500 chars): {raw[:500]}"
            )

    output = ChurnOutput(**data)
    if not output.signals:
        raise RuntimeError("The Churn Engine returned no signals. Try adding more detail to your input.")

    return _normalize_signals(output)

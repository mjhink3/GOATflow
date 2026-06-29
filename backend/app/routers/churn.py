from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.dependencies import get_current_user
from app.services.ai import Signal, run_churn_engine
from app.services.files import extract_docx_text, extract_pdf_text, resize_image_to_jpeg

router = APIRouter()

_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
_DOC_EXTS = frozenset({".docx", ".doc"})


def _ext(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def _process_files(files: list[UploadFile]) -> list[dict]:
    result: list[dict] = []
    for f in files:
        raw = await f.read()
        name = f.filename or "upload"
        content_type = f.content_type or ""
        ext = _ext(name)

        if ext == ".pdf" or "pdf" in content_type:
            text = extract_pdf_text(raw)
            result.append({"type": "text", "name": name, "content": text or "[PDF could not be parsed]"})

        elif ext in _DOC_EXTS or "wordprocessingml" in content_type or "msword" in content_type:
            text = extract_docx_text(raw)
            result.append({"type": "text", "name": name, "content": text or "[DOCX could not be parsed]"})

        elif ext in _IMAGE_EXTS or "image" in content_type:
            try:
                b64, mime = resize_image_to_jpeg(raw)
                result.append({"type": "image", "name": name, "b64": b64, "mime": mime})
            except Exception:
                pass  # Skip unreadable images silently

        else:
            # Try to decode as plain text (e.g. .txt, .md, .csv)
            try:
                text = raw.decode("utf-8", errors="replace")
                result.append({"type": "text", "name": name, "content": text})
            except Exception:
                pass

    return result


async def _save_signals(conn: asyncpg.Connection, user_id: str, signals: list[Signal]) -> None:
    for s in signals:
        existing = await conn.fetchrow(
            "SELECT id FROM signals WHERE task_name = $1 AND completed = FALSE AND user_id = $2",
            s.task_name,
            user_id,
        )
        if existing:
            await conn.execute(
                """
                UPDATE signals
                SET why = $1, xp_reward = $2, operational_weight = $3,
                    directive_applied = $4, bleat_type = $5,
                    horn_applied_name = $6, category = $7
                WHERE id = $8
                """,
                s.why,
                s.xp_reward,
                s.operational_weight,
                s.directive_applied,
                s.bleat_type,
                s.horn_applied_name,
                s.category or "other",
                existing["id"],
            )
        else:
            await conn.execute(
                """
                INSERT INTO signals
                    (task_name, why, xp_reward, operational_weight, directive_applied,
                     bleat_type, horn_applied_name, category, user_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                s.task_name,
                s.why,
                s.xp_reward,
                s.operational_weight,
                s.directive_applied,
                s.bleat_type,
                s.horn_applied_name,
                s.category or "other",
                user_id,
            )


@router.post("")
async def churn(
    text: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    files_data = await _process_files(files)

    if not (text and text.strip()) and not files_data:
        raise HTTPException(status_code=400, detail="Provide text or at least one file.")

    # Fetch current active signals to pass to the engine for merging
    existing_rows = await conn.fetch(
        """
        SELECT task_name, why, xp_reward, operational_weight, bleat_type, category
        FROM signals
        WHERE completed = FALSE AND user_id = $1
        ORDER BY operational_weight DESC
        """,
        current_user["id"],
    )
    existing = [dict(r) for r in existing_rows]

    # Fetch GOAT Horns
    horns_row = await conn.fetchrow(
        "SELECT rules_text FROM directives WHERE user_id = $1",
        current_user["id"],
    )
    horns_text = horns_row["rules_text"] if horns_row else ""

    # Enforce daily limit
    DAILY_LIMIT = 15
    usage_row = await conn.fetchrow(
        "SELECT count FROM churn_usage WHERE user_id = $1 AND usage_date = CURRENT_DATE",
        int(current_user["id"]),
    )
    if usage_row and usage_row["count"] >= DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Daily churn limit reached ({DAILY_LIMIT}/day). Come back tomorrow.")

    # Track usage
    await conn.execute(
        """
        INSERT INTO churn_usage (user_id, usage_date, count)
        VALUES ($1, CURRENT_DATE, 1)
        ON CONFLICT (user_id, usage_date)
        DO UPDATE SET count = churn_usage.count + 1
        """,
        int(current_user["id"]),
    )

    try:
        result = run_churn_engine(existing, files_data, text or "", horns_text)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e) or "Churn Engine failed — please try again.")

    await _save_signals(conn, current_user["id"], result.signals)

    # Return the full updated signal list in sorted order
    rows = await conn.fetch(
        """
        SELECT id, task_name, why, xp_reward, operational_weight, bleat_type,
               directive_applied, horn_applied_name, category, created_at
        FROM signals
        WHERE completed = FALSE AND user_id = $1
        ORDER BY operational_weight DESC, created_at ASC
        """,
        current_user["id"],
    )
    return [dict(r) for r in rows]

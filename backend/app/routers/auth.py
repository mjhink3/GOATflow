import random
import secrets
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.services.auth import hash_password, verify_password

router = APIRouter()


# ─── Request/response models ─────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    display_name: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ─── GoatName generator data ─────────────────────────────────────────────────

GOAT_ADJECTIVES = [
    "Majestic", "Feral", "Distinguished", "Chaotic", "Legendary", "Sneaky", "Tactical",
    "Midnight", "Golden", "Horned", "Notorious", "Rogue", "Elite", "Supreme", "Ancient",
    "Turbocharged", "Diplomatic", "Caffeinated", "Unstoppable", "Bureaucratic", "Certified",
    "Overpaid", "Underslept", "Agile", "Disruptive", "Synergistic", "Scalable", "Pivoting",
    "Bootstrapped", "PreRevenue", "PostMeeting", "FullyRemote", "CrossFunctional",
]

GOAT_NOUNS = [
    "Chomper", "Bleater", "FenceJumper", "HayStacker", "HornPolisher", "PastureWalker",
    "TrailBlazer", "SummitChaser", "CheeseBanker", "HerdWhisperer", "BleatMachine",
    "SignalSender", "TrackDestroyer", "MomentumBuilder", "FenceBreaker", "HayFarmer",
    "TractionLord", "PastureBoss", "GOATAdjacent", "CheeseHoarder", "HornInvestor",
    "DeliverableGoat", "KPIDestroyer", "SynergyGoat", "PivotMaster", "DeckBuilder",
    "MeetingSurvivor", "InboxConqueror", "DeadlineGoat", "BandwidthMaximizer",
]

GOAT_SUFFIXES = [
    "III", "Jr", "Sr", "Esq", "PhD", "MBA", "TheThird", "v2", "Pro", "Ultra",
    "Prime", "Plus", "Max", "XL", "Deluxe", "Premium", "Elite", "Alpha", "Beta",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("username") != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


# ─── Auth endpoints ───────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, conn: asyncpg.Connection = Depends(get_db)):
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Goatname must be at least 3 characters.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if not req.display_name.strip():
        raise HTTPException(status_code=400, detail="Display name is required.")

    username = req.username.strip().lower()
    existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
    if existing:
        raise HTTPException(status_code=400, detail="That goatname is already claimed.")

    pw_hash, salt = hash_password(req.password)

    async with conn.transaction():
        row = await conn.fetchrow(
            """
            INSERT INTO users (username, password_hash, password_salt, display_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, username, display_name
            """,
            username,
            pw_hash,
            salt,
            req.display_name.strip(),
        )
        await conn.execute(
            """
            INSERT INTO player (user_id, total_xp, total_hay_earned, level, tasks_completed, hay, fresh_cheese)
            VALUES ($1, 0, 0, 1, 0, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            """,
            str(row["id"]),
        )

    return TokenResponse(
        access_token=_create_token(row["id"]),
        user_id=str(row["id"]),
        username=row["username"],
        display_name=row["display_name"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, conn: asyncpg.Connection = Depends(get_db)):
    username = req.username.strip().lower()
    row = await conn.fetchrow(
        "SELECT id, username, display_name, password_hash, password_salt FROM users WHERE username = $1",
        username,
    )
    if not row or not verify_password(req.password, row["password_hash"], row["password_salt"]):
        raise HTTPException(status_code=401, detail="Invalid goatname or password.")

    return TokenResponse(
        access_token=_create_token(row["id"]),
        user_id=str(row["id"]),
        username=row["username"],
        display_name=row["display_name"],
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user


# ─── OAuth bridge ─────────────────────────────────────────────────────────────

class TokenBridgeStore(BaseModel):
    email: str
    goatflow_token: str
    user_id: str


@router.post("/store-token")
async def store_token(body: TokenBridgeStore, conn: asyncpg.Connection = Depends(get_db)):
    await conn.execute(
        """INSERT INTO oauth_token_bridge (email, goatflow_token, goatflow_user_id)
           VALUES ($1, $2, $3)
           ON CONFLICT (email) DO UPDATE SET goatflow_token=$2, goatflow_user_id=$3, created_at=NOW()""",
        body.email, body.goatflow_token, body.user_id,
    )
    return {"ok": True}


@router.get("/retrieve-token")
async def retrieve_token(email: str, conn: asyncpg.Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT goatflow_token, goatflow_user_id FROM oauth_token_bridge WHERE email=$1",
        email,
    )
    if not row:
        return {"token": None, "user_id": None}
    await conn.execute("DELETE FROM oauth_token_bridge WHERE email=$1", email)
    return {"token": row["goatflow_token"], "user_id": row["goatflow_user_id"]}


class OAuthRequest(BaseModel):
    email: str
    display_name: str
    provider: str
    provider_id: str


@router.post("/oauth")
async def oauth_login(body: OAuthRequest, conn: asyncpg.Connection = Depends(get_db)):
    user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", body.email)

    if not user:
        random_username = f"{body.provider}_{secrets.token_hex(6)}"
        pw_hash, salt = hash_password(secrets.token_hex(32))
        user = await conn.fetchrow(
            """
            INSERT INTO users (username, display_name, password_hash, password_salt, email, provider, provider_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            random_username,
            body.display_name,
            pw_hash,
            salt,
            body.email,
            body.provider,
            body.provider_id,
        )
        await conn.execute(
            "INSERT INTO player (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            str(user["id"]),
        )

    return {
        "access_token": _create_token(user["id"]),
        "token_type": "bearer",
        "user_id": str(user["id"]),
        "display_name": user["display_name"],
    }


# ─── Password reset ───────────────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, conn: asyncpg.Connection = Depends(get_db)):
    user = await conn.fetchrow(
        "SELECT id, username, email FROM users WHERE email = $1", body.email
    )

    # Always succeed to prevent email enumeration
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    await conn.execute(
        """INSERT INTO password_reset_tokens (user_id, token, expires_at)
           VALUES ($1, $2, $3)""",
        user["id"], token, expires_at,
    )

    reset_url = f"https://goatflow.app/reset-password?token={token}"

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": "GOATflow <noreply@goatflow.app>",
                    "to": [body.email],
                    "subject": "Reset your GOATflow password",
                    "html": f"""
                    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;background:#08080f;color:#F5F5F5;padding:32px;border-radius:12px;">
                        <h2 style="color:#a78bfa;font-size:20px;margin-bottom:8px;">Reset your password 🐐</h2>
                        <p style="color:#9ca3af;font-size:14px;line-height:1.6;">Someone requested a password reset for your GOATflow account (<strong>{user['username']}</strong>).</p>
                        <p style="color:#9ca3af;font-size:14px;">Click the button below to set a new password. This link expires in 1 hour.</p>
                        <a href="{reset_url}" style="display:inline-block;margin:24px 0;padding:12px 24px;background:#6100ff;color:white;text-decoration:none;border-radius:8px;font-weight:600;font-size:14px;">Reset Password</a>
                        <p style="color:#4b5563;font-size:12px;">If you didn't request this, ignore this email. Your password won't change.</p>
                        <p style="color:#4b5563;font-size:11px;margin-top:24px;">GOATflow · goatflow.app</p>
                    </div>
                    """,
                },
            )
    except Exception as e:
        print(f"[forgot-password] email send failed: {e}")

    return {"message": "If that email exists, a reset link has been sent."}


@router.get("/reset-password/validate")
async def validate_reset_token(token: str, conn: asyncpg.Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT id FROM password_reset_tokens WHERE token = $1 AND used = FALSE AND expires_at > NOW()",
        token,
    )
    return {"valid": bool(row)}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, conn: asyncpg.Connection = Depends(get_db)):
    token_row = await conn.fetchrow(
        """SELECT * FROM password_reset_tokens
           WHERE token = $1 AND used = FALSE AND expires_at > NOW()""",
        body.token,
    )

    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    pw_hash, salt = hash_password(body.new_password)
    await conn.execute(
        "UPDATE users SET password_hash = $1, password_salt = $2 WHERE id = $3",
        pw_hash, salt, token_row["user_id"],
    )
    await conn.execute(
        "UPDATE password_reset_tokens SET used = TRUE WHERE id = $1",
        token_row["id"],
    )

    return {"message": "Password reset successfully. You can now log in."}


# ─── GoatName generator ───────────────────────────────────────────────────────

@router.get("/generate-goatname")
async def generate_goatname(conn: asyncpg.Connection = Depends(get_db)):
    for _ in range(20):
        adj  = random.choice(GOAT_ADJECTIVES)
        noun = random.choice(GOAT_NOUNS)
        roll = random.random()

        if roll < 0.3:
            username = f"{adj}{noun}{random.randint(1, 999)}"
        elif roll < 0.5:
            suffix   = random.choice(GOAT_SUFFIXES)
            username = f"{adj}{noun}_{suffix}"
        else:
            username = f"{adj}{noun}"

        existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
        if not existing:
            return {"username": username, "display_name": f"{adj} {noun}"}

    fallback = f"{random.choice(GOAT_ADJECTIVES)}{random.choice(GOAT_NOUNS)}{random.randint(1000, 9999)}"
    return {"username": fallback, "display_name": fallback}


# ─── Admin endpoints ──────────────────────────────────────────────────────────

@router.get("/admin/users")
async def admin_list_users(
    admin: dict = Depends(require_admin),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        """SELECT u.id, u.username, u.display_name, u.email, u.provider,
                  u.created_at, u.current_herd_id, u.role,
                  p.level, p.total_hay_earned, p.tasks_completed,
                  p.cheese_state, p.last_active_at
           FROM users u
           LEFT JOIN player p ON p.user_id = CAST(u.id AS TEXT)
           ORDER BY u.created_at DESC"""
    )
    return [dict(r) for r in rows]


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin: dict = Depends(require_admin),
    conn: asyncpg.Connection = Depends(get_db),
):
    if user_id == int(admin["id"]):
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    await conn.execute("DELETE FROM player WHERE user_id = $1", str(user_id))
    await conn.execute("DELETE FROM users WHERE id = $1", user_id)
    return {"ok": True, "deleted_user_id": user_id}


@router.patch("/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: int,
    admin: dict = Depends(require_admin),
    conn: asyncpg.Connection = Depends(get_db),
):
    temp_password = secrets.token_urlsafe(12)
    pw_hash, salt = hash_password(temp_password)
    await conn.execute(
        "UPDATE users SET password_hash = $1, password_salt = $2 WHERE id = $3",
        pw_hash, salt, user_id,
    )
    return {"temp_password": temp_password}

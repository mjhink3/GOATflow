# GOATflow — WorkGOAT Ecosystem Tactical Input Layer

AI-powered operational intelligence SaaS dashboard with multi-user authentication, gamified Cheese Churn Rate system, Hay & Fresh Cheese reward economy, and Stateless Privacy for Postmaster-level operations. Part of the WorkGOAT Ecosystem.

## Overview
Users sign in via username/password to access their private dashboard. Each user has isolated data (Tracks/Signals, Horns/Directives, XP, Hay, Fresh Cheese). Users drop files (PDFs, images, text) or record voice into the Track Sieve (via floating Voice FAB). GPT-4o-mini classifies inputs as "Routine Grazing" or "Summit Call", merges with existing tasks, and re-sorts by Operational Weight. Tasks persist in PostgreSQL per-user. Completing Tracks earns Cheese Churn Points and Hay.

### Mobile UX
- Above-the-fold layout: banner header replaces circular logo+tagline; Track Sieve, input zone, and churn button all fit without scrolling
- Banner header (`.gf-banner-wrap`): 90px desktop / 64px mobile; object-fit cover; object-position center 20% desktop / center 15% mobile; bottom fade overlay; GOATflow wordmark built into image
- Floating Voice FAB: `#gf-voice-fab`, position:fixed bottom-right, injected into parent doc via ob_iframe IIFE (step 6), purple → red recording → amber processing → green complete states
- Stat cards: 2-column CSS grid on mobile (`grid-template-columns: 1fr 1fr`)
- Scroll indicator: `#gf-scroll-hint` — three dots (&bull;&bull;&bull;), 8px, #4b5563, letter-spacing 4px, below churn button; auto-hides on first scroll or after 6s; mobile only

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page
- **Fonts**: Syne (700/800) for headings/stat numbers, DM Sans (400/500) for body
- **Background**: #0a0a0f with topographic contour SVG pattern (3-4% opacity, #1a1a2e strokes)
- **Auth**: Self-contained username/password (PBKDF2-HMAC-SHA256) in PostgreSQL
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals, XP, Hay, Fresh Cheese, and directives — all scoped by `user_id`
- **PDF Parsing**: PyPDF2
- **Assets**: Celebration artwork images + main logo

## Authentication & Multi-User
- Self-contained username/password auth using PostgreSQL `users` table
- Passwords hashed with PBKDF2-HMAC-SHA256 + random salt (hashlib stdlib)
- Session stored in `st.session_state` keys: `auth_user_id`, `auth_user_name`, `auth_display_name`
- `get_current_user()` returns `{"id", "name", "display_name"}` from session state or `None`
- Landing page: full-screen, logo centered, tagline (Syne 700), descriptor (DM Sans muted), Login/Create Account tabs
- Signup validates: all fields required, username >= 3 chars, password >= 6 chars, passwords match, username unique
- Logout button in sidebar clears session keys and reruns
- Each user gets their own player record, signals, and directives (keyed by `user_id` = str(users.id))

## Database Schema
- **users**: id (SERIAL PK), username (TEXT UNIQUE), password_hash, password_salt, display_name, created_at
- **signals**: id (SERIAL PK), task_name, why, xp_reward, operational_weight, completed, directive_applied, bleat_type, created_at, completed_at, **user_id** (TEXT NOT NULL), horn_applied_name
- **player**: id (SERIAL PK), **user_id** (TEXT UNIQUE), total_xp, level, tasks_completed, **hay** (INTEGER DEFAULT 0), **fresh_cheese** (INTEGER DEFAULT 0), **onboarding_done** (BOOLEAN DEFAULT FALSE)
- **directives**: id (SERIAL PK), **user_id** (TEXT UNIQUE), rules_text (newline-separated Horns)
- **operational_log**: id, user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier, created_at
- Migration: `ensure_schema()` adds all new columns via ALTER TABLE IF NOT EXISTS checks

## Goatifications System
GOATflow's branded in-app and push notification system. Every notification is called a "Goatification" — never a "notification" in user-facing text.
- **IIFE Template**: `_GOATIF_IIFE_TMPL` (raw Python string in `app.py`, injected after voice FAB via `_stc.html()`)
- **Icon**: `static/goatification_icon.png` — animated megaphone/horn graphic; loaded as base64 `goatif_icon_src`; substituted into IIFE via `__GOATIF_ICON__` placeholder
- **In-app Toast**: Slides down from top of parent document (#gf-toast); animates in 300ms, auto-dismisses after 4s; queued system ensures no overlap
- **Permission Flow**: Branded overlay (`.gf-perm-overlay`) with hornPulse animation; fires once after onboarding via `gfMaybeAskPermission()`; result stored in `localStorage.goatflow_notif_asked`
- **Sidebar Section**: `#gf-goatif-sidebar` — injected into parent sidebar DOM via JS MutationObserver+retry pattern; positioned before "Your Trail" button; collapsible (default: collapsed); state in `sessionStorage.gf_sb_collapsed`
- **6 Toggles**: Fresh Cheese Earned (ON), Summit Call Overdue (ON), Speed Bonus (ON), Clip Rate Nudges (OFF, "Max 1/48hrs" pill), Morning Summit Reminder (OFF + time picker 6am–11am), Streak Milestones (ON)
- **Prefs**: `localStorage.goatflow_notif_prefs` — read/saved on every toggle; master ON/OFF gates all triggers
- **Triggers wired**:
  - Fresh Cheese: `_stc.html()` injected alongside `show_fresh_cheese_popup()` 
  - Speed Bonus: detected when `hay_earned > base_hay` at completion; stored as `just_earned_speed_bonus` session state; injected in `just_completed_task` handler; only fires when tab is not focused
  - Summit Overdue: `setInterval` every 30 min; reads `data-signal-id`, `data-bleat-type`, `data-created-at` from signal card DOM
  - Daily Reminder: `setTimeout` calculated to next reminder time; re-schedules daily
- **Signal cards**: Have `data-signal-id`, `data-bleat-type`, `data-created-at`, `data-task-name` HTML attributes for JS trigger detection
- **Rate limit**: Max 2 per 10-minute window; streak milestones bypass the limit
- **Quiet hours**: 10pm–7am; push notifications suppressed; in-app toasts always allowed

## Key Files
- `app.py` — Full application
- `goatflow_logo.png` — Main WorkGOAT logo (320px header, home button)
- `celeb_levelup.png` / `celeb_levelup_new.png` — Leader Goat: Fence Broken celebration
- `celeb_task_completed.png` — Thumbs-Up "Gusto" Goat: task completion popup
- `celeb_priority_achieved.png` — Glow-Eye Goat: High-Leverage task icon on cards
- `celeb_power_hour.png` — GOAT tier completion / Crown avatar for Level 5+
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## Landing Page
- Shown to non-logged-in users
- Full-screen: topographic background, logo centered, tagline "Grab life by the horns. Leave the bull behind." (Syne 700), descriptor "Metabolize your to-do list." (DM Sans muted #9ca3af)
- Login / Create Account tabs with dark-styled forms
- No feature cards — brand and form only
- Footer: "GOATflow is a subsidiary of the WorkGOAT Ecosystem"
- Calls `st.stop()` after rendering

## Track Card Visual Hierarchy (Priority-Coded Left Borders)
- **Summit Call**: 4px left border #ff4444, card bg #1a0f0f, glow on hover red
- **Standard/High-Leverage**: 4px left border #7c3aed, card bg #0f0f1a, glow on hover purple
- **Completed**: 4px left border #22c55e, card bg #0a1a0f, 60% opacity
- Corner radius: 8px, no uniform border

## GOAT Horns Panel (Sidebar)
- Each Horn displayed as an individual card with amber left border (#f59e0b), amber glow on hover
- Horn text in DM Sans 500 weight
- Single-line input with "Add a Horn" placeholder, "Lock In My Horns" button
- Maximum 10 Horns per user
- Delete (×) button on each Horn card
- Stored as newline-separated text in `directives.rules_text`

## Button System
- **Primary** (Drop Into Churn Engine, Lock In My Horns, Complete): bg #7c3aed, white text, Syne 700, radius 6px, purple glow on hover
- **Secondary**: transparent, 1px border #7c3aed, purple text, no glow
- **Destructive**: bg #1a1a1a, text #ff4444

## Churn Engine Processing Animation
- Custom topographic SVG animation (concentric ellipse rings pulsing in/out)
- Text cycles: "Reading the terrain…" → "Filtering the noise…" → "Surfacing your Tracks…" (800ms fade)
- Overlay sits above the input area; disappears on rerun or error

## Hay & Fresh Cheese Economy (V1)
- **Hay earned per completion**: Summit Call = 50 Hay, all others = 10 Hay
- **Speed bonus**: +10 Hay if Track completed within 24h of generation
- **Conversion**: 500 Hay → 1 Fresh Cheese automatically; `hay` column stores remainder after conversion
- **HAY DECAY** — reserved for WorkGOAT integration phase (commented in code)
- Conversion triggers: fresh_cheese count increments, cheese-toast notification displays in feed
- Dashboard stat cards (7): Active Tracks, Summit Calls, Completed, Hay (🌾 amber), Fresh Cheese (🧀 green), Active Horns (with Horns image + count), CLIP RATE (✂️, color-coded green/amber/red)
- Hay card shows "340/500 to next 🧀" sub-label
- Clip Rate = (Tracks completed / Tracks generated) × 100 over rolling 7-day window; "—" for users with < 5 total completed
- Clip Rate card border: green (#3DAA6A) ≥75%, amber (#f59e0b) 50-74%, red (#ef4444) <50%
- Nudge panel (amber, JS-injected): appears when Clip Rate < 60% with ≥5 completed Tracks; dismissed per-session via sessionStorage; "Refine a Horn →" opens sidebar
- Pasture Gauge bar shows "🌾 X/500 Hay to next 🧀" below the tier label

## Sidebar My Stats
- Total Grit (XP), Cheese Churn Rate, Ascension Rank, Next Fence
- **Fresh Cheese Banked** (green #22c55e) with muted link to workgoat.vip
- **✂️ Clip Rate (7d)**: color-coded (green/amber/red) matching dashboard card thresholds
- **Clip Rate — Last 4 Weeks** bar chart: █/░ block chars, per-week color coded, shown inside My Stats card
- Trail dialog: weekly 4-week Clip Rate bar chart shown at top before filter buttons
- **Port to WorkGOAT** button (secondary style) — tooltip: "WorkGOAT is coming. Your Fresh Cheese will be waiting."

## Ascension Profile & Progress (Sidebar)
- **Ascension Ranks**: The Kid (L1), The Starter (L2-3), The Builder (L4-5), The Architect (L6), The GOAT (L7+)
- **Crown Avatar**: Users Level 5+ get the Crown Goat as profile avatar
- Pastures: The Pen → Grazing Grounds → Open Pasture → Highland Trail → Summit Ridge → The Peak → GOAT Mountain

## Cheese Churn Rate (CCR) System
- Micro: 100 CCR, Standard: 500 CCR, High-Leverage: 1500 CCR, GOAT: 5000 CCR
- Level thresholds: Level 1 = 5000 CCR, each subsequent = +20% more
- Confetti + Gusto Goat popup on task completion
- LinkedIn share button in Fresh Cheese stat card

## Terminology (UI vs Internal)
- Signals = Tracks (UI); `signals` table (DB)
- Horns = Directives (UI); `directives` table / `rules_text` column (DB)
- Summit Call = "Summit-Level Bleat" (old) or "Summit Call" (new) — both recognized
- Routine Grazing = routine tasks
- CCR = Cheese Churn Rate = XP
- Fence Broken = Level Up
- Pasture Gauge = XP progress bar
- Track Sieve = input area (was Bleat Sieve)

## OpSec & Privacy
- Stateless Processing: files_data.clear() after AI analysis
- Incognito Mode: session-only signals, not persisted to DB
- OpSec Layer panel in sidebar

## Onboarding Flow (Slideshow → Shepherd.js Tour)

### Key Technical Facts
- **CRITICAL**: `st.markdown(unsafe_allow_html=True)` does NOT execute `<script>` tags in Streamlit 1.55.
- **Solution**: Use `streamlit.components.v1.html()` — same-origin iframe; `window.parent.document.createElement('script')` injects scripts into the parent page scope.
- AMD-disable wrapper forces Shepherd.js UMD global path (avoids Streamlit React's `define.amd` hijack).
- `pw = window.parent` may equal `window` (top-level) or parent Replit frame — `pw.document` is always correct target.
- Streamlit also strips `onclick` / all `on*` event handler attributes from `st.markdown` HTML. Use DOM TreeWalker to bind click listeners programmatically.

### Slideshow (Animal Elimination — 15 animals)
- Runs BEFORE the Shepherd tour for first-time users (`gfObForce=true` when `onboarding_done=false`).
- Sequence per slide: image fade-in (0.5s) → SVG X draws across (1.0s) → caption fades in (0.75s) → pause (0.75s) → next. ~3s per slide.
- Animal order: bull, ram, chicken, cow, dog, cat, donkey, lizard, hamster, sheep, pig, rabbit, duck, eagle, horse.
- After all 15: GOATflow logo + "The choice is clear." celebration → `pw.gfStartTour()`.
- "Skip Intro →" button: fixed top-right, `z-index: 100000`, skips directly to tour.
- Progress dots: 15 dots bottom-center, active = purple `#7c3aed`.
- Images: `static/onboarding/animal_[name].jpg` (compressed JPGs ~20-31KB each), served at `/app/static/onboarding/`.
- Logo: `static/goatflow_logo_nobg.png`.
- Guard: `pw._gfSlideshowStarted = true` prevents slideshow restart on Streamlit reruns.

### Shepherd.js Tour (6 steps)
- Defined in `_tour_iife` (Python raw string), JSON-encoded, injected into parent document head via `components.v1.html`.
- Steps: welcome → horns → sieve → ranking → hay → done.
- `pw.gfStartTour()` defined in parent window; called by slideshow completion AND by Replay Tutorial button.
- Replay Tutorial button: Streamlit strips `onclick`, so `_bindReplayBtn()` in tour IIFE uses TreeWalker to find text node "Replay Tutorial" and binds DOM click listener.
- Completion/cancel: `pw.history.replaceState(...?ob_done=1)` → Streamlit detects → `mark_onboarding_done()`.

### Static Files
- `static/shepherd.min.js` (45KB), `static/shepherd.css` (3.4KB)
- `static/onboarding/animal_*.jpg` (15 compressed JPGs)
- `static/goatflow_logo_nobg.png`

### Imports at Top of app.py
- `import streamlit.components.v1 as _stc`
- `import json as _json`

### Rebuild Pattern
From `/tmp/app_part1.py` + `/tmp/app_shepherd_section.py` + `/tmp/app_part3.py`: make sure `_stc` and `_json` imports are at the top level (they're in app_part1.py already). Shepherd section has no inline imports. Apply patches: (1) Help button onclick → `gfStartTour()` (now uses DOM binding so onclick not needed), (2) `id="gf-sieve-anchor"` on churn-label div.

## Dependencies
- streamlit, openai, PyPDF2, fpdf2, psycopg2-binary, Pillow

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection (set by Replit)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key

## Running
```bash
streamlit run app.py --server.port 5000
```

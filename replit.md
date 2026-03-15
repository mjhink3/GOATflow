# GOATflow — WorkGOAT Ecosystem Tactical Input Layer

## Overview
GOATflow is an AI-powered operational intelligence SaaS dashboard designed to be the tactical input layer for the WorkGOAT Ecosystem. It provides multi-user authentication, a gamified "Cheese Churn Rate" system, a "Hay & Fresh Cheese" reward economy, and "Stateless Privacy" for operational data.

Users log in to access a private dashboard where they can input files (PDFs, images, text) or voice recordings into the "Track Sieve." GPT-4o-mini classifies these inputs as "Routine Grazing" or "Summit Call," merges them with existing tasks, and re-sorts them by "Operational Weight." Tasks are persistently stored per-user in PostgreSQL. Completing "Tracks" earns "Cheese Churn Points" (XP) and "Hay." The project aims to enhance user productivity and engagement through a gamified task management system.

## User Preferences
I prefer iterative development, with clear communication before major architectural or design changes. I want the agent to prioritize high-level feature implementation and architectural consistency over minor code optimizations initially. Ensure all user-facing terminology aligns with the "GOATflow" brand (e.g., "Goatification" instead of "notification").

## System Architecture
The application is built using Streamlit (Python) with a centered, single-page layout.
**UI/UX Decisions:**
- **Design:** Dark theme (`#0a0a0f`) with a subtle topographic contour SVG background.
- **Typography:** Syne (700/800) for headings and stats, DM Sans (400/500) for body text.
- **Mobile UX:** Optimized for mobile with specific banner, FAB, and stat card layouts. A scroll indicator (`#gf-scroll-hint`) is present on mobile.
- **Task Cards:** Visually prioritized with color-coded left borders (red for "Summit Call", purple for "Standard/High-Leverage", green for "Completed") and distinct background colors.
- **Buttons:** Primary (purple background, white text), Secondary (transparent, purple border/text), and Destructive (dark background, red text) styles.
- **Animations:** Custom topographic SVG animation for the "Churn Engine" processing, text cycling during processing, and confetti/popup on task completion.
- **Goatifications:** Branded in-app and push notification system with an animated megaphone icon, queueing, and user-configurable preferences (e.g., Summit Call Overdue, Speed Bonus, Daily Reminder).

**Technical Implementations:**
- **Authentication:** Self-contained username/password system using PBKDF2-HMAC-SHA256 hashing against a PostgreSQL `users` table. User sessions are managed via `st.session_state`.
- **AI Integration:** Utilizes OpenAI GPT-4o-mini via Replit AI Integrations for input classification and task processing, expecting structured output via Pydantic.
- **Database:** PostgreSQL is used for persistence of user data including signals (tasks), XP, Hay, Fresh Cheese, and user-defined directives (Horns), all scoped by `user_id`.
- **PDF Parsing:** PyPDF2 is used for processing PDF inputs.
- **Gamification:** "Hay & Fresh Cheese" economy: Hay is earned per task completion (50 for Summit Call, 10 for others), with a speed bonus. 500 Hay automatically converts to 1 Fresh Cheese. "Cheese Churn Rate" (XP) dictates user level and "Ascension Rank."
- **Onboarding:** Features a multi-slide "Animal Elimination" sequence followed by a Shepherd.js guided tour for first-time users.
- **Stateless Privacy:** `files_data.clear()` after AI analysis ensures data privacy. An "Incognito Mode" allows for session-only signals.
- **Streamlit Integration:** Extensive use of `streamlit.components.v1.html()` for injecting custom HTML, CSS, and JavaScript, including dynamic element injection and event binding workarounds for Streamlit's limitations (e.g., script execution, `onclick` stripping).

**Feature Specifications:**
- **Track Sieve:** The primary input area for files and voice recordings.
- **GOAT Horns Panel:** A sidebar panel for users to define and manage up to 10 "Horns" (directives/rules) that guide AI processing.
- **Dashboard Stats:** Includes "Active Tracks," "Summit Calls," "Completed," "Hay," "Fresh Cheese," "Active Horns," and a "CLIP RATE" (tasks completed vs. generated).
- **Ascension Profile:** Users progress through ranks ("The Kid" to "The GOAT") with associated visual cues (e.g., Crown Avatar).

## External Dependencies
- **Streamlit:** Primary web application framework.
- **OpenAI:** For AI model (GPT-4o-mini) integration.
- **PyPDF2:** For parsing PDF documents.
- **psycopg2-binary:** PostgreSQL adapter.
- **Pillow:** Image processing library.
- **Shepherd.js:** For interactive user onboarding tours.
- **fpdf2:** Likely for PDF generation or manipulation (though not explicitly detailed in use).
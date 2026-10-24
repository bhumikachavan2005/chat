# 🔐 Vinu 💝🎀 × Bhuu 🎀 | Private WhatsApp Friendship Archive

A **100% private, offline, secure, and modern personal web application** that transforms the WhatsApp chat export between Vinu and Bhuu into an interactive, searchable friendship archive with full-text search, memories, analytics, timeline, Friendship Wrapped, and offline insights.

---

## 🛡️ Privacy & Security Highlights

* **100% Localhost Only**: The server binds exclusively to `127.0.0.1` (never exposed to the local network or the internet).
* **Zero Telemetry / Tracking**: No analytics, Google Analytics, Firebase, Mixpanel, or third-party cloud connections.
* **Argon2id Password Protection**: Master password is securely hashed with Argon2id (and Scrypt fallback). No plaintext passwords stored anywhere.
* **Local SQLite Database with FTS5**: All 17,000+ messages are indexed locally in `data/chat.db` with full-text search.
* **Lossless Incremental Merge & Deduplication**: Uploading updated `.txt` exports never duplicates or deletes existing messages and preserves memory bookmarks.
* **AES-256-GCM Encrypted Backups**: Portable, authenticated encrypted backup export & restore.
* **Inactivity Auto-Lock**: Automatically locks the archive after a period of inactivity (configurable from 5 to 60 minutes).
* **Untouched Source Data**: The original `WhatsApp Chat with Vinu💝🎀.txt` file remains completely untouched.

---

## 🚀 How to Run the Archive

### Option A: One-Click (Recommended)
1. **First-Time Setup**: Double-click `install.bat`
2. **Launch Application**: Double-click `start.bat` (opens browser automatically on `http://127.0.0.1:8765`)

---

### Option B: Manual Commands (Terminal / Command Prompt / PowerShell)

#### Step 1: Open Terminal in Project Directory
```powershell
cd /d "%~dp0"  # or cd to your project directory (e.g. "C:\Users\Vinayak\Downloads\TP\TP")
```

#### Step 2: Install All Dependencies
```bash
python -m pip install fastapi uvicorn argon2-cffi cryptography python-multipart
```
*(If on a standard user account without Admin rights, add `--user`:)*
```bash
python -m pip install --user fastapi uvicorn argon2-cffi cryptography python-multipart
```

#### Step 3: Run the Archive
```bash
python start_archive.py
```
*(Or if using the Python Launcher: `py start_archive.py`)*

#### Step 4: Open in Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:8765
```

---

## 🔑 Setting and Managing Your Password

1. **First-Time Launch**: On your first visit, the lock screen will prompt you to **Create Master Password**.
2. **Unlocking**: Enter your master password and click **Unlock Archive**.
3. **Change Password**: Go to the **⚙️ Settings** tab > **Change Master Password**, enter your current password, and set a new one.
4. **Instant Lock**: Click the **🔒 Lock** button in the top right header at any time to immediately lock the archive.

---

## 📂 Project Structure

```
TP/ (Project Root)
├── backend/
│   ├── api/                # FastAPI API routes & auth guards
│   │   ├── auth_middleware.py
│   │   ├── routes_auth.py
│   │   ├── routes_chat.py
│   │   ├── routes_search.py
│   │   ├── routes_memories.py
│   │   ├── routes_stats.py
│   │   ├── routes_insights.py
│   │   └── routes_system.py
│   ├── parser/             # WhatsApp export parser
│   │   └── whatsapp_parser.py
│   ├── security/           # Argon2id & AES-256-GCM cryptography
│   │   └── auth.py
│   ├── services/           # Search, Stats, Timeline, Evolution, Memories, Insights
│   │   ├── chat_service.py
│   │   ├── search_service.py
│   │   ├── memory_service.py
│   │   ├── stats_service.py
│   │   ├── evolution_service.py
│   │   ├── funny_service.py
│   │   ├── insights_service.py
│   │   └── backup_service.py
│   ├── database.py         # SQLite connection, schema & FTS5 triggers
│   └── main.py             # FastAPI app with security headers
├── data/                   # Local database (excluded from Git)
│   └── chat.db
├── frontend/               # Modern SPA Frontend
│   ├── css/
│   │   └── style.css       # Obsidian glassmorphic design system
│   ├── js/
│   │   ├── components/     # Chat, Search, Timeline, Memories, Stats, Evolution, Funny, Insights, Settings
│   │   ├── api.js          # Authenticated local API client
│   │   ├── charts.js       # Standalone zero-dependency SVG chart engine
│   │   └── app.js          # SPA Controller & auto-lock lifecycle
│   └── index.html
├── tests/                  # Automated test suite
│   ├── test_archive.py
│   └── test_http_e2e.py
├── .gitignore              # Protects private database, backups, and chat files
├── README.md
├── start_archive.py        # Local Python launcher
└── start.bat               # Windows batch launcher
```

---

## ✨ Features Walkthrough

1. **💬 WhatsApp Chat Viewer**:
   - Distinct message bubbles (Bhumi on left in soft slate/rose accent, Vinu on right in emerald green).
   - Date separators, message timestamps, edited/deleted tags, and media placeholders.
   - Fast pagination and virtualized scrolling for smooth performance across 17,000+ messages.
   - Quick jump buttons: **⏮ First**, **Latest ⏭**, and **Jump to Date**.
   - Filters by Sender (All, Vinu, Bhumi, System), Media Only, or ⭐ Memories Only.
   - 1-click **❤️ Save Memory** button on any message.

2. **🔍 Powerful Search Engine**:
   - SQLite FTS5 instant keyword and phrase search.
   - Keyword highlighting and surrounding 2-message conversation preview.
   - 1-click **View in Conversation ➔** jump into chat timeline.

3. **🗓️ Friendship Timeline**:
   - Year and month hierarchy with message volume, active days, and memory counts.
   - 1-click month card navigation.

4. **❤️ Memory Vault**:
   - 8 Categorized memory types: *❤️ Special, 🥹 Emotional, 😂 Funny, 😭 Difficult, 🎂 Birthday, 🎓 Career, 🫂 Friendship, ⭐ Important*.
   - Personal reflections, reflections editor, tags, and category filtering.

5. **📊 Factual Statistics & Analytics**:
   - Factual message counts, percentage split, and active days.
   - Interactive **Message Share Donut Chart** (SVG).
   - **24-Hour Chatting Rhythm Area Chart** (Heatmap of active chatting hours).
   - **Day of Week & Monthly Trend Bar Charts**.
   - **Top Emojis Leaderboard** (with breakdown for Vinu vs Bhumi).
   - **Word Frequency Cloud** with stopword filtering for English and Marathi transliterations.

6. **📈 Friendship Evolution**:
   - Factual side-by-side comparison between **2025** (Initial Connection) and **2026** (Active Era).
   - Velocity, daily frequency, sender share balance shifts, and vocabulary progression.

7. **😂 Funny Moments Hub**:
   - Detects humor markers (`😂`, `🤣`, `💀`, `haha`, `lol`) and displays surrounding conversation threads.
   - Allows confirming moments as memories or dismissing suggestions.

8. **🧠 Private Offline AI Insights**:
   - 100% offline rule-based query resolution with verified message citations.
   - Answers inquiries such as:
     - *"When did Bhumi first ask me for internship help?"* (31/12/2025 at 1:17 PM)
     - *"Find our conversations about placements."*
     - *"What were we discussing around New Year 2026?"*
     - *"Show conversations where we apologized."*
     - *"How did our communication change between 2025 and 2026?"*
   - Custom query search bar with direct links to message IDs.

9. **🌙 Dark / Light Mode**:
   - Default Obsidian Dark mode with smooth toggle to crisp Light mode.

---

## 💾 Backups & Data Deletion

### Where is data stored?
- Local SQLite database: `data/chat.db`

### How to Create an Encrypted Backup:
1. Go to **⚙️ Settings** > **🛡️ AES-256-GCM Encrypted Backup**.
2. Enter a backup passphrase and click **Download Encrypted Backup (.enc)**.
3. The `.enc` file is authenticated with AES-256-GCM and can be restored anytime.

### How to Restore an Encrypted Backup:
1. Go to **⚙️ Settings** > **📥 Restore Encrypted Backup**.
2. Select your `.enc` file, enter your passphrase, and click **Decrypt & Restore**.

### How to Completely Delete All Data:
1. Go to **⚙️ Settings** > **⚠️ Nuclear Wipe Data**.
2. Enter your master password to confirm and click **Erase All Data Permanently**.
3. All messages, memories, and database records will be erased immediately.

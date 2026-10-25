Set-Content README.md @"
# 🏏 Cricket Auction Arena

A real-time multiplayer cricket auction simulation platform built with **Flask**, **Flask-SocketIO**, and vanilla **HTML/CSS/JavaScript**. It lets users create or join private auction rooms, place live bids, manage team purses, and run custom team squad analyses.

🔗 **Live Demo:** [cricket-auction-arena.onrender.com](https://cricket-auction-arena.onrender.com)

---

## ⚡ Features

- **Live Bidding with WebSockets:** Instant bid updates across all participants in a room using SocketIO.
- **Room Management:** Create private rooms with custom team names, or join existing rooms with a 5-letter room code.
- **Host Controls:** Dedicated controls for room creators to pause, resume, start, or move to the next player.
- **Rate-Limited Actions:** Basic anti-spam protection on bidding and client actions.
- **Player Search & Filtering:** Filter the available pool of players by role, nationality, or keyword.
- **Squad Analysis:** Post-auction evaluation engine that rates squad balance and remaining budget based on T20 scoring metrics.

---

## 📁 Project Structure

\`\`\`text
cricket-auction-arena/
├── backend/
│   ├── app.py              # Main Flask server and SocketIO event handlers
│   ├── auction.py          # Core auction state engine, bidding locks, and rules
│   ├── db.py               # Player database loader and state persistence
│   ├── analysis.py         # Squad rating and team analysis logic
│   └── config.py           # Configuration variables and environment loading
├── frontend/
│   ├── index.html          # Main application interface
│   └── static/
│       ├── css/
│       │   └── main.css    # UI styling
│       └── js/
│           └── app.js      # Frontend client logic and SocketIO connection
├── .gitignore              # Ignored files (.env, .venv, *.db, __pycache__)
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation
\`\`\`

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Python 3.10 or higher installed on your machine.
- Git installed.

### 2. Clone the Repository
\`\`\`bash
git clone https://github.com/srahul3410/cricket-auction-arena.git
cd cricket-auction-arena
\`\`\`

### 3. Set Up Virtual Environment
\`\`\`bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
\`\`\`

### 4. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 5. Configure Environment Variables
Create a .env file in the root folder:
\`\`\`env
SECRET_KEY=mycricketsecretkey12345
PORT=5000
\`\`\`

### 6. Run the Application
\`\`\`bash
python -m backend.app
\`\`\`

Open your browser at: \`http://127.0.0.1:5000\`

---

## 🛡️ License
MIT License
"@

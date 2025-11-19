#!/usr/bin/env python3
"""
Kraken Kouncil v4.2.1 – Web Search + Model Icons Edition
✓ NEW: Google PSE web search integration for real-time information
✓ NEW: Model family icons (llama, gemma, qwen, etc.) with emoji fallbacks
✓ Retained: Agentic Debate System with round counters
✓ Retained: Comprehensive How-To Manual (Help menu + ? button)
✓ Retained: Original awesome arena design with pulsing avatars
✓ Retained: All v3.6 features (thread-safe, strict voting, personas, etc.)
"""

import asyncio
import aiohttp
import requests
import sqlite3
import datetime
import json
import threading
import zipfile
import hashlib
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon, QKeySequence

try:
    from pyqtdarktheme import apply_theme
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False

# ====================== Config & Constants ======================

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "kouncil_stats.db"
SETTINGS_PATH = APP_DIR / "kouncil_settings.json"

# Personality definitions for the models
DEFAULT_PERSONAS = [
    {"name": "None", "prompt": None, "emoji": "🟢"},
    {"name": "Meticulous Fact-Checker", "prompt": "You are a meticulous fact-checker. You prefer primary sources and verify every claim. If you are unsure, admit it.", "emoji": "🔍"},
    {"name": "Pragmatic Engineer", "prompt": "You are a pragmatic engineer. Focus on feasible steps, trade-offs, and implementation details. Be concise and practical.", "emoji": "⚙️"},
    {"name": "Cautious Risk Assessor", "prompt": "You are a cautious risk assessor. Your job is to identify potential failure modes, security risks, and downsides.", "emoji": "⚠️"},
    {"name": "Clear Teacher", "prompt": "You are a clear teacher. Explain complex concepts simply using analogies and examples. Avoid jargon.", "emoji": "👨‍🏫"},
    {"name": "Data Analyst", "prompt": "You are a data analyst. Structure your answer with bullet points, tables, and clear metrics. Be objective.", "emoji": "📊"},
    {"name": "Systems Thinker", "prompt": "You are a systems thinker. Map out second and third-order consequences. Look at the big picture.", "emoji": "🧠"},
    {"name": "Creative Muse", "prompt": "You are a creative muse. Think outside the box, offer novel solutions, and use evocative language.", "emoji": "🎨"},
    {"name": "Devil's Advocate", "prompt": "You are a devil's advocate. Challenge the premise of the question and offer a counter-intuitive perspective.", "emoji": "😈"},
]

# Distinct colors for model avatars
MODEL_COLORS = [
    "#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#FF8B94",
    "#A8E6CF", "#FFD3B6", "#AA96DA", "#FCBAD3", "#88D8B0",
    "#D4A5A5", "#9B59B6", "#3498DB", "#E67E22", "#2ECC71"
]

# ====================== Settings Management ======================

def load_settings() -> dict:
    """Load settings from JSON or return defaults"""
    default = {
        "lm_studio_url": "http://localhost:1234",
        "ollama_url": "http://localhost:11434",
        "lm_studio_enabled": True,
        "ollama_enabled": True,
        "theme": "dark",
        "max_concurrency": 3,
        "persona_assignments": {},
        "debate_enabled": False,
        "debate_rounds": 2,
        "web_search_enabled": False,
        "google_api_key": "",
        "google_search_engine_id": "",
        "max_search_results": 5,
    }
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            default.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return default

def save_settings(s: dict):
    """Save settings to JSON"""
    current = load_settings()
    current.update(s)
    try:
        SETTINGS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving settings: {e}")

settings = load_settings()

# ====================== Database & Leaderboard ======================

def ensure_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        question TEXT,
        winner TEXT,
        details TEXT
    )""")
    conn.commit()
    conn.close()

def record_vote(question: str, winner: str, details: dict):
    """Record a round result to the DB"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO votes (timestamp, question, winner, details) VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), question, winner, json.dumps(details))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def load_leaderboard() -> Dict[str, int]:
    """Fetch win counts from DB"""
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.cursor().execute("SELECT winner, COUNT(*) FROM votes GROUP BY winner ORDER BY COUNT(*) DESC").fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}
    except Exception as e:
        print(f"Leaderboard Error: {e}")
        return {}

ensure_db()
leaderboard = load_leaderboard()

# ====================== Web Search Functions ======================

async def google_pse_search(query: str, api_key: str, engine_id: str, max_results: int = 5) -> list:
    """
    Perform Google Programmable Search Engine query
    Returns list of search result dicts with 'title', 'link', 'snippet'
    """
    if not api_key or not engine_id:
        return []
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": engine_id,
        "q": query,
        "num": min(max_results, 10)  # Google PSE max is 10 per request
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Google PSE Error {response.status}: {error_text}")
                    return []
                
                data = await response.json()
                return data.get("items", [])
    except asyncio.TimeoutError:
        print("Google PSE search timed out")
        return []
    except Exception as e:
        print(f"Google PSE search failed: {e}")
        return []

def format_search_results(results: list, query: str) -> str:
    """Format search results for inclusion in model context"""
    if not results:
        return ""
    
    # Add current date for temporal context
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    formatted = f"[Current Date: {current_date}]\n\n"
    formatted += f"[Web Search Results for: {query}]\n\n"
    
    for i, item in enumerate(results, 1):
        title = item.get('title', 'No title')
        link = item.get('link', 'No link')
        snippet = item.get('snippet', 'No description')
        
        formatted += f"[{i}] {title}\n"
        formatted += f"    URL: {link}\n"
        formatted += f"    {snippet}\n\n"
    
    formatted += f"[End of Web Search Results - {len(results)} results]\n\n"
    formatted += f"IMPORTANT: If you use information from these search results, cite the source number like [{i}] in your response.\n\n"
    return formatted

# ====================== File & String Helpers ======================

def process_attachment(path: Path) -> str:
    """Read and format attached files"""
    if not path.exists() or path.stat().st_size > 10 * 1024 * 1024:
        return "[File too large (>10MB) or missing]"

    suffix = path.suffix.lower()
    text_exts = {".txt", ".py", ".json", ".md", ".log", ".csv", ".yaml", ".yml", ".toml", ".html", ".css", ".js", ".bat", ".sh"}
    
    if suffix in text_exts:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except:
            return "[Could not read text file]"

    if suffix == ".zip":
        try:
            with zipfile.ZipFile(path) as z:
                files = []
                for name in z.namelist()[:15]:
                    if not name.endswith("/"):
                        data = z.read(name)
                        try:
                            text = data.decode("utf-8")
                        except:
                            text = f"[binary, {len(data)} bytes]"
                        files.append(f"--- {name} ---\n{text}")
                return "\n\n".join(files) + f"\n[Zip had {len(z.namelist())} files total]"
        except:
            return "[Corrupted zip]"

    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf"}:
        return f"[Attached Media: {path.name}] (Vision processing not yet enabled)"

    return f"[Attached binary file: {path.name}]"

def short_id(s: str, n: int = 20) -> str:
    """Truncate a model ID for display"""
    if len(s) <= n:
        return s
    return s[:n//2-1] + "…" + s[-(n//2):]

def get_initials(text: str) -> str:
    """Generate 2-char initials from a name"""
    parts = text.replace(":", " ").replace("-", " ").replace("_", " ").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    else:
        return text[:2].upper()

def repair_json(json_str: str) -> str:
    """
    Aggressively repair malformed JSON from small models.
    """
    s = json_str.strip()
    
    # Remove markdown fences
    s = re.sub(r'```(?:json)?', '', s)
    
    # Find JSON object/array
    brace_start = s.find("{")
    brace_end = s.rfind("}")
    
    if brace_start != -1 and brace_end > brace_start:
        s = s[brace_start:brace_end+1]
    
    # Fix single quotes ONLY around keys (not in content like contractions)
    # This regex only matches 'key': patterns and converts to "key":
    s = re.sub(r"['](\w+)[']\s*:", r'"\1":', s)
    
    # Fix missing commas
    s = re.sub(r'(?<=\d)\s+(?=")', ', ', s)
    s = re.sub(r'(?<=")\s+(?=")', ', ', s)
    
    return s

# ====================== How-To Manual Dialog ======================

class HowToManualDialog(QtWidgets.QDialog):
    """Comprehensive how-to manual for Kraken Kouncil"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Kraken Kouncil - How to Use")
        self.setMinimumSize(900, 700)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("🏛️ KRAKEN KOUNCIL USER MANUAL")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #FFD700; padding: 10px;")
        layout.addWidget(title)
        
        # Scrollable content
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        
        # Manual content
        manual_html = """
        <style>
            body { font-family: 'Segoe UI', Arial; font-size: 11pt; line-height: 1.6; }
            h2 { color: #4ECDC4; border-bottom: 2px solid #4ECDC4; padding-bottom: 5px; margin-top: 20px; }
            h3 { color: #FFD700; margin-top: 15px; }
            .feature { background: rgba(78, 205, 196, 0.1); padding: 10px; border-left: 3px solid #4ECDC4; margin: 10px 0; }
            .tip { background: rgba(255, 215, 0, 0.1); padding: 10px; border-left: 3px solid #FFD700; margin: 10px 0; }
            .warning { background: rgba(255, 107, 107, 0.1); padding: 10px; border-left: 3px solid #FF6B6B; margin: 10px 0; }
            code { background: rgba(255, 255, 255, 0.1); padding: 2px 6px; border-radius: 3px; font-family: 'Consolas', monospace; }
            ul { margin-left: 20px; }
            li { margin: 5px 0; }
        </style>
        
        <h2>🎯 What is Kraken Kouncil?</h2>
        <p>Kraken Kouncil orchestrates multiple AI models to collaborate on answering your questions. Models debate, vote, and compete to provide the best answer.</p>
        
        <h2>🚀 Quick Start</h2>
        
        <h3>1. Discover Models</h3>
        <div class="feature">
        <p>Click <b>"🔍 Discover"</b> to scan LM Studio and Ollama for available models.</p>
        <p>Models appear as a <b>compact list</b> in the left sidebar with checkboxes.</p>
        </div>
        
        <h3>2. Select Council Members (Left Sidebar)</h3>
        <div class="feature">
        <p>Check the boxes next to models you want in your council.</p>
        <p>Selected models instantly appear in the <b>⚔️ COUNCIL ARENA</b> as detailed, animated cards.</p>
        <p><b>This is the hybrid design:</b> Compact selection list + detailed arena cards for chosen models only!</p>
        </div>
        
        <h3>3. Assign Personalities (Arena Cards)</h3>
        <div class="feature">
        <p>Each arena card has a <b>visible personality dropdown</b> - just click and select!</p>
        <p><b>No menu popups needed</b> - it's a standard dropdown for quick one-click selection:</p>
        <ul>
            <li>🔍 Meticulous Fact-Checker</li>
            <li>⚙️ Pragmatic Engineer</li>
            <li>⚠️ Cautious Risk Assessor</li>
            <li>👨‍🏫 Clear Teacher</li>
            <li>📊 Data Analyst</li>
            <li>🧠 Systems Thinker</li>
            <li>🎨 Creative Muse</li>
            <li>😈 Devil's Advocate</li>
        </ul>
        </div>
        
        <h3>4. Ask Your Question</h3>
        <div class="feature">
        <p>Type at the bottom and press <b>Enter</b> or click <b>"🐙 ASK KOUNCIL"</b></p>
        </div>
        
        <h2>🗣️ NEW: Agentic Debate System</h2>
        
        <div class="feature">
        <p><b>Enable in Settings:</b> ⚙️ → Debate Settings → Check "Enable Agentic Debate"</p>
        <p><b>Set Rounds:</b> Choose 1-5 rounds (default: 2)</p>
        <p><b>How it works:</b></p>
        <ol>
            <li>Models generate initial answers</li>
            <li><b>Debate Round 1/X:</b> Each model critiques all responses</li>
            <li><b>Refinement:</b> Models improve their answers based on critiques</li>
            <li><b>Repeat</b> for configured rounds</li>
            <li>Final voting on refined answers</li>
        </ol>
        </div>
        
        <div class="tip">
        <b>💡 Progress Tracking:</b> During debate, each model's status shows exactly where they are:<br>
        • "🗣️ Debate Round 2/3" - Overall progress announcement<br>
        • "💭 Critiquing (2/3)" - Analyzing responses<br>
        • "🔧 Refining (2/3)" - Improving their answer<br>
        This helps you estimate remaining time!
        </div>
        
        <div class="tip">
        <b>💡 When to Use Debate:</b> Enable for complex analytical questions. For simple queries, standard mode is faster.
        </div>
        
        <div class="warning">
        <b>⚠️ Performance:</b> Debate mode takes longer. 2 rounds with 4 models = ~20 API calls vs 8 in standard mode.
        </div>
        
        <h2>🎭 Arena Features</h2>
        
        <h3>Enhanced Arena Cards</h3>
        <p>When you select a model, it "enters the arena" as a detailed card showing:</p>
        <ul>
            <li><b>Pulsing Avatar</b> - Animated while model is thinking</li>
            <li><b>Backend Badge</b> - 🎬 LM Studio or 🦙 Ollama</li>
            <li><b>Model Name</b> - Up to 25 characters (more readable!)</li>
            <li><b>Personality Dropdown</b> - Visible, one-click selection</li>
            <li><b>Status</b> - Real-time updates with round progress</li>
            <li><b>Response Area</b> - Live streaming text (100-150px height)</li>
            <li><b>Score Badge</b> - Accumulates votes with flash effects</li>
        </ul>
        
        <h3>Why the Hybrid Design is Better</h3>
        <div class="tip">
        <b>Left Sidebar = Selection:</b> Compact checkbox list shows ALL available models without clutter<br>
        <b>Arena = Detail:</b> Only selected models get full cards with all information<br><br>
        You don't need details about models you're not using, but once they enter the arena, you get EVERYTHING!
        </div>
        
        <h3>Live Status Updates</h3>
        <p>Track each model's progress in real-time:</p>
        <ul>
            <li><b>🔄 Generating...</b> - Creating initial response</li>
            <li><b>✅ Complete</b> - Generation finished</li>
            <li><b>🗣️ Debate Round X/Y</b> - Starting debate round</li>
            <li><b>💭 Critiquing (X/Y)</b> - Analyzing responses</li>
            <li><b>🔧 Refining (X/Y)</b> - Improving answer</li>
            <li><b>🗳️ Voting...</b> - Scoring responses</li>
            <li><b>✅ Voted</b> - Voting complete</li>
        </ul>
        
        <h2>🎨 Model Icons & Visual Identity</h2>
        
        <div class="feature">
        <p><b>Smart Icon System:</b> Models are automatically identified and displayed with beautiful visuals!</p>
        <p><b>Three-tier fallback system:</b></p>
        <ol>
            <li><b>PNG Icons</b> - If you have custom icons in the <code>/icons</code> folder (best!)</li>
            <li><b>Emoji Fallbacks</b> - Beautiful built-in emojis for recognized families (great!)</li>
            <li><b>Initials</b> - Two-letter abbreviation for unknown models (functional!)</li>
        </ol>
        </div>
        
        <h3>Recognized Model Families</h3>
        <div class="tip">
        <p>The system automatically detects these families and shows their emoji:</p>
        <ul>
            <li>🦙 <b>Llama</b> - llama, llama2, llama3, llama4</li>
            <li>💎 <b>CodeLlama</b> - codellama</li>
            <li>💚 <b>Gemma</b> - gemma, gemma2, gemma3</li>
            <li>🌙 <b>Qwen</b> - qwen, qwen2, qwen2.5, qwen3</li>
            <li>🔮 <b>DeepSeek</b> - deepseek, deepseek-v2, deepseek-v3</li>
            <li>🌪️ <b>Mistral</b> - mistral, mixtral</li>
            <li>🔵 <b>Phi</b> - phi, phi-2, phi-3, phi-4</li>
            <li>🦅 <b>Falcon</b> - falcon</li>
            <li>🐉 <b>Yi</b> - yi models</li>
        </ul>
        <p><b>Example:</b> "llama3.2:3b" automatically shows 🦙, "gemma2:2b" shows 💚</p>
        </div>
        
        <h3>Custom Icons (Optional)</h3>
        <div class="tip">
        <p>Want even better visuals? Add PNG icons!</p>
        <ol>
            <li>Create an <code>/icons</code> folder next to the app</li>
            <li>Add PNG files named: <code>llama.png</code>, <code>gemma.png</code>, etc.</li>
            <li>Recommended size: 128x128 pixels with transparent background</li>
            <li>That's it! Icons load automatically</li>
        </ol>
        <p>The icons use circular clipping and proper layering for a perfect look!</p>
        </div>
        
        <h2>🌐 Web Search Integration</h2>
        
        <div class="feature">
        <p><b>NEW: Real-time web information!</b> Your council can search Google before answering, giving models access to current events, prices, news, and any time-sensitive information.</p>
        </div>
        
        <h3>Setting Up Web Search</h3>
        <div class="feature">
        <p><b>Step 1: Get Google PSE Credentials</b></p>
        <ol>
            <li>Go to <b>Settings</b> (⚙️) → <b>Web Search Settings</b></li>
            <li>Click <b>"How to get API credentials?"</b> for detailed instructions</li>
            <li>Get API Key from Google Cloud Console</li>
            <li>Get Search Engine ID from Programmable Search Engine</li>
            <li>Enable the Custom Search API</li>
        </ol>
        
        <p><b>Step 2: Configure in Kraken Kouncil</b></p>
        <ol>
            <li>Paste your API Key</li>
            <li>Paste your Search Engine ID</li>
            <li>Set Max Results (1-10, default: 5)</li>
            <li>Check <b>"Enable Web Search"</b></li>
            <li>Click <b>💾 Save</b></li>
        </ol>
        </div>
        
        <h3>How Web Search Works</h3>
        <div class="tip">
        <p><b>When enabled:</b></p>
        <ol>
            <li>You ask a question</li>
            <li>System shows <b>"🔍 Searching web..."</b> on all cards</li>
            <li>Google PSE searches for relevant information</li>
            <li>Results are formatted with title, URL, and snippet</li>
            <li>Search context is prepended to your question</li>
            <li>Models generate with access to current information!</li>
        </ol>
        </div>
        
        <h3>When to Use Web Search</h3>
        <div class="tip">
        <p><b>✅ Great for:</b></p>
        <ul>
            <li>Current events and news ("What happened today?")</li>
            <li>Prices and markets ("Bitcoin price now?")</li>
            <li>Weather ("Weather in Tokyo?")</li>
            <li>Recent developments ("Latest AI news?")</li>
            <li>Sports scores ("Who won yesterday?")</li>
        </ul>
        
        <p><b>❌ Not needed for:</b></p>
        <ul>
            <li>Math problems</li>
            <li>Code generation</li>
            <li>Creative writing</li>
            <li>Historical facts</li>
        </ul>
        </div>
        
        <h3>Pricing & Free Tier</h3>
        <div class="feature">
        <p><b>💰 Google PSE Pricing:</b></p>
        <ul>
            <li><b>100 queries per day</b> - Completely FREE!</li>
            <li>$5 per 1,000 queries after that</li>
            <li>Perfect for personal use!</li>
        </ul>
        <p><b>Tip:</b> Disable web search when not needed to save your free quota!</p>
        </div>
        
        <h2>🗳️ Voting System</h2>
        
        <div class="feature">
        <p>After responses, models score each other on 5 criteria (1-10 each):</p>
        <ul>
            <li><b>Relevance</b> - Does it answer the question?</li>
            <li><b>Clarity</b> - Well-written and understandable?</li>
            <li><b>Completeness</b> - Thorough answer?</li>
            <li><b>Accuracy</b> - Facts and reasoning correct?</li>
            <li><b>Helpfulness</b> - Actionable insight?</li>
        </ul>
        <p>Max score per judge: 50 points. Winner = highest total.</p>
        </div>
        
        <div class="warning">
        <b>⚠️ Anti-Lazy Rule:</b> Responses under 20 words get Completeness = 1
        </div>
        
        <h2>📊 Stats Panel</h2>
        
        <p>Left sidebar shows:</p>
        <ul>
            <li><b>Status:</b> Current operation</li>
            <li><b>Selected:</b> How many models in arena</li>
            <li><b>Phase:</b> Generating/Voting/Complete</li>
            <li><b>Decision:</b> Consensus/Decision/Tie indicator</li>
        </ul>
        
        <h2>🏆 Leaderboard</h2>
        
        <p>Tracks historical wins. Click "Clear Stats" to reset (requires confirmation).</p>
        
        <h2>⚙️ Settings</h2>
        
        <h3>Server URLs</h3>
        <p>Configure LM Studio (default: localhost:1234) and Ollama (default: localhost:11434)</p>
        
        <h3>Debate Configuration</h3>
        <p>Enable/disable debate mode and set rounds (1-5, default: 2)</p>
        
        <h3>Performance</h3>
        <p>Max Concurrent: How many models generate simultaneously (1-10)</p>
        
        <h2>🔥 Pro Tips</h2>
        
        <div class="tip">
        <b>🎨 Hybrid Design Benefits:</b>
        <ul>
            <li><b>One-Click Personas:</b> Dropdown visible on arena cards - no menu popup needed!</li>
            <li><b>More Info:</b> Cards show backend badge, 25-char names, bigger response areas</li>
            <li><b>Efficient Space:</b> Unselected models stay in compact sidebar, only chosen ones get detailed cards</li>
            <li><b>Clear Workflow:</b> Sidebar = Selection, Arena = Configuration & Battle</li>
        </ul>
        </div>
        
        <div class="tip">
        <b>Personality Combos:</b>
        <ul>
            <li><b>Balanced Council:</b> Fact-Checker + Engineer + Systems Thinker + Creative Muse</li>
            <li><b>Critical Thinking:</b> Devil's Advocate + Risk Assessor + Fact-Checker</li>
            <li><b>Education:</b> Clear Teacher + Systems Thinker + Data Analyst</li>
        </ul>
        </div>
        
        <div class="tip">
        <b>Performance Modes:</b>
        <ul>
            <li><b>Fast:</b> 2-3 models, no debate, concurrency=2</li>
            <li><b>Quality:</b> 5-7 models, 2-round debate, concurrency=3</li>
            <li><b>Maximum Insight:</b> 8+ models, 3-round debate, concurrency=3</li>
        </ul>
        </div>
        
        <h2>📎 File Attachments</h2>
        
        <p>Click "📎 Attach" to include context files (10MB limit):</p>
        <ul>
            <li>Supported: .txt, .py, .json, .md, .log, .csv, .yaml, .html, .css, .js, .zip</li>
            <li>Coming soon: Images and PDFs with vision</li>
        </ul>
        
        <h2>🐛 Troubleshooting</h2>
        
        <div class="warning">
        <b>Models not found?</b> Verify LM Studio/Ollama is running and URLs are correct in Settings.
        </div>
        
        <div class="warning">
        <b>ERROR in responses?</b> Model may not be loaded or compatible with chat API.
        </div>
        
        <div class="warning">
        <b>Voting fails?</b> Small models (<3B) may struggle with JSON. Use larger models as voters.
        </div>
        
        <h2>⌨️ Keyboard Shortcuts</h2>
        
        <p><b>Enter</b> in text box - Submit question (Shift+Enter for new line)</p>
        
        <p style="text-align: center; margin-top: 30px; color: #FFD700; font-size: 14pt;">
        <b>🏛️ May the wisest AI prevail! 🏛️</b>
        </p>
        """
        
        text_browser = QtWidgets.QTextBrowser()
        text_browser.setHtml(manual_html)
        text_browser.setOpenExternalLinks(True)
        content_layout.addWidget(text_browser)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QtWidgets.QPushButton("✅ Got It!")
        close_btn.setStyleSheet("font-size: 12pt; font-weight: bold; padding: 8px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

# ====================== Discovery Worker ======================

class DiscoveryWorker(QThread):
    """Worker thread to discover models on local servers"""
    progress = Signal(str)
    finished = Signal(list, dict)
    
    def __init__(self, lm_url: str, ollama_url: str, lm_enabled: bool, ollama_enabled: bool):
        super().__init__()
        self.lm_url = lm_url
        self.ollama_url = ollama_url
        self.lm_enabled = lm_enabled
        self.ollama_enabled = ollama_enabled
    
    def run(self):
        models = []
        backends = {}
        
        urls = []
        if self.lm_enabled:
            urls.append((self.lm_url, "lmstudio"))
        if self.ollama_enabled:
            urls.append((self.ollama_url, "ollama"))
        
        if not urls:
            self.progress.emit("❌ No backends enabled")
            self.finished.emit(models, backends)
            return
        
        found_any = False
        for url, backend_type in urls:
            self.progress.emit(f"🔍 Checking {backend_type} at {url}...")
            
            if self.test_url(url):
                found_any = True
                discovered = self.fetch_models(url, backend_type)
                self.progress.emit(f"✅ Found {len(discovered)} on {backend_type}")
                
                for m in discovered:
                    mid = m["id"]
                    if mid not in backends:
                        models.append(m)
                        backends[mid] = {"url": url, "type": backend_type}
            else:
                self.progress.emit(f"❌ {backend_type} not responding")
        
        if not found_any:
            self.progress.emit("❌ No servers found")
        else:
            self.progress.emit(f"✅ Discovered {len(models)} model(s)")
        
        self.finished.emit(models, backends)
    
    def test_url(self, url: str) -> bool:
        try:
            r = requests.get(url.rstrip("/")+"/v1/models", timeout=2)
            return r.ok
        except:
            try:
                r = requests.get(url.rstrip("/")+"/api/tags", timeout=2)
                return r.ok
            except:
                return False
    
    def fetch_models(self, url: str, backend: str) -> List[dict]:
        models = []
        try:
            if backend == "ollama":
                data = requests.get(url.rstrip("/")+"/api/tags", timeout=5).json()
                for m in data.get("models", []):
                    name = m.get("name") or m.get("model")
                    if name:
                        models.append({"id": name, "backend": "ollama", "url": url})
            else:
                data = requests.get(url.rstrip("/")+"/v1/models", timeout=5).json()
                for m in data.get("data", []):
                    mid = m.get("id")
                    if mid:
                        models.append({"id": mid, "backend": "lmstudio", "url": url})
        except:
            pass
        return models

# ====================== UI Components ======================

class SubmitTextEdit(QtWidgets.QPlainTextEdit):
    """Custom TextEdit that submits on Enter (Shift+Enter for new line)"""
    submit_requested = Signal()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit_requested.emit()
        else:
            super().keyPressEvent(event)

class ModelAvatar(QtWidgets.QWidget):
    """Circular avatar with model family icon/emoji or initials and pulsing effect"""
    def __init__(self, model_id: str, color: str, size: int = 60):
        super().__init__()
        self.model_id = model_id
        self.color = QColor(color)
        self.initials = get_initials(model_id)
        self.pulsing = False
        self.pulse_value = 0
        self.setFixedSize(size, size)
        self.size = size
        
        # Try to load model family icon, get emoji fallback
        self.icon_pixmap, self.fallback_emoji = self.load_model_icon()
        
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.update_pulse)
    
    def load_model_icon(self):
        """Try to load icon for model family, return (pixmap, emoji_fallback)"""
        # Detect model family from model_id (case-insensitive)
        model_lower = self.model_id.lower()
        
        # Map of model families to (icon_name, emoji_fallback)
        family_map = {
            'codellama': ('codellama', '💎'),
            'llama': ('llama', '🦙'),
            'gemma': ('gemma', '💚'),
            'qwen': ('qwen', '🌙'),
            'deepseek': ('deepseek', '🔮'),
            'mistral': ('mistral', '🌪️'),
            'phi': ('phi', '🔵'),
            'vicuna': ('vicuna', '🦙'),
            'falcon': ('falcon', '🦅'),
            'yi': ('yi', '🐉'),
        }
        
        # Check each family (sorted by length to match codellama before llama)
        for family in sorted(family_map.keys(), key=len, reverse=True):
            if family in model_lower:
                icon_name, emoji = family_map[family]
                
                # Try both .png and .PNG for cross-platform compatibility
                for ext in ['.png', '.PNG']:
                    icon_path = APP_DIR / 'icons' / f'{icon_name}{ext}'
                    
                    # Try to load PNG icon first
                    if icon_path.exists():
                        try:
                            pixmap = QtGui.QPixmap(str(icon_path))
                            if not pixmap.isNull():
                                # Scale to fit circle with some padding (85% for better visibility)
                                scaled = pixmap.scaled(
                                    int(self.size * 0.85), 
                                    int(self.size * 0.85),
                                    Qt.KeepAspectRatio, 
                                    Qt.SmoothTransformation
                                )
                                return scaled, None  # PNG found, no emoji needed
                        except Exception as e:
                            print(f"Failed to load icon for {family}: {e}")
                
                # PNG not found or failed, return emoji fallback
                return None, emoji
        
        # No family match, return no icon and no emoji (will use initials)
        return None, None
    
    def start_pulse(self):
        if not self.pulsing:
            self.pulsing = True
            self.pulse_value = 0
            self.pulse_timer.start(50)
    
    def stop_pulse(self):
        if self.pulsing:
            self.pulsing = False
            self.pulse_timer.stop()
            self.pulse_value = 0
            self.update()
    
    def update_pulse(self):
        if self.pulsing:
            self.pulse_value = (self.pulse_value + 0.1) % 1.0
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        radius = min(rect.width(), rect.height()) / 2 - 4
        
        # Pulse ring (drawn first, behind everything)
        if self.pulsing:
            pulse_radius = radius + (10 * abs(0.5 - self.pulse_value))
            pulse_color = QColor(self.color)
            pulse_color.setAlpha(int(100 * (1 - abs(0.5 - self.pulse_value) * 2)))
            painter.setBrush(QBrush(pulse_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(center_x, center_y), pulse_radius, pulse_radius)
        
        # Main circle background (colored background for transparency)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Set circular clipping region so icon doesn't exceed circle
        from PySide6.QtGui import QPainterPath
        clip_path = QPainterPath()
        clip_path.addEllipse(QPointF(center_x, center_y), radius, radius)
        painter.setClipPath(clip_path)
        
        # Draw content (PNG icon / Emoji / Initials) - will be clipped to circle
        if self.icon_pixmap:
            # Draw PNG icon (transparency will show colored background)
            icon_x = (rect.width() - self.icon_pixmap.width()) / 2
            icon_y = (rect.height() - self.icon_pixmap.height()) / 2
            painter.drawPixmap(int(icon_x), int(icon_y), self.icon_pixmap)
        elif self.fallback_emoji:
            # Draw emoji (nice and big!)
            painter.setPen(QColor("white"))
            font = QFont("Segoe UI Emoji", int(radius * 0.9))
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, self.fallback_emoji)
        else:
            # Draw initials as last resort
            painter.setPen(QColor("white"))
            font = QFont("Arial", int(radius / 2), QFont.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, self.initials)
        
        # Remove clipping for border
        painter.setClipping(False)
        
        # Draw circle border ON TOP to frame everything nicely
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#222"), 2))
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

class ArenaModelCard(QtWidgets.QWidget):
    """Card widget for a model in the arena - Enhanced design with more info"""
    persona_changed = Signal(str, str)
    
    def __init__(self, model_id: str, backend: str, color: str, wins: int):
        super().__init__()
        self.model_id = model_id
        self.color = color
        self.current_score = 0
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # --- Top Row: Avatar + Score ---
        top_row = QtWidgets.QHBoxLayout()
        self.avatar = ModelAvatar(model_id, color, 60)
        top_row.addWidget(self.avatar)
        
        top_row.addStretch()
        
        self.score_badge = QtWidgets.QLabel("0")
        self.score_badge.setStyleSheet(f"""
            background: rgba(0,0,0,0.5);
            color: {color};
            border: 2px solid {color};
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
            font-size: 16pt;
        """)
        self.score_badge.setAlignment(Qt.AlignCenter)
        self.score_badge.setFixedWidth(80)
        top_row.addWidget(self.score_badge)
        layout.addLayout(top_row)
        
        # --- Name ---
        name_label = QtWidgets.QLabel(short_id(model_id, 25))
        name_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11pt;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # --- Backend Badge ---
        backend_badge = QtWidgets.QLabel("🎬 LM Studio" if backend == "lmstudio" else "🦙 Ollama")
        backend_badge.setStyleSheet("font-size: 9pt; color: #888; padding: 2px;")
        layout.addWidget(backend_badge)
        
        # --- Persona Dropdown (Visible!) ---
        persona_layout = QtWidgets.QHBoxLayout()
        persona_layout.addWidget(QtWidgets.QLabel("Role:"))
        
        self.persona_combo = QtWidgets.QComboBox()
        self.persona_combo.setStyleSheet(f"""
            QComboBox {{
                background: rgba(0, 0, 0, 0.3);
                color: white;
                border: 1px solid {color};
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {color};
            }}
        """)
        for p in DEFAULT_PERSONAS:
            self.persona_combo.addItem(f"{p['emoji']} {p['name']}")
        self.persona_combo.currentTextChanged.connect(self.on_persona_change)
        persona_layout.addWidget(self.persona_combo, stretch=1)
        layout.addLayout(persona_layout)
        
        # --- Status ---
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("""
            color: #888; font-size: 9pt;
            background: rgba(0, 0, 0, 0.3);
            padding: 5px; border-radius: 4px;
            font-weight: bold;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # --- Text Response Area ---
        self.response_area = QtWidgets.QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setMinimumHeight(100)
        self.response_area.setMaximumHeight(150)
        self.response_area.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(0, 0, 0, 0.4);
                color: white;
                border: 2px solid {color};
                border-radius: 6px;
                padding: 8px;
                font-size: 9pt;
                line-height: 1.4;
            }}
        """)
        self.response_area.setPlaceholderText("Response will appear here...")
        layout.addWidget(self.response_area, stretch=1)
        
        # --- Main Styling ---
        self.setStyleSheet(f"""
            ArenaModelCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(40, 40, 40, 0.95), 
                    stop:1 rgba(25, 25, 25, 0.95));
                border: 3px solid {color};
                border-radius: 12px;
            }}
        """)
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)
    
    def on_persona_change(self, text):
        # Extract persona name from "emoji name" format
        parts = text.split(" ", 1)
        persona_name = parts[1] if len(parts) > 1 else "None"
        self.persona_changed.emit(self.model_id, persona_name if persona_name != "None" else "")
    
    def set_persona(self, name: str, emoji: str):
        # Find and select the matching persona in combo box
        for i in range(self.persona_combo.count()):
            if name in self.persona_combo.itemText(i):
                self.persona_combo.setCurrentIndex(i)
                break
    
    def update_status(self, text: str, state: str = "working"):
        self.status_label.setText(text)
        colors = {"working": "#FFE66D", "done": "#4ECDC4", "error": "#FF6B6B", "idle": "#888"}
        self.status_label.setStyleSheet(f"""
            color: {colors.get(state, '#888')};
            font-size: 9pt; font-weight: bold;
            background: rgba(0, 0, 0, 0.3);
            padding: 4px; border-radius: 4px;
        """)
        
        if state == "working":
            self.avatar.start_pulse()
        else:
            self.avatar.stop_pulse()

    def add_score(self, points: int):
        self.current_score += points
        self.score_badge.setText(f"{self.current_score}")
        
        # Flash effect
        if points > 0:
            self.score_badge.setStyleSheet(f"""
                background: #4ECDC4; color: black;
                border: 1px solid {self.color};
                border-radius: 4px; padding: 4px 8px;
                font-weight: bold; font-size: 14pt;
            """)
            QTimer.singleShot(500, lambda: self.score_badge.setStyleSheet(f"""
                background: rgba(0,0,0,0.5); color: {self.color};
                border: 1px solid {self.color};
                border-radius: 4px; padding: 4px 8px;
                font-weight: bold; font-size: 14pt;
            """))

    def reset_score(self):
        self.current_score = 0
        self.score_badge.setText("0")
    
    def append_response(self, text: str):
        self.response_area.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.response_area.insertPlainText(text)
    
    def clear_response(self):
        self.response_area.clear()

class ModelListItem(QtWidgets.QWidget):
    """Sidebar list item"""
    selection_changed = Signal(str, bool)
    
    def __init__(self, model_id: str, color: str):
        super().__init__()
        self.model_id = model_id
        
        # Prevent the list item itself from being squashed vertically
        self.setMinimumHeight(38)
        
        layout = QtWidgets.QHBoxLayout(self)
        
        # Give breathing room on the left (10px) so it's not hugging the wall
        # Format: (Left, Top, Right, Bottom)
        layout.setContentsMargins(10, 2, 2, 2)
        
        # Keep spacing between elements
        layout.setSpacing(8)
        
        self.checkbox = QtWidgets.QCheckBox()
        
        # --- THE CRITICAL FIX ---
        # Force the checkbox to reserve width so it doesn't get clipped
        self.checkbox.setFixedWidth(22)
        # ------------------------
        
        self.checkbox.stateChanged.connect(
            lambda: self.selection_changed.emit(model_id, self.checkbox.isChecked()))
        layout.addWidget(self.checkbox)
        
        indicator = QtWidgets.QLabel("●")
        indicator.setStyleSheet(f"color: {color}; font-size: 14pt;")
        layout.addWidget(indicator)
        
        name = QtWidgets.QLabel(short_id(model_id, 20))
        name.setStyleSheet("color: white; font-size: 9pt;")
        name.setWordWrap(True)
        layout.addWidget(name, stretch=1)
        
        self.setStyleSheet("""
            ModelListItem {
                background: rgba(40, 40, 40, 0.5);
                border-radius: 4px; margin: 2px;
            }
            ModelListItem:hover { background: rgba(60, 60, 60, 0.7); }
        """)

class StatsPanel(QtWidgets.QWidget):
    """Left sidebar stats"""
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.labels = {}
        stats = [
            ("status", "Status:", "Ready"),
            ("models", "Selected:", "0"),
            ("phase", "Phase:", "Idle"),
            ("controversy", "Decision:", ""),
        ]
        
        for key, label_text, default_value in stats:
            row = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(label_text)
            label.setStyleSheet("color: #AAA; font-weight: bold;")
            value = QtWidgets.QLabel(default_value)
            value.setStyleSheet("color: white; font-size: 11pt;")
            row.addWidget(label)
            row.addWidget(value, stretch=1)
            layout.addLayout(row)
            self.labels[key] = value
        
        layout.addStretch()
        self.setStyleSheet("""
            StatsPanel {
                background: rgba(30, 30, 30, 0.95);
                border: 2px solid #4ECDC4;
                border-radius: 8px;
            }
        """)
        self.setMinimumWidth(200)
    
    def update_stat(self, key: str, value: str, color: str = "white"):
        if key in self.labels:
            self.labels[key].setText(value)
            self.labels[key].setStyleSheet(f"color: {color}; font-size: 11pt;")

class GPUMonitor(QtWidgets.QWidget):
    """GPU monitoring widget with color-coded stats"""
    def __init__(self):
        super().__init__()
        self.gpu_available = False
        self.pynvml = None
        self.handle = None
        
        # Try to initialize NVIDIA monitoring
        try:
            import pynvml
            self.pynvml = pynvml
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # First GPU
            self.gpu_available = True
        except Exception as e:
            print(f"GPU monitoring not available: {e}")
        
        self.setup_ui()
        
        # Update timer
        if self.gpu_available:
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_stats)
            self.timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QtWidgets.QLabel("🎮 GPU MONITOR")
        header.setStyleSheet("color: #4ECDC4; font-weight: bold; font-size: 11pt;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        if not self.gpu_available:
            no_gpu = QtWidgets.QLabel("No GPU detected")
            no_gpu.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
            no_gpu.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_gpu)
        else:
            # GPU Name
            try:
                gpu_name = self.pynvml.nvmlDeviceGetName(self.handle)
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode('utf-8')
                name_label = QtWidgets.QLabel(gpu_name)
                name_label.setStyleSheet("color: white; font-size: 9pt; font-weight: bold;")
                name_label.setWordWrap(True)
                layout.addWidget(name_label)
            except:
                pass
            
            # Stats labels
            self.temp_label = QtWidgets.QLabel("Temp: --°C")
            self.util_label = QtWidgets.QLabel("Usage: --%")
            self.mem_label = QtWidgets.QLabel("Memory: -- / -- MB")
            
            for label in [self.temp_label, self.util_label, self.mem_label]:
                label.setStyleSheet("color: white; font-size: 10pt; padding: 2px;")
                layout.addWidget(label)
        
        layout.addStretch()
        
        self.setStyleSheet("""
            GPUMonitor {
                background: rgba(30, 30, 30, 0.95);
                border: 2px solid #4ECDC4;
                border-radius: 8px;
            }
        """)
        self.setMinimumWidth(200)
        self.setMaximumHeight(180)
    
    def update_stats(self):
        if not self.gpu_available or not self.handle:
            return
        
        try:
            # Temperature
            temp = self.pynvml.nvmlDeviceGetTemperature(self.handle, 0)  # 0 = GPU temp
            temp_color = self.get_temp_color(temp)
            self.temp_label.setText(f"Temp: {temp}°C")
            self.temp_label.setStyleSheet(f"color: {temp_color}; font-size: 10pt; padding: 2px; font-weight: bold;")
            
            # Utilization
            util = self.pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            util_color = self.get_util_color(util.gpu)
            self.util_label.setText(f"Usage: {util.gpu}%")
            self.util_label.setStyleSheet(f"color: {util_color}; font-size: 10pt; padding: 2px;")
            
            # Memory
            mem_info = self.pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            mem_used_mb = mem_info.used / 1024 / 1024
            mem_total_mb = mem_info.total / 1024 / 1024
            mem_percent = (mem_info.used / mem_info.total) * 100
            mem_color = self.get_util_color(mem_percent)
            self.mem_label.setText(f"Memory: {mem_used_mb:.0f} / {mem_total_mb:.0f} MB")
            self.mem_label.setStyleSheet(f"color: {mem_color}; font-size: 10pt; padding: 2px;")
            
        except Exception as e:
            print(f"Error updating GPU stats: {e}")
    
    def get_temp_color(self, temp):
        """Color code temperature"""
        if temp < 60:
            return "#4ECDC4"  # Cool cyan
        elif temp < 70:
            return "#A8E6CF"  # Light green
        elif temp < 80:
            return "#FFD93D"  # Yellow
        elif temp < 85:
            return "#FFB347"  # Orange
        else:
            return "#FF6B6B"  # Red/hot
    
    def get_util_color(self, percent):
        """Color code utilization"""
        if percent < 30:
            return "#4ECDC4"  # Cyan
        elif percent < 60:
            return "#A8E6CF"  # Green
        elif percent < 80:
            return "#FFD93D"  # Yellow
        else:
            return "#FFB347"  # Orange
    
    def closeEvent(self, event):
        """Cleanup on close"""
        if self.gpu_available and self.pynvml:
            try:
                self.pynvml.nvmlShutdown()
            except:
                pass
        event.accept()

class Leaderboard(QtWidgets.QWidget):
    """Sidebar Leaderboard"""
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        header = QtWidgets.QLabel("🏆 LEADERBOARD")
        header.setStyleSheet("color: gold; font-weight: bold; font-size: 11pt;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: rgba(0, 0, 0, 0.3);
                border: none; color: white; font-size: 9pt;
            }
            QListWidget::item { padding: 4px; }
        """)
        layout.addWidget(self.list_widget)
        
        clear_btn = QtWidgets.QPushButton("Clear Stats")
        clear_btn.clicked.connect(self.clear_stats)
        layout.addWidget(clear_btn)
        
        self.setStyleSheet("""
            Leaderboard {
                background: rgba(30, 30, 30, 0.95);
                border: 2px solid gold;
                border-radius: 8px;
            }
        """)
        self.setMinimumWidth(200)
    
    def refresh(self):
        global leaderboard
        leaderboard = load_leaderboard()
        self.list_widget.clear()
        
        if not leaderboard:
            self.list_widget.addItem("No data yet")
            return
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (model, wins) in enumerate(leaderboard.items()):
            medal = medals[i] if i < 3 else "  "
            self.list_widget.addItem(f"{medal} {short_id(model, 15)}: {wins}")
    
    def clear_stats(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm",
            "Clear all stats?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM votes")
                conn.commit()
                conn.close()
                self.refresh()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed: {e}")

class ServerConfigDialog(QtWidgets.QDialog):
    """Settings dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_current()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        form = QtWidgets.QFormLayout()
        
        # LM Studio
        form.addRow(QtWidgets.QLabel("<b>LM Studio</b>"))
        self.lm_url = QtWidgets.QLineEdit()
        form.addRow("URL:", self.lm_url)
        self.lm_enabled = QtWidgets.QCheckBox("Enabled")
        form.addRow("", self.lm_enabled)
        
        form.addRow(QtWidgets.QLabel(""))
        
        # Ollama
        form.addRow(QtWidgets.QLabel("<b>Ollama</b>"))
        self.ollama_url = QtWidgets.QLineEdit()
        form.addRow("URL:", self.ollama_url)
        self.ollama_enabled = QtWidgets.QCheckBox("Enabled")
        form.addRow("", self.ollama_enabled)
        
        form.addRow(QtWidgets.QLabel(""))
        
        # Performance
        form.addRow(QtWidgets.QLabel("<b>Performance</b>"))
        self.concurrency = QtWidgets.QSpinBox()
        self.concurrency.setRange(1, 10)
        form.addRow("Max Concurrent:", self.concurrency)
        
        form.addRow(QtWidgets.QLabel(""))
        
        # Debate Settings
        form.addRow(QtWidgets.QLabel("<b>Debate Settings</b>"))
        self.debate_enabled = QtWidgets.QCheckBox("Enable Agentic Debate")
        form.addRow("", self.debate_enabled)
        self.debate_rounds = QtWidgets.QSpinBox()
        self.debate_rounds.setRange(1, 5)
        form.addRow("Debate Rounds:", self.debate_rounds)
        
        form.addRow(QtWidgets.QLabel(""))
        
        # Web Search Settings
        form.addRow(QtWidgets.QLabel("<b>🌐 Web Search Settings</b>"))
        self.web_search_enabled = QtWidgets.QCheckBox("Enable Web Search")
        form.addRow("", self.web_search_enabled)
        
        self.google_api_key = QtWidgets.QLineEdit()
        self.google_api_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.google_api_key.setPlaceholderText("Your Google API Key")
        form.addRow("API Key:", self.google_api_key)
        
        self.google_search_engine_id = QtWidgets.QLineEdit()
        self.google_search_engine_id.setPlaceholderText("Your Search Engine ID (cx)")
        form.addRow("Engine ID:", self.google_search_engine_id)
        
        self.max_search_results = QtWidgets.QSpinBox()
        self.max_search_results.setRange(1, 10)
        form.addRow("Max Results:", self.max_search_results)
        
        help_label = QtWidgets.QLabel('<a href="#help">How to get API credentials?</a>')
        help_label.setStyleSheet("color: #4ECDC4; font-size: 9pt;")
        help_label.linkActivated.connect(self.show_pse_help)
        form.addRow("", help_label)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QtWidgets.QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def load_current(self):
        self.lm_url.setText(settings.get("lm_studio_url", "http://localhost:1234"))
        self.ollama_url.setText(settings.get("ollama_url", "http://localhost:11434"))
        self.lm_enabled.setChecked(settings.get("lm_studio_enabled", True))
        self.ollama_enabled.setChecked(settings.get("ollama_enabled", True))
        self.concurrency.setValue(settings.get("max_concurrency", 3))
        self.debate_enabled.setChecked(settings.get("debate_enabled", False))
        self.debate_rounds.setValue(settings.get("debate_rounds", 2))
        self.web_search_enabled.setChecked(settings.get("web_search_enabled", False))
        self.google_api_key.setText(settings.get("google_api_key", ""))
        self.google_search_engine_id.setText(settings.get("google_search_engine_id", ""))
        self.max_search_results.setValue(settings.get("max_search_results", 5))
    
    def save_settings(self):
        save_settings({
            "lm_studio_url": self.lm_url.text().strip(),
            "ollama_url": self.ollama_url.text().strip(),
            "lm_studio_enabled": self.lm_enabled.isChecked(),
            "ollama_enabled": self.ollama_enabled.isChecked(),
            "max_concurrency": self.concurrency.value(),
            "debate_enabled": self.debate_enabled.isChecked(),
            "debate_rounds": self.debate_rounds.value(),
            "web_search_enabled": self.web_search_enabled.isChecked(),
            "google_api_key": self.google_api_key.text().strip(),
            "google_search_engine_id": self.google_search_engine_id.text().strip(),
            "max_search_results": self.max_search_results.value(),
        })
        global settings
        settings = load_settings()
        QtWidgets.QMessageBox.information(self, "Success", "Settings saved!")
        self.accept()
    
    def show_pse_help(self):
        """Show help dialog for getting Google PSE credentials"""
        help_text = """
        <h3>🌐 How to Get Google PSE Credentials</h3>
        
        <p><b>Step 1: Get API Key</b></p>
        <ol>
            <li>Go to: <a href="https://console.cloud.google.com/apis/credentials">Google Cloud Console</a></li>
            <li>Create a project (if you don't have one)</li>
            <li>Click "Create Credentials" → "API Key"</li>
            <li>Copy your API key and paste it above</li>
        </ol>
        
        <p><b>Step 2: Get Search Engine ID</b></p>
        <ol>
            <li>Go to: <a href="https://programmablesearchengine.google.com/">Programmable Search Engine</a></li>
            <li>Click "Add" to create a new search engine</li>
            <li>Choose "Search the entire web"</li>
            <li>Create it and copy the "Search engine ID" (cx parameter)</li>
        </ol>
        
        <p><b>Step 3: Enable Custom Search API</b></p>
        <ol>
            <li>Go to: <a href="https://console.cloud.google.com/apis/library">API Library</a></li>
            <li>Search for "Custom Search API"</li>
            <li>Click "Enable"</li>
        </ol>
        
        <p><b>💰 Free Tier:</b></p>
        <ul>
            <li>100 queries per day - FREE</li>
            <li>$5 per 1000 queries after that</li>
            <li>Perfect for personal use!</li>
        </ul>
        
        <p><b>🎯 How It Works:</b></p>
        <p>When enabled, your council will search Google before answering, giving models access to current information!</p>
        """
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Google PSE Setup Guide")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec()

# ====================== Main Application Window ======================

class KrakenKouncilWindow(QtWidgets.QMainWindow):
    # Signals to ensure thread safety
    status_signal = Signal(str)
    card_status_signal = Signal(str, str, str)  # mid, text, state
    error_signal = Signal(str)
    result_signal = Signal(tuple)
    stream_signal = Signal(str, str)
    vote_signal = Signal(str, str, int)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🐙 Kraken Kouncil v4.2 – Web Search + Icons + Agentic Debate")
        self.resize(1800, 1000)
        
        self.models = []
        self.model_list_items = {}
        self.model_cards = {}
        self.model_colors = {}
        self.model_backends = {}
        self.selected_models = set()
        self.personas = settings.get("persona_assignments", {})
        self.attached_content = ""
        self.attached_name = ""
        self.discovery_worker = None
        
        # Connect signals to slots
        self.status_signal.connect(self.update_status)
        self.card_status_signal.connect(self.handle_card_status)
        self.error_signal.connect(self.show_error)
        self.result_signal.connect(self.handle_result)
        self.stream_signal.connect(self.handle_stream_chunk)
        self.vote_signal.connect(self.handle_vote)
        
        self.build_ui()
    
    def build_ui(self):
        # Menu bar
        menubar = self.menuBar()
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        manual_action = help_menu.addAction("📖 How to Use")
        manual_action.triggered.connect(self.show_manual)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction("ℹ️ About")
        about_action.triggered.connect(self.show_about)
        
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setSpacing(12)
        
        # === Left Panel ===
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QtWidgets.QLabel("🐙 KRAKEN\nKOUNCIL")
        header.setStyleSheet("""
            font-size: 18pt; font-weight: bold; color: #4ECDC4;
            padding: 12px; background: rgba(78, 205, 196, 0.2);
            border-radius: 8px;
        """)
        header.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(header)
        
        btn_row = QtWidgets.QHBoxLayout()
        config_btn = QtWidgets.QPushButton("⚙️")
        config_btn.setFixedSize(40, 40)
        config_btn.clicked.connect(self.show_server_config)
        btn_row.addWidget(config_btn)
        
        # Big help button
        help_btn = QtWidgets.QPushButton("❓")
        help_btn.setFixedSize(40, 40)
        help_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff6b6b, stop:1 #e74c3c);
            }
        """)
        help_btn.setToolTip("Click for How-To Manual")
        help_btn.clicked.connect(self.show_manual)
        btn_row.addWidget(help_btn)
        
        discover_btn = QtWidgets.QPushButton("🔍 Discover")
        discover_btn.clicked.connect(self.auto_discover)
        btn_row.addWidget(discover_btn, stretch=1)
        left_layout.addLayout(btn_row)
        
        models_label = QtWidgets.QLabel("📋 Available Models")
        models_label.setStyleSheet("color: #FFE66D; font-weight: bold; font-size: 10pt; padding: 8px 4px;")
        left_layout.addWidget(models_label)
        
        model_scroll = QtWidgets.QScrollArea()
        model_scroll.setWidgetResizable(True)
        model_scroll.setStyleSheet("QScrollArea { border: 1px solid #444; background: rgba(0,0,0,0.3); border-radius: 4px; }")
        
        self.model_list_container = QtWidgets.QWidget()
        self.model_list_layout = QtWidgets.QVBoxLayout(self.model_list_container)
        self.model_list_layout.setSpacing(4)
        self.model_list_layout.addStretch()
        
        model_scroll.setWidget(self.model_list_container)
        left_layout.addWidget(model_scroll, stretch=1)
        
        self.stats_panel = StatsPanel()
        left_layout.addWidget(self.stats_panel)
        
        # GPU Monitor
        self.gpu_monitor = GPUMonitor()
        left_layout.addWidget(self.gpu_monitor)
        
        self.leaderboard = Leaderboard()
        self.leaderboard.refresh()
        left_layout.addWidget(self.leaderboard)
        
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(350)
        main_layout.addWidget(left_panel)
        
        # === Center Panel ===
        center_panel = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        arena_label = QtWidgets.QLabel("⚔️ COUNCIL ARENA")
        arena_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #FFE66D; padding: 8px;")
        arena_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(arena_label)
        
        # Arena Grid
        arena_scroll = QtWidgets.QScrollArea()
        arena_scroll.setWidgetResizable(True)
        arena_scroll.setStyleSheet("QScrollArea { border: 2px solid #444; border-radius: 8px; background: rgba(0,0,0,0.2); }")
        
        self.arena_container = QtWidgets.QWidget()
        self.arena_layout = QtWidgets.QGridLayout(self.arena_container)
        self.arena_layout.setSpacing(16)
        
        arena_scroll.setWidget(self.arena_container)
        center_layout.addWidget(arena_scroll, stretch=1)
        
        # Result Display
        self.winner_scroll = QtWidgets.QScrollArea()
        self.winner_scroll.setWidgetResizable(True)
        self.winner_scroll.setVisible(False)
        self.winner_scroll.setMaximumHeight(250)
        self.winner_scroll.setStyleSheet("QScrollArea { border: none; margin-top: 10px; }")
        
        self.winner_widget = QtWidgets.QWidget()
        winner_layout = QtWidgets.QVBoxLayout(self.winner_widget)
        winner_layout.setContentsMargins(0, 0, 0, 0)
        
        self.winner_label = QtWidgets.QTextEdit()
        self.winner_label.setReadOnly(True)
        self.winner_label.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:1 #2a5298);
                color: gold;
                font-size: 11pt; font-weight: bold;
                border: 3px solid gold;
                border-radius: 12px; padding: 16px;
            }
        """)
        winner_layout.addWidget(self.winner_label)
        self.winner_scroll.setWidget(self.winner_widget)
        center_layout.addWidget(self.winner_scroll)

        # Input Section
        input_label = QtWidgets.QLabel("💬 Ask the Kouncil")
        input_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #95E1D3; padding: 8px;")
        center_layout.addWidget(input_label)
        
        self.prompt_edit = SubmitTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your question... (Press Enter to submit)")
        self.prompt_edit.setMaximumHeight(80)
        self.prompt_edit.submit_requested.connect(self.ask_kouncil)
        center_layout.addWidget(self.prompt_edit)
        
        self.attach_label = QtWidgets.QLabel("")
        self.attach_label.setStyleSheet("color: #FFE66D; padding: 4px; font-size: 9pt;")
        center_layout.addWidget(self.attach_label)
        
        btn_layout = QtWidgets.QHBoxLayout()
        attach_btn = QtWidgets.QPushButton("📎 Attach")
        attach_btn.clicked.connect(self.attach_file)
        btn_layout.addWidget(attach_btn)
        
        btn_layout.addStretch()
        
        ask_btn = QtWidgets.QPushButton("🐙 ASK KOUNCIL")
        ask_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B6B, stop:1 #FF8B94);
                color: white; font-size: 12pt; font-weight: bold;
                padding: 12px 40px; border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF7B7B, stop:1 #FF9BA4);
            }
        """)
        ask_btn.clicked.connect(self.ask_kouncil)
        btn_layout.addWidget(ask_btn)
        
        center_layout.addLayout(btn_layout)
        main_layout.addWidget(center_panel, stretch=1)
    
    def show_manual(self):
        """Show the comprehensive how-to manual"""
        dialog = HowToManualDialog(self)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>🦑 Kraken Kouncil v4.2</h2>
        <h3>Web Search + Icons + Agentic Debate Edition</h3>
        <p><b>An AI orchestration system by The Kraken</b></p>
        <br>
        
        <h3>🎊 Latest: Version 4.2.1</h3>
        <p><b>🛠️ Bug Fixes & Quality Improvements:</b></p>
        <ul>
            <li><b>Fixed:</b> Voting now works with contractions (model's, it's, etc.)</li>
            <li><b>Fixed:</b> Models now understand current date when using web search</li>
            <li><b>Enhanced:</b> Models cite sources [1], [2], [3] in their answers</li>
            <li><b>Enhanced:</b> Tougher critiques during debates → better quality</li>
            <li><b>Fixed:</b> Cross-platform icon loading (.png and .PNG)</li>
            <li><b>Improved:</b> Icon visibility (85% scaling, better presence)</li>
        </ul>
        
        <h3>🌐 Web Search Integration (v4.2)</h3>
        <ul>
            <li>Google Programmable Search Engine (PSE) support</li>
            <li>Real-time information for your council</li>
            <li>Configurable in Settings with help dialog</li>
            <li>100 free queries per day</li>
            <li>Smart status indicators: "🔍 Searching web..."</li>
        </ul>
        
        <p><b>🎨 Model Icons & Visual Identity (v4.2):</b></p>
        <ul>
            <li>PNG icon support for custom model logos</li>
            <li>Beautiful emoji fallbacks (🦙💚🌙🔮🌪️🔵)</li>
            <li>Auto-detection for 10+ model families</li>
            <li>Circular clipping with proper transparency</li>
            <li>Border framing for professional look</li>
        </ul>
        
        <h3>🗣️ Agentic Debate System (v4.0)</h3>
        <ul>
            <li>Multi-round critique and refinement</li>
            <li>1-5 configurable debate rounds</li>
            <li>Round progress tracking: "💭 Critiquing (2/3)"</li>
            <li>Models improve answers based on peer critiques</li>
            <li>Final voting on refined responses</li>
        </ul>
        
        <h3>🎭 Arena & UX Features</h3>
        <ul>
            <li>Hybrid design: Compact sidebar + detailed arena</li>
            <li>Pulsing animated avatars</li>
            <li>Backend badges (🎬 LM Studio / 🦙 Ollama)</li>
            <li>One-click persona dropdowns</li>
            <li>Real-time status updates</li>
            <li>Live response streaming</li>
            <li>Score accumulation with flash effects</li>
        </ul>
        
        <h3>📊 Voting & Stats</h3>
        <ul>
            <li>5-criteria scoring system (Relevance, Clarity, Completeness, Accuracy, Helpfulness)</li>
            <li>Anti-lazy rule: Short responses penalized</li>
            <li>Win tracking & leaderboard</li>
            <li>Stats panel with phase tracking</li>
            <li>Consensus/Decision/Tie indicators</li>
        </ul>
        
        <h3>⚙️ Configuration & Help</h3>
        <ul>
            <li>Comprehensive manual (❓ button)</li>
            <li>Settings with inline help dialogs</li>
            <li>LM Studio & Ollama support</li>
            <li>Adjustable concurrency</li>
            <li>Persistent persona assignments</li>
            <li>File attachment support</li>
        </ul>
        
        <br>
        <p><b>Version History:</b></p>
        <p>v4.2.1 - Bug Fixes & Quality | v4.2 - Web Search + Icons | v4.0 - Agentic Debate | v3.6 - Hybrid Arena</p>
        <br>
        <p><i>Orchestrate brilliance, one council at a time.</i></p>
        """
        QtWidgets.QMessageBox.about(self, "About Kraken Kouncil", about_text)
    
    def show_server_config(self):
        dialog = ServerConfigDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.auto_discover()
    
    def attach_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Attach File", "", "All Files (*)")
        if path:
            p = Path(path)
            self.attached_content = process_attachment(p)
            self.attached_name = p.name
            disp = p.name if len(p.name)<40 else p.name[:37]+"..."
            self.attach_label.setText(f"📎 {disp}")
    
    def update_status(self, text: str):
        self.stats_panel.update_stat("status", text, "#4ECDC4")
        
    def handle_card_status(self, mid: str, text: str, state: str):
        """Slot to safely update model cards from background thread"""
        if mid in self.model_cards:
            self.model_cards[mid].update_status(text, state)
    
    def show_error(self, text: str):
        QtWidgets.QMessageBox.critical(self, "Error", text)
    
    # --- Discovery Logic ---
    def auto_discover(self):
        if self.discovery_worker and self.discovery_worker.isRunning():
            return
        
        # Clear existing
        for w in self.model_list_items.values(): w.deleteLater()
        self.model_list_items.clear()
        for w in self.model_cards.values(): w.deleteLater()
        self.model_cards.clear()
        
        self.models.clear()
        self.model_backends.clear()
        self.selected_models.clear()
        
        self.discovery_worker = DiscoveryWorker(
            settings.get("lm_studio_url", "http://localhost:1234"),
            settings.get("ollama_url", "http://localhost:11434"),
            settings.get("lm_studio_enabled", True),
            settings.get("ollama_enabled", True)
        )
        
        self.discovery_worker.progress.connect(self.update_status)
        self.discovery_worker.finished.connect(self.discovery_finished)
        self.discovery_worker.start()
    
    def discovery_finished(self, models: list, backends: dict):
        self.models = models
        self.model_backends = backends
        
        if models:
            self.populate_model_list()
            self.update_status(f"✅ Ready ({len(models)} models)")
        else:
            self.update_status("❌ No models found")
    
    def populate_model_list(self):
        for i, m in enumerate(self.models):
            mid = m["id"]
            color = MODEL_COLORS[i % len(MODEL_COLORS)]
            self.model_colors[mid] = color
            
            item = ModelListItem(mid, color)
            item.selection_changed.connect(self.on_model_selection_changed)
            
            self.model_list_items[mid] = item
            self.model_list_layout.insertWidget(self.model_list_layout.count()-1, item)
    
    def on_model_selection_changed(self, model_id: str, selected: bool):
        if selected:
            self.selected_models.add(model_id)
            self.add_to_arena(model_id)
        else:
            self.selected_models.discard(model_id)
            self.remove_from_arena(model_id)
        
        count = len(self.selected_models)
        self.stats_panel.update_stat("models", f"{count} Selected", "#4ECDC4")
    
    def add_to_arena(self, model_id: str):
        if model_id in self.model_cards: return
        
        color = self.model_colors[model_id]
        backend = self.model_backends[model_id]["type"]
        
        card = ArenaModelCard(model_id, backend, color, leaderboard.get(model_id, 0))
        card.persona_changed.connect(self.save_persona)
        
        # Restore persona - now works with combo box
        saved_persona = self.personas.get(model_id, "None")
        for p in DEFAULT_PERSONAS:
            if p["name"] == saved_persona:
                card.set_persona(p["name"], p["emoji"])
                break
        
        self.model_cards[model_id] = card
        self.reorganize_arena()
        
    def remove_from_arena(self, model_id: str):
        if model_id in self.model_cards:
            card = self.model_cards[model_id]
            card.deleteLater()
            del self.model_cards[model_id]
            self.reorganize_arena()

    def reorganize_arena(self):
        n = len(self.model_cards)
        # Adjust columns based on number of models - larger cards need fewer columns
        if n <= 3:
            cols = 2
        elif n <= 6:
            cols = 3
        else:
            cols = 4
        
        # Clear layout
        for i in reversed(range(self.arena_layout.count())): 
            self.arena_layout.itemAt(i).widget().setParent(None)
            
        for i, (mid, card) in enumerate(self.model_cards.items()):
            row = i // cols
            col = i % cols
            self.arena_layout.addWidget(card, row, col)
    
    def save_persona(self, mid: str, name: str):
        if name and name != "None":
            self.personas[mid] = name
        else:
            self.personas.pop(mid, None)
        save_settings({"persona_assignments": self.personas})
    
    def get_selected(self) -> List[str]:
        return list(self.selected_models)
    
    # --- Execution Logic ---
    def ask_kouncil(self):
        question = self.prompt_edit.toPlainText().strip()
        full = question
        if self.attached_content:
            full = f"{question}\n\n[Attached: {self.attached_name}]\n{self.attached_content}" if question else self.attached_content
        
        selected = self.get_selected()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "No Models Selected", "Please check at least one model!")
            return
        
        # Reset UI
        for card in self.model_cards.values():
            card.clear_response()
            card.reset_score()
        
        self.winner_scroll.setVisible(False)
        self.stats_panel.update_stat("phase", "Generating...", "#FFE66D")
        self.stats_panel.update_stat("controversy", "Pending", "#888")
        
        self.prompt_edit.clear()
        self.attach_label.clear()
        self.attached_content = self.attached_name = ""
        
        for mid in selected:
            self.model_cards[mid].update_status(f"Thinking...", "working")
        
        threading.Thread(target=self.run_kouncil, args=(full, selected), daemon=True).start()
    
    def run_kouncil(self, prompt: str, selected: List[str]):
        try:
            debate_enabled = settings.get("debate_enabled", False)
            debate_rounds = settings.get("debate_rounds", 2)
            
            answers, winner, details, tally = asyncio.run(council_round(
                selected, prompt, self.personas,
                lambda mid, txt, state="working": self.card_status_signal.emit(mid, txt, state),
                lambda mid, chunk: self.stream_signal.emit(mid, chunk),
                lambda voter, cand, score: self.vote_signal.emit(voter, cand, score),
                settings.get("max_concurrency", 3),
                self.model_backends,
                debate_enabled,
                debate_rounds
            ))
            record_vote(prompt, winner, details)
            self.result_signal.emit((prompt, answers, winner, details, tally))
        except Exception as e:
            print(f"FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.error_signal.emit(f"Council error: {e}")
    
    def handle_stream_chunk(self, model_id: str, chunk: str):
        if model_id in self.model_cards:
            self.model_cards[model_id].append_response(chunk)
    
    def handle_vote(self, voter: str, candidate: str, score: int):
        if candidate in self.model_cards:
            self.model_cards[candidate].add_score(score)
    
    def handle_result(self, payload):
        _, answers, winner, details, tally = payload
        self.stats_panel.update_stat("phase", "Complete", "#4ECDC4")
        
        # Controversy Logic
        scores = list(tally.values())
        if scores:
            sorted_scores = sorted(scores, reverse=True)
            total_points = sum(scores)
            
            if len(sorted_scores) > 1 and sorted_scores[0] == sorted_scores[1]:
                controversy = "⚡ TIE"
                color = "#FF8B94"
            else:
                margin = sorted_scores[0] - (sorted_scores[1] if len(sorted_scores) > 1 else 0)
                if margin > (total_points * 0.15):
                    controversy = "🎯 CONSENSUS"
                    color = "#4ECDC4"
                else:
                    controversy = "✅ DECISION"
                    color = "#FFE66D"
                    
            self.stats_panel.update_stat("controversy", controversy, color)
        
        win_color = self.model_colors.get(winner, "#FFE66D")
        win_answer = answers.get(winner, "No response")
        
        self.winner_label.setPlainText(f"🏆 KOUNCIL DECISION 🏆\nWinner: {short_id(winner, 30)}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n{win_answer}")
        self.winner_label.setStyleSheet(f"""
            QTextEdit {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:1 #2a5298);
                color: gold; font-size: 11pt; font-weight: bold;
                border: 3px solid {win_color}; border-radius: 12px; padding: 16px;
            }}
        """)
        self.winner_scroll.setVisible(True)
        
        # Refresh leaderboard
        self.leaderboard.refresh()
        
        for card in self.model_cards.values():
            card.update_status("Ready", "idle")

# ====================== Async Core Logic ======================

async def call_model_stream(session, mid, messages, backend, stream_callback):
    url = backend["url"]
    is_ollama = backend["type"] == "ollama"
    
    try:
        if is_ollama:
            payload = {
                "model": mid, "messages": messages, "stream": True,
                "options": {"temperature": 0.7, "num_predict": 1600}
            }
            ep = f"{url.rstrip('/')}/api/chat"
            
            full_response = ""
            chunk_buffer = ""
            async with session.post(ep, json=payload, timeout=aiohttp.ClientTimeout(total=600)) as r:
                if r.status != 200: return f"[ERROR {r.status}]"
                async for line in r.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                full_response += chunk
                                chunk_buffer += chunk
                                if len(chunk_buffer.split()) >= 30:
                                    stream_callback(mid, chunk_buffer)
                                    chunk_buffer = ""
                        except: pass
                if chunk_buffer: stream_callback(mid, chunk_buffer)
                return full_response
        else:
            # LM Studio
            payload = {
                "model": mid, "messages": messages,
                "temperature": 0.7, "max_tokens": 1600
            }
            ep = f"{url.rstrip('/')}/v1/chat/completions"
            async with session.post(ep, json=payload, timeout=aiohttp.ClientTimeout(total=600)) as r:
                if r.status != 200: return f"[ERROR {r.status}]"
                data = await r.json()
                resp = data["choices"][0]["message"]["content"]
                # Fake stream
                words = resp.split()
                for i in range(0, len(words), 30):
                    chunk = " ".join(words[i:i+30]) + " "
                    stream_callback(mid, chunk)
                    await asyncio.sleep(0.5)
                return resp
    except Exception as e:
        return f"[ERROR] {e}"

async def call_model_vote(session, mid, prompt, backend):
    url = backend["url"]
    is_ollama = backend["type"] == "ollama"
    
    if is_ollama:
        payload = {
            "model": mid, "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 3000, "num_ctx": 8192}
        }
        ep = f"{url.rstrip('/')}/api/chat"
    else:
        payload = {
            "model": mid, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 3000
        }
        ep = f"{url.rstrip('/')}/v1/chat/completions"
    
    async with session.post(ep, json=payload, timeout=aiohttp.ClientTimeout(total=400)) as r:
        if r.status != 200: raise Exception(f"HTTP {r.status}")
        data = await r.json()
        if is_ollama:
            return data.get("message", {}).get("content", "")
        else:
            return data["choices"][0]["message"]["content"]

async def debate_round(session, selected, question, initial_responses, roles, status_cb, backends, round_num, total_rounds, sem):
    """One round of debate: critique then refine"""
    critiques = {}
    refined_answers = {}
    
    # Helper for semaphore
    async def run_vote(mid, prompt, backend):
        async with sem:
            return await call_model_vote(session, mid, prompt, backend)
    
    # Phase 1: Critique (ALL models become "Ruthless Editor" for this phase)
    tasks = []
    for mid in selected:
        status_cb(mid, f"💭 Critiquing ({round_num}/{total_rounds})", "working")
        
        context = f"Original Question: {question}\n\n"
        context += "All Responses:\n" + "\n\n".join(
            f"[{short_id(m, 15)}]: {ans[:800]}..." 
            for m, ans in initial_responses.items() if "ERROR" not in ans
        )
        
        # Force RUTHLESS EDITOR role for all models during critique
        # This ensures tough, meaningful critiques regardless of original persona
        critique_prompt = f"""You are a ruthless logic checker and fact verifier. Your job is to find flaws, 
fallacies, missing information, and weak reasoning in the responses below.

Point out:
- Logical fallacies or weak reasoning
- Missing crucial information  
- Factual errors or unsupported claims
- Areas that need more depth
- Assumptions that should be questioned

{context}

Provide your critique in this format:
- Response [model]: [specific, tough critique]

Be brutally honest and constructive."""
        
        backend = backends[mid]
        tasks.append((mid, run_vote(mid, critique_prompt, backend)))
    
    results = await asyncio.gather(*(t[1] for t in tasks), return_exceptions=True)
    
    for (mid, _), res in zip(tasks, results):
        if isinstance(res, Exception):
            critiques[mid] = f"[ERROR] {res}"
            status_cb(mid, "❌ Critique failed", "error")
        else:
            critiques[mid] = res
            status_cb(mid, "✅ Critique done", "done")
    
    # Phase 2: Refine
    tasks = []
    for mid in selected:
        status_cb(mid, f"🔧 Refining ({round_num}/{total_rounds})", "working")
        
        refine_prompt = f"""Original Question: {question}

Your Previous Answer:
{initial_responses.get(mid, "N/A")}

Critiques from other council members:
{chr(10).join(f"- {short_id(m, 15)}: {c[:500]}" for m, c in critiques.items())}

Based on these critiques, refine and improve your answer. Address weaknesses, incorporate good suggestions, but maintain your perspective."""
        
        backend = backends[mid]
        prompt_obj = next((p["prompt"] for p in DEFAULT_PERSONAS if p["name"] == roles.get(mid, "None")), None)
        # system = prompt_obj or "You are a helpful assistant." # Unused variable
        
        tasks.append((mid, run_vote(mid, refine_prompt, backend)))
        
    results = await asyncio.gather(*(t[1] for t in tasks), return_exceptions=True)
    
    for (mid, _), res in zip(tasks, results):
        if isinstance(res, Exception):
            refined_answers[mid] = initial_responses.get(mid, f"[ERROR] {res}")
            status_cb(mid, "❌ Refinement failed", "error")
        else:
            refined_answers[mid] = res
            status_cb(mid, "✅ Refinement done", "done")
    
    return refined_answers

async def council_round(selected, question, roles, status_cb, stream_cb, vote_cb, concurrency, backends, debate_enabled, debate_rounds):
    answers = {}
    async with aiohttp.ClientSession() as sess:
        # --- WEB SEARCH (if enabled) ---
        enhanced_question = question
        if settings.get("web_search_enabled", False):
            api_key = settings.get("google_api_key", "")
            engine_id = settings.get("google_search_engine_id", "")
            max_results = settings.get("max_search_results", 5)
            
            if api_key and engine_id:
                # Show search status
                for mid in selected:
                    status_cb(mid, "🔍 Searching web...", "working")
                
                try:
                    search_results = await google_pse_search(question, api_key, engine_id, max_results)
                    if search_results:
                        search_context = format_search_results(search_results, question)
                        enhanced_question = search_context + "\n" + question
                        print(f"✓ Web search found {len(search_results)} results")
                    else:
                        print("⚠ Web search returned no results")
                except Exception as e:
                    print(f"⚠ Web search failed: {e}")
        
        # --- INITIAL GENERATION ---
        sem = asyncio.Semaphore(concurrency)
        
        async def run_stream(mid, msgs, backend):
            async with sem:
                return await call_model_stream(sess, mid, msgs, backend, stream_cb)
        
        tasks = []
        for mid in selected:
            backend = backends[mid]
            prompt = next((p["prompt"] for p in DEFAULT_PERSONAS if p["name"] == roles.get(mid, "None")), None)
            system = prompt or "You are a helpful assistant."
            msgs = [{"role": "system", "content": system}, {"role": "user", "content": enhanced_question}]
            status_cb(mid, "🔄 Generating...", "working")
            tasks.append((mid, run_stream(mid, msgs, backend)))
        
        results = await asyncio.gather(*(t[1] for t in tasks), return_exceptions=True)
        
        for (mid, _), res in zip(tasks, results):
            if isinstance(res, Exception):
                answers[mid] = f"[ERROR] {res}"
                status_cb(mid, "❌ Failed", "error")
            elif "[ERROR]" in str(res):
                answers[mid] = str(res)
                status_cb(mid, "❌ Error", "error")
            else:
                answers[mid] = str(res)
                status_cb(mid, "✅ Complete", "done")
        
        # --- DEBATE PHASE ---
        if debate_enabled and debate_rounds > 0:
            current_answers = answers.copy()
            
            for round_num in range(1, debate_rounds + 1):
                # Show overall progress
                for mid in selected:
                    status_cb(mid, f"🗣️ Debate Round {round_num}/{debate_rounds}", "working")
                await asyncio.sleep(0.5)  # Brief pause so users see the round announcement
                
                current_answers = await debate_round(
                    sess, selected, enhanced_question, current_answers, roles, status_cb, backends,
                    round_num, debate_rounds, sem
                )
            
            answers = current_answers
        
        # --- VOTING ---
        valid = {}
        tally = {m: 0 for m in selected}
        
        for voter in selected:
            status_cb(voter, "🗳️ Voting...", "working")
            context = "\n\n".join(f"{short_id(m, 15)}: {a[:500]}..." for m, a in answers.items() if "ERROR" not in a)
            
            vote_prompt = f"""You are a strict judge. Score responses 1-10.
CRITICAL RULES:
1. IF A RESPONSE IS LESS THAN 20 WORDS, GIVE IT A SCORE OF 1 FOR COMPLETENESS.
2. PENALIZE LAZY ANSWERS.
3. REWARD DEPTH AND ACCURACY.

Question: {question}

Responses:
{context}

Return ONLY a JSON object with this exact format:
{{"scores": {{"{short_id(selected[0], 15)}": {{"Relevance": 8, "Clarity": 9, "Completeness": 7, "Accuracy": 8, "Helpfulness": 9}}}}}}"""
            
            for attempt in range(3):
                try:
                    raw = await call_model_vote(sess, voter, vote_prompt, backends[voter])
                    
                    if "<think>" in raw:
                        raw = raw.split("</think>")[-1]
                    
                    cleaned = repair_json(raw)
                    ballot = json.loads(cleaned)
                    valid[voter] = ballot
                    
                    for cand, scores in ballot.get("scores", {}).items():
                        target = next((x for x in selected if short_id(x, 15) in cand or cand in short_id(x, 15)), None)
                        if target:
                            s = sum(scores.values())
                            vote_cb(voter, target, int(s))
                            tally[target] += s
                    
                    status_cb(voter, "✅ Voted", "done")
                    break
                except Exception as e:
                    print(f"[Retry {attempt+1}] Vote failed for {voter}: {e}")
                    if attempt == 2:
                        status_cb(voter, "⚠️ Vote failed", "error")
                    else:
                        await asyncio.sleep(1)
        
        if not tally:
            winner = selected[0]
        else:
            winner = max(tally, key=tally.get)
            
        return answers, winner, {"valid_votes": valid}, tally

# ====================== Main Entry Point ======================

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Kraken Kouncil")
    
    if THEME_AVAILABLE:
        theme = settings.get("theme", "dark")
        apply_theme(theme, app)
    
    win = KrakenKouncilWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
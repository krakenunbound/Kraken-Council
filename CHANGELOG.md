# Kraken Kouncil - Changelog

All notable changes to the Kraken Kouncil project are documented in this file.

---

## [4.3.0] - 2026-07-13

This is expected to be the final release from the original creator. Kraken Kouncil is now presented as a proof of concept and a starting point for community forks and experimentation, without an expectation of ongoing maintenance or support.

The project is now distributed under the MIT License to make that reuse explicit.

### Correctness and safety

- Added complete, atomic ballot validation with deterministic candidate aliases.
- Added explicit tie and no-valid-ballot outcomes; arbitrary fallback winners were removed.
- Prevented concurrent/overlapping council runs and configuration mutation during execution.
- Added responsive cancellation for active HTTP/generation tasks and safe close-after-cancel behavior.
- Restored personas during debate refinement.
- Stopped saving attached file contents in SQLite history.
- Added bounded ZIP extraction and removable attachments.
- Added a 100,000-character attachment prompt limit with visible truncation notices.
- Migrated settings and history to a writable per-user application-data directory.
- Made settings writes atomic and report failures instead of showing false success.

### Providers and interface

- Added real Server-Sent Event streaming for LM Studio.
- Added JSON response mode for final voting on Ollama and LM Studio.
- Preserved duplicate model IDs across different backends.
- Added automatic startup discovery, server URL validation, keyboard shortcuts, and remembered window geometry.
- Added single-instance locking and clearer discovery/run button states.
- Enabled SQLite busy timeouts and WAL journaling for safer local history access.
- Replaced the incompatible `pyqtdarktheme` integration with a built-in Qt palette.
- Marked Google Custom Search as legacy because it is closed to new customers and scheduled for discontinuation.

### Quality

- Added offline unit tests for ballot validation, ties, and failed-vote behavior.
- Added bounded dependencies, optional GPU requirements, and `.gitignore` rules.
- Preserved `kraken_council_v4_2_1.py` as the previous release.

---

## [4.2.1] - 2024-11-18

### 🛠️ Bug Fixes (Critical)
**Fixed:**
- **Concurrency Control:** Fixed a critical issue where `max_concurrency` settings were ignored
  - Implemented `asyncio.Semaphore` to strictly enforce model limits
  - Prevents system overload when selecting many models
  - Now applies to both initial generation AND debate phases
  
- **Web Search Context:** Fixed data loss during debate phase
  - Web search results are now properly passed to the debate round
  - Models retain access to external information during critique and refinement
  - Prevents hallucinations where models would "forget" the search data

- **Debate Performance:** Parallelized the debate phase
  - Critiques and refinements now run concurrently (up to the limit)
  - Significantly faster debate rounds compared to previous sequential execution

- **Apostrophe Catastrophe:** Voting now works correctly with contractions (model's, it's, don't, etc.)
  - Changed `repair_json()` to only fix single quotes around keys, not in content
  - Regex pattern: `r"['](\w+)[']\s*:"` instead of replacing all apostrophes
  - Prevents JSON parse failures during debate/voting phases
  
- **Date Blindness:** Models now understand temporal context with web search
  - Added current date to search results: `[Current Date: Monday, November 18, 2024]`
  - Models can now properly interpret "today," "this week," "recently," etc.
  - Improves accuracy of time-sensitive queries

### ✨ Enhancements
**Added:**
- **Source Attribution:** Models now cite web search sources
  - Search results numbered as [1], [2], [3]
  - Instruction added: "cite the source number like [1] in your response"
  - Enables verification and builds trust in answers
  
- **Ruthless Editor Role:** Significantly improved debate quality
  - ALL models become "Ruthless Editor" during critique phase
  - Forces tough, specific critiques regardless of persona
  - Models return to original persona during refinement
  - Results in meaningfully better final answers

**Improved:**
- **Cross-Platform Icon Loading:** Icons work on all platforms
  - Now tries both `.png` and `.PNG` extensions
  - Fixes case-sensitivity issues on Linux
  - No changes needed to existing icon files

- **Icon Visibility:** Better presence in avatar circles
  - Increased scaling from 70% to 85%
  - Icons more clearly visible without being oversized
  - Placeholder icons already have padding, so larger scale works well

### 📊 Impact
- Critical fixes: Voting reliability, temporal awareness
- Quality improvements: Source citations, debate depth
- Polish: Cross-platform compatibility, visual improvements

### 🔧 Technical Details
**Files Modified:**
- `repair_json()` - Lines ~269-271
- `format_search_results()` - Lines ~186-196
- `debate_round()` - Lines ~1998-2009  
- `ModelAvatar.load_model_icon()` - Lines ~791-809

**Lines Changed:** ~130 lines across 5 functions

---

## [4.2.0] - 2024-11-18

### 🌐 Web Search Integration
**Added:**
- Google Programmable Search Engine (PSE) integration
- Real-time web information before model generation
- Settings UI for web search configuration:
  - API Key field (password-protected)
  - Search Engine ID field
  - Max Results spinner (1-10)
  - Enable/disable checkbox
- Built-in setup help dialog with step-by-step instructions
- Search status indicator: "🔍 Searching web..." on model cards
- Automatic search result formatting with title, URL, snippet
- Graceful error handling and fallback to normal operation

**Technical Details:**
- `google_pse_search()` async function for API calls
- `format_search_results()` for context formatting
- Search results prepended to user question before generation
- Supports 100 free queries per day (Google free tier)
- 10-second timeout with error recovery

**Configuration:**
- Navigate to Settings → Web Search Settings
- Click "How to get API credentials?" for detailed setup guide
- Enter API key and Search Engine ID
- Set max results (default: 5)
- Enable web search

### 🎨 Model Icons & Visual Identity
**Added:**
- PNG icon support from `/icons` folder
- Automatic model family detection (case-insensitive)
- Beautiful emoji fallbacks for recognized families:
  - 🦙 Llama (llama, llama2, llama3, llama4)
  - 💎 CodeLlama (codellama)
  - 💚 Gemma (gemma, gemma2, gemma3)
  - 🌙 Qwen (qwen, qwen2, qwen2.5, qwen3)
  - 🔮 DeepSeek (deepseek, deepseek-v2, deepseek-v3)
  - 🌪️ Mistral (mistral, mixtral)
  - 🔵 Phi (phi, phi-2, phi-3, phi-4)
  - 🦅 Falcon (falcon)
  - 🐉 Yi (yi)
- Three-tier fallback system: PNG → Emoji → Initials
- 10 placeholder PNG icons included (128x128px)

**Fixed:**
- Circular clipping path for icons (no more square corners!)
- Transparency support for PNG icons
- Border layering - frame now draws ON TOP of icon
- Proper visual hierarchy in avatar rendering

**Technical Details:**
- `load_model_icon()` method with family detection
- Circular `QPainterPath` clipping
- Scaled icons to 70% of avatar size
- Border drawn last for proper framing

### 📚 Documentation Updates
**Updated:**
- User manual with new sections:
  - Model Icons & Visual Identity
  - Recognized Model Families
  - Custom Icons setup guide
  - Web Search Integration
  - Web Search setup instructions
  - When to use web search
  - Pricing & Free Tier information
- About dialog with comprehensive feature list
- Version history in About page
- Created CHANGELOG.md (this file)

### 🔧 Internal Improvements
- Updated settings structure to include web search config
- Enhanced error logging for search failures
- Improved status callback system for search phase
- Better icon path resolution using APP_DIR

---

## [4.1.0] - 2024-11-18 (Internal)

### 🎨 Visual Enhancements
**Added:**
- Initial model icon system (later improved in 4.2.0)
- Support for loading PNG icons from `/icons` folder
- Fallback to initials for unknown models

**Note:** v4.1 was an intermediate version, quickly superseded by 4.2.0 with emoji fallbacks and transparency fixes.

---

## [4.0.0] - 2024-11 (Agentic Debate Edition)

### 🗣️ Agentic Debate System
**Added:**
- Multi-round debate before final voting
- Critique phase: Models analyze all responses
- Refinement phase: Models improve their answers
- Configurable debate rounds (1-5, default: 2)
- Round progress tracking with visual indicators
- Status updates: "🗣️ Debate Round X/Y", "💭 Critiquing (X/Y)", "🔧 Refining (X/Y)"
- Brief pause between rounds for user visibility

**Settings:**
- Debate enable/disable checkbox
- Debate rounds spinner
- Settings persist across sessions

### 📖 Comprehensive Manual System
**Added:**
- Built-in user manual accessible via ❓ button
- Help menu with "How to Use" option
- Scrollable HTML-based manual with:
  - Quick Start guide
  - Debate system documentation
  - Arena features explanation
  - Voting system details
  - Stats panel info
  - Settings guide
  - Pro tips and troubleshooting
- Styled sections with tips, warnings, and feature boxes

### 🎭 Arena Design Enhancements
**Improved:**
- Enhanced arena cards with more information
- Backend badges (🎬 LM Studio / 🦙 Ollama)
- Longer model names (25 chars instead of 16)
- Bigger response areas (100-150px height)
- Better status color coding
- Improved gradient backgrounds

### 📊 Progress Tracking
**Added:**
- Real-time round announcements
- Phase-specific status updates
- Progress counters: "(2/3)" format
- Clear workflow visibility
- Time estimation support

---

## [3.6.0] - 2024-11 (Hybrid Arena)

### 🏛️ Hybrid Design
**Added:**
- Compact checkbox list in LEFT sidebar (all models)
- Detailed arena cards in CENTER (selected models only)
- Dynamic grid layout (2-4 columns based on count)
- Model selection/deselection with instant arena updates

**Benefits:**
- Space efficiency: Only show details for selected models
- Quick scanning: All available models visible at once
- Clear workflow: Select → Configure → Execute

### 🎨 Visual Polish
**Added:**
- Pulsing animated avatars
- Color-coded model indicators
- Gradient arena card backgrounds
- Score badges with flash effects
- Status label color coding

### ⚙️ One-Click Personas
**Changed:**
- Persona dropdown now always visible on arena cards
- Changed from emoji menu (2 clicks) to dropdown (1 click)
- 9 predefined personas:
  - 🟢 None
  - 🔍 Meticulous Fact-Checker
  - ⚙️ Pragmatic Engineer
  - ⚠️ Cautious Risk Assessor
  - 👨‍🏫 Clear Teacher
  - 📊 Data Analyst
  - 🧠 Systems Thinker
  - 🎨 Creative Muse
  - 😈 Devil's Advocate

---

## [3.0.0 - 3.5.0] - 2024-11 (Evolution)

### Core Features Established
- Multi-model orchestration
- Concurrent generation with asyncio
- Thread-safe Qt signal system
- Response streaming
- Voting system (5 criteria, 1-10 scale)
- Leaderboard tracking
- Stats panel
- Settings dialog
- LM Studio and Ollama support
- File attachment support
- JSON repair for small models
- SQLite database for vote storage

### Anti-Lazy Rules
**Added:**
- Responses under 20 words penalized
- Completeness score set to 1 for short answers
- Encourages detailed, thoughtful responses

### Voting Criteria
**Established:**
- Relevance (answers the question?)
- Clarity (well-written?)
- Completeness (thorough?)
- Accuracy (correct facts?)
- Helpfulness (actionable insights?)
- Max 50 points per judge

---

## [2.0.0] - 2024 (Multi-Model)

### 🎯 Core Concept
**Added:**
- Multiple model selection
- Concurrent query execution
- Model comparison
- Basic voting system

---

## [1.0.0] - 2024 (Initial)

### 🎉 Birth of Kraken Kouncil
**Created:**
- Single model query interface
- Basic Qt/PySide6 GUI
- Ollama integration
- Simple output display

---

## Features Roadmap

### Future Considerations
- [ ] Additional search engines (Bing, DuckDuckGo)
- [ ] Search result caching
- [ ] More model family icons
- [ ] User-uploadable custom icons
- [ ] Export conversation history
- [ ] Prompt templates
- [ ] Model performance analytics
- [ ] API rate limiting UI
- [ ] Advanced debate strategies
- [ ] Custom voting criteria

---

## Installation & Setup

### Requirements
- Python 3.12+
- PySide6
- aiohttp
- requests
- Optional: pyqtdarktheme

### Quick Start
```bash
# Install dependencies
pip install PySide6 aiohttp requests

# Optional theme support
pip install pyqtdarktheme

# Run application
python3 kraken_council_v4.py
```

### File Structure
```
project/
├── kraken_council_v4.py    # Main application
├── icons/                   # Model family icons (optional)
│   ├── llama.png
│   ├── gemma.png
│   └── ...
├── kouncil_stats.db         # Created on first run
└── kouncil_settings.json    # Created on first run
```

---

## Contributing

This is a personal project by The Kraken, but if you have suggestions or find bugs, feel free to:
- Test thoroughly and report issues
- Suggest new model family icons
- Share persona ideas
- Propose new features

---

## License

Created by The Kraken for personal use and enjoyment.

---

## Acknowledgments

**Model Families Supported:**
- Meta (Llama)
- Google (Gemma)
- Alibaba (Qwen)
- DeepSeek
- Mistral AI
- Microsoft (Phi)
- TII (Falcon)
- 01.AI (Yi)

**Technologies:**
- PySide6/Qt for GUI
- aiohttp for async operations
- Google Programmable Search Engine
- LM Studio & Ollama for local inference

---

**Current Version:** 4.2.1  
**Last Updated:** November 19, 2024  
**Status:** Production Ready 🎊

*Orchestrate brilliance, one council at a time.* 🦑⚔️🌐

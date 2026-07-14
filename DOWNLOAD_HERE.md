# 🎊 Kraken Kouncil v4.3.0

## 📥 Download Your Files

### Main Application
Run `kraken_council_v4_3_0.py` from this project folder.

### Icon Files (Place in `/icons` folder next to script)
The included `icons/` folder contains the model-family artwork used by the app.

### Documentation

- `README.md` – installation, features, and offline verification
- `CHANGELOG.md` – release history
- `GPU_SETUP_QUICK.md` – optional NVIDIA telemetry setup

---

## 🚀 Quick Start

### 1. File Structure
```
your-folder/
├── kraken_council_v4_3_0.py
└── icons/
    ├── llama.png
    ├── gemma.png
    ├── qwen.png
    └── ... (7 more)
```

### 2. Run It!
```bash
python kraken_council_v4_3_0.py
```

### 3. Features to Try

**🎨 Model Icons:**
- Discover models
- Select llama/gemma/qwen models
- See icons (PNG) or emojis (fallback)!

**🌐 Web Search:**
- Click ⚙️ Settings
- Scroll to "🌐 Web Search Settings"
- Click "How to get API credentials?"
- Follow setup guide
- Enable and test with: "What's today's news?"

---

## ✨ What You Got

### Phase 1: Model Icons + Emoji Fallbacks
- 🦙 Real icons for llama, gemma, qwen, deepseek, mistral, phi, etc.
- 💚 Beautiful emoji fallbacks if no PNG
- 🔤 Boring initials only for truly unknown models

**Fallback Hierarchy:**
1. PNG Icon (if exists) → Best!
2. Emoji (if family recognized) → Great!
3. Initials (unknown models) → Last resort

### Phase 2: Google PSE Web Search
- 🌐 Real-time web information
- 📰 Current events, prices, news
- ⚙️ Easy configuration in Settings
- 🔍 "Searching web..." status indicator
- 💰 100 free queries/day

---

## 🎯 Key Features

**Arena Design:**
- ✅ Hybrid sidebar + arena cards
- ✅ Pulsing avatars with icons/emojis
- ✅ Backend badges (🎬 LM Studio / 🦙 Ollama)
- ✅ One-click persona dropdowns
- ✅ Round progress tracking

**Debate System:**
- ✅ Multi-round critique & refinement
- ✅ "💭 Critiquing (2/3)" progress
- ✅ "🔧 Refining (3/3)" status
- ✅ Clear round announcements

**Web Search:**
- ✅ Google PSE integration
- ✅ Pre-search before generation
- ✅ Formatted results in context
- ✅ Graceful error handling

**User Experience:**
- ✅ Comprehensive manual (❓ button)
- ✅ Settings with help dialogs
- ✅ Stats panel & leaderboard
- ✅ File attachments support

---

## 📚 Quick Reference

### To Enable Web Search:
1. Settings → Web Search Settings
2. Get API key from Google Cloud Console
3. Get Engine ID from Programmable Search
4. Enable "Custom Search API"
5. Paste credentials, enable, save!

### To Add More Icons:
1. Download PNG (128x128 recommended)
2. Name it `{family}.png`
3. Drop in `/icons` folder
4. Done! Auto-detected

### To Test Everything:
1. Run app
2. Discover models
3. Select 3-4 models
4. Enable debate (2 rounds)
5. Enable web search (if configured)
6. Ask: "What are the latest AI developments?"
7. Watch the magic! ✨

---

## 🎊 Version Summary

**v4.3.0 - Stabilization Edition**

**New:**
- Model family icons with emoji fallbacks
- Google PSE web search integration
- Comprehensive setup help dialogs

**Retained:**
- Agentic debate system (v4.0)
- Round progress tracking (v4.0)
- Hybrid arena design (v4.0)
- Manual system (v4.0)
- All v3.6 features

---

## 💡 Pro Tips

**Icons:**
- The emojis look great! Don't worry about finding official logos
- You can mix PNGs and emoji fallbacks
- Unknown models still get initials (works fine)

**Web Search:**
- Use for: news, prices, current events
- Skip for: math, code, creative writing
- Free tier is 100 queries/day (plenty!)
- Disable when not needed (saves API calls)

**Debate:**
- Use 2-3 rounds for complex questions
- 1 round is fine for simple queries
- Watch the round counters!

---

## 🎉 You're Done!

Both Phase 1 and Phase 2 are COMPLETE! Your Kraken Kouncil is now a powerful AI orchestration system with:

- Beautiful visual design (icons + emojis)
- Real-time web knowledge (Google PSE)
- Advanced debate mechanics (multi-round refinement)
- Professional UX (progress tracking, help system)

Enjoy orchestrating your AI council! 🦑⚔️🌐💚

---

**Questions? Issues?**
- Check PHASE_1_COMPLETE.md for icon details
- Check PHASE_2_COMPLETE.md for web search setup
- Use the ❓ button in the app for user manual
- Settings dialogs have built-in help links

**Happy counciling!** ☕🎨

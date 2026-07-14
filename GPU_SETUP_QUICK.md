# ⚡ Quick Setup - GPU Monitoring

## 🎮 Get GPU Stats in 2 Steps

### Step 1: Install Package
```bash
pip install nvidia-ml-py
```

**Alternative:**
```bash
python -m pip install -r requirements-optional.txt
```

### Step 2: Run App
```bash
python kraken_council_v4_3_0.py
```

**That's it!** 🎉

---

## ✅ What You'll See

### With GPU:
```
🎮 GPU MONITOR
━━━━━━━━━━━━━━━━━━━━━
NVIDIA GeForce RTX 3080

Temp: 65°C  
Usage: 45%
Memory: 4500 / 10240 MB
```

### Without GPU:
```
🎮 GPU MONITOR
━━━━━━━━━━━━━━━━━━━━━
No GPU detected
```

---

## 🌈 Color Guide

### Temperature:
- 🟦 **< 60°C** - Cool
- 🟢 **60-70°C** - Normal  
- 🟡 **70-80°C** - Warm
- 🟠 **80-85°C** - Hot
- 🔴 **> 85°C** - Very Hot!

### Usage/Memory:
- 🟦 **< 30%** - Idle
- 🟢 **30-60%** - Working
- 🟡 **60-80%** - Busy
- 🟠 **> 80%** - Maxed

---

## 🔧 Troubleshooting

### nvidia-smi works but app doesn't show GPU?

```bash
pip uninstall nvidia-ml-py
pip install nvidia-ml-py
```

### Still not working?

```bash
python -m pip install -r requirements-optional.txt
```

### Linux permission error?

```bash
sudo usermod -a -G video $USER
# Log out and back in
```

---

## 📍 Location

**Left Sidebar:**
1. Model List (top)
2. Stats Panel
3. **🎮 GPU Monitor** ← Here!
4. Leaderboard (bottom)

---

## 💡 Why It's Useful

- **Temperature monitoring** - Prevent overheating
- **Memory tracking** - Avoid OOM errors
- **Usage monitoring** - Optimize concurrency
- **Real-time feedback** - See GPU work!

---

## 🚀 Ready!

GPU monitoring updates every 2 seconds automatically.

No configuration needed. Just works! ✨

---

*Updated: November 18, 2024*

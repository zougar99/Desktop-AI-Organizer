# 📁 Desktop-AI-Organizer — A powerful Windows desktop app that analyzes, organizes, and manages your desktop files with AI-powered categorization, duplicate detection, and smart cleanup

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/zougar99/Desktop-AI-Organizer/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/zougar99/Desktop-AI-Organizer?style=social)](https://github.com/zougar99/Desktop-AI-Organizer)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](https://github.com/zougar99/Desktop-AI-Organizer)

> A powerful Windows desktop app that analyzes, organizes, and manages your desktop files with AI-powered categorization, duplicate detection, and smart cleanup.

---

## 📖 Table of Contents
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [FAQ](#-faq)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features
- ✔ **AI Categorization** — Automatically sorts files by type, content, and context
- ✔ **Duplicate Detection** — Finds exact and near-duplicate files using content hashing
- ✔ **Smart Cleanup** — Identifies temp files, caches, and unused items older than N days
- ✔ **Rules Engine** — User-defined rules: move, copy, delete, archive based on patterns
- ✔ **Visual Dashboard** — Pie charts, storage trends, and category breakdowns
- ✔ **Undo System** — Full undo/redo for all organize operations
- ✔ **Scheduling** — Auto-run on schedule (daily/weekly/monthly)

---

## 🔮 How It Works

```
  Input ──► Processing Pipeline ──► Output
  ┌────────┐   ┌────────┐   ┌────────┐
  │ Data   │──►│ Engine │──►│ Result │
  │ Source │   │ Logic  │   │        │
  └────────┘   └────────┘   └────────┘
```

1. **Input** — Load data from file, API, or user input
2. **Process** — Core engine applies logic/analysis/transformation
3. **Output** — Results displayed in UI, saved to file, or sent via API

---

## 💻 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI | CustomTkinter |
| AI | OpenAI / local classifier |
| Database | SQLite |
| Platform | Windows |

---

## 🚀 Installation

```bash
git clone https://github.com/zougar99/Desktop-AI-Organizer.git
cd Desktop-AI-Organizer
pip install -r requirements.txt
```

---

## 📄 Configuration

Create a `config.yaml` or `.env` file in the project root:

```yaml
# Application settings
debug: false
port: 8080
theme: dark
language: en
```

---

## 🧰 Usage Guide

1. Launch: `python main.py`
2. Select the folder(s) to organize
3. Choose AI mode or manual rules
4. Preview changes before applying
5. Click **Apply** or schedule for later

---

## 🖼 Screenshots

> *(Screenshots coming soon. PRs welcome!)*

---

## 🔄 Roadmap

- 🟢 Web dashboard
- 🟡 Mobile companion app
- ⚫ API access
- ⚫ Plugin system
- ⚫ Multi-language support

---

## ❓ FAQ

### Does it modify files automatically?
No — all changes require your confirmation. Preview first.

### Can it organize network drives?
Yes — any accessible drive or folder is supported.

---

## 🚧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **App won't start** | Check Python version (3.10+); run `pip install -r requirements.txt` |
| **No output** | Check logs in `logs/` folder; enable debug mode in config |
| **Performance issues** | Close other applications; reduce batch size in config |
| **Dependency errors** | Create fresh venv: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📐 License
Distributed under the **MIT License**. See [`LICENSE`](https://github.com/zougar99/Desktop-AI-Organizer/blob/main/LICENSE) for more information.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/zougar99">zougar99</a>
</p>

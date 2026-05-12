# Desktop AI Organizer v3.0

A powerful Windows desktop application that analyzes, organizes, and manages your desktop files with AI-powered insights and a suite of power tools.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## About

Built and maintained by **WerList99** — developer focused on practical Windows tools, Python desktop apps, and clean UX.

```yaml
maintainer: WerList99
connect:
  telegram: "@werlist99 — https://t.me/werlist99"
  github: "https://github.com/zougar99"
  tech_blog: "https://werlist99.blogspot.com/"
  firefox_addons_mozilla_amo: "https://addons.mozilla.org/en-US/firefox/user/19705561/"
  extensions_hub: "https://extefw99.blogspot.com/"
focus:
  - Desktop automation & file workflows
  - Algorithms & data structures (performance-aware tooling)
  - Privacy-minded software
```

**Reach the maintainer:** [Telegram @werlist99](https://t.me/werlist99) · [GitHub @zougar99](https://github.com/zougar99) · [Tech blog](https://werlist99.blogspot.com/) · [Firefox add-ons (AMO)](https://addons.mozilla.org/en-US/firefox/user/19705561/) · [Extensions hub](https://extefw99.blogspot.com/)

---

## Features

### Core Analysis
- **Desktop Analysis** — Scans your desktop and calculates a health score (0-100) with clutter level assessment
- **Smart Categorization** — Automatically categorizes files (Images, Videos, Documents, Code, Archives, etc.)
- **Visual Charts** — Pie charts for file distribution and bar charts for file age analysis
- **AI Recommendations** — Smart suggestions based on file types, sizes, age, and duplicates

### Organization Tools
- **Auto-Organize** — One-click file organization into category folders (`_Images/`, `_Documents/`, etc.)
- **Undo Support** — Revert any file moves or renames with a single click
- **Batch Rename** — Rename multiple files with patterns (prefix, suffix, numbering, date, find & replace, case change)

### Power Tools
- **Duplicate Finder** — Deep hash-based scan to find exact duplicate files with wasted space calculation
- **Bulk Cleanup** — Find and remove old files, temp files, and large files with configurable filters
- **File Shredder** — Securely delete files with multi-pass overwrite (data is unrecoverable)
- **System Info** — Live dashboard showing OS info, disk usage, and RAM statistics

### Monitoring & Search
- **File Search** — Search files on your desktop by name
- **Live Watcher** — Real-time monitoring of desktop changes (add/remove/modify)
- **Export Reports** — Generate detailed text reports of your desktop analysis

## Screenshots

> *Coming soon*

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows OS

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/zougar99/Desktop-AI-Organizer.git
   cd Desktop-AI-Organizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

Or simply double-click `START_APP.bat` — it handles dependency installation and launches the app automatically.

## Project Structure

```
Desktop-AI-Organizer/
├── app.py                 # Main GUI application (sidebar + all pages)
├── desktop_analyzer.py    # Core engine (analysis, organization, tools)
├── test_gui.py            # GUI smoke test
├── requirements.txt       # Python dependencies
├── START_APP.bat          # Windows launcher script
└── README.md              # This file
```

## Tech Stack

| Technology | Purpose |
|---|---|
| **CustomTkinter** | Modern dark-themed GUI framework |
| **Matplotlib** | Charts and data visualization |
| **Pillow** | Image handling |
| **Python stdlib** | File ops, threading, hashing, ctypes for system info |

## How It Works

1. **Scan** — Analyzes all files and folders on your Windows desktop
2. **Score** — Calculates a health score based on clutter, duplicates, and organization
3. **Recommend** — Provides smart recommendations to clean up your desktop
4. **Organize** — Moves files into categorized folders with full undo support
5. **Maintain** — Use power tools to find duplicates, bulk rename, cleanup, and shred files

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.

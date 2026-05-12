"""
Desktop AI Organizer v2.0
A smart application that analyzes and organizes your desktop using AI-powered insights.
Features: Sidebar, Charts, Quick Actions, Search, Undo, Export, Desktop Watcher.
"""

import os
import sys
import json
import threading
import math
import io
import webbrowser
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, Canvas

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from desktop_analyzer import (
    analyze_desktop,
    get_organization_plan,
    execute_organization,
    undo_organization,
    has_undo_history,
    delete_empty_folders,
    search_desktop,
    export_report,
    format_size,
    DesktopWatcher,
    FILE_CATEGORIES,
    CATEGORY_EMOJIS,
    find_duplicates,
    delete_duplicate,
    batch_rename_preview,
    batch_rename_execute,
    undo_batch_rename,
    get_system_info,
    bulk_cleanup_scan,
    bulk_cleanup_execute,
    shred_files,
)

# ===================== THEME =====================

ctk.set_default_color_theme("blue")


def _settings_path():
    base = os.path.join(os.path.expanduser("~"), ".desktop_ai_organizer")
    return os.path.join(base, "settings.json")


DEFAULT_SETTINGS = {
    "appearance": "dark",
    "ui_scale": 1.0,
}

C = {
    "bg":           "#0d1117",
    "sidebar":      "#010409",
    "card":         "#161b22",
    "card_hover":   "#1c2333",
    "blue":         "#58a6ff",
    "green":        "#3fb950",
    "red":          "#f85149",
    "orange":       "#d29922",
    "purple":       "#bc8cff",
    "pink":         "#f778ba",
    "cyan":         "#56d4dd",
    "text":         "#f0f6fc",
    "text2":        "#8b949e",
    "text3":        "#484f58",
    "border":       "#30363d",
    "btn_hover":    "#1f2937",
}

CAT_COLORS = {
    "Images": "#58a6ff", "Videos": "#f85149", "Audio": "#d29922",
    "Documents": "#3fb950", "Text Files": "#8b949e", "Code / Scripts": "#bc8cff",
    "Archives": "#f778ba", "Executables": "#ff7b72", "Fonts": "#79c0ff",
    "3D / CAD": "#56d364", "Databases": "#d2a8ff", "Other": "#6e7681",
}


# ===================== MAIN APP =====================

class DesktopAIOrganizer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Desktop AI Organizer v3.0")
        self.geometry("1200x800")
        self.minsize(1000, 650)
        self.configure(fg_color=C["bg"])

        self.analysis_results = None
        self.organization_plan = None
        self.watcher = None
        self.watcher_events = []
        self.current_page = "dashboard"
        self._settings = self._load_settings()
        self._apply_settings_from_disk()

        self._build_layout()
        self._show_page("dashboard")

    def _build_layout(self):
        """Build sidebar + main area layout."""
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=C["sidebar"], width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=70)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame, text="[ AI ]",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=C["blue"],
        ).pack(side="left", padx=18, pady=18)
        ctk.CTkLabel(
            logo_frame, text="Desktop Organizer",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=C["text"],
        ).pack(side="left", pady=18)

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=C["border"], height=1).pack(fill="x", padx=12)

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard",    "Dashboard"),
            ("categories",   "Categories"),
            ("files",        "All Files"),
            ("folders",      "Folders"),
            ("search",       "Search"),
            ("duplicates",   "Duplicate Finder"),
            ("rename",       "Batch Rename"),
            ("cleanup",      "Bulk Cleanup"),
            ("shredder",     "File Shredder"),
            ("sysinfo",      "System Info"),
            ("quick",        "Quick Actions"),
            ("watcher",      "Live Monitor"),
            ("settings",     "Settings"),
            ("about",        "About"),
        ]

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=12)

        for key, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame, text="  {}".format(label),
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=C["btn_hover"],
                text_color=C["text2"], anchor="w", height=38, corner_radius=8,
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Bottom actions
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=8, pady=10)

        self.analyze_btn = ctk.CTkButton(
            bottom_frame, text="Analyze Desktop",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0",
            height=40, corner_radius=8,
            command=self._start_analysis,
        )
        self.analyze_btn.pack(fill="x", pady=3)

        self.organize_btn = ctk.CTkButton(
            bottom_frame, text="Organize Desktop",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["green"], hover_color="#2ea043",
            height=40, corner_radius=8, state="disabled",
            command=self._start_organization,
        )
        self.organize_btn.pack(fill="x", pady=3)

        self.undo_btn = ctk.CTkButton(
            bottom_frame, text="Undo Organization",
            font=ctk.CTkFont(size=12),
            fg_color=C["border"], hover_color=C["btn_hover"],
            text_color=C["orange"], height=34, corner_radius=8,
            command=self._undo_organization,
            state="normal" if has_undo_history() else "disabled",
        )
        self.undo_btn.pack(fill="x", pady=3)

        # Main content area
        self.content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

    def _load_settings(self):
        s = DEFAULT_SETTINGS.copy()
        path = _settings_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k in s:
                    if k in loaded:
                        s[k] = loaded[k]
        except Exception:
            pass
        app = str(s.get("appearance", "dark")).lower()
        if app not in ("dark", "light", "system"):
            s["appearance"] = "dark"
        else:
            s["appearance"] = app
        try:
            scale = float(s.get("ui_scale", 1.0))
        except (TypeError, ValueError):
            scale = 1.0
        s["ui_scale"] = max(0.8, min(1.25, scale))
        return s

    def _save_settings_to_disk(self):
        path = _settings_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception as ex:
            messagebox.showerror("Settings", "Could not save settings:\n{}".format(ex))
            return False
        return True

    def _apply_settings_from_disk(self):
        ctk.set_appearance_mode(self._settings.get("appearance", "dark"))
        scale = float(self._settings.get("ui_scale", 1.0))
        try:
            ctk.set_widget_scaling(scale)
        except Exception:
            pass
        try:
            ctk.set_window_scaling(scale)
        except Exception:
            pass

    def _highlight_nav(self, key):
        """Highlight active nav button."""
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=C["card"], text_color=C["blue"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text2"])

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_page(self, page):
        self.current_page = page
        self._highlight_nav(page)
        self._clear_content()

        pages = {
            "dashboard": self._page_dashboard,
            "categories": self._page_categories,
            "files": self._page_files,
            "folders": self._page_folders,
            "search": self._page_search,
            "duplicates": self._page_duplicates,
            "rename": self._page_rename,
            "cleanup": self._page_cleanup,
            "shredder": self._page_shredder,
            "sysinfo": self._page_sysinfo,
            "quick": self._page_quick_actions,
            "watcher": self._page_watcher,
            "settings": self._page_settings,
            "about": self._page_about,
        }
        pages.get(page, self._page_dashboard)()

    # ======================== HEADER UTIL ========================

    def _make_header(self, parent, title, subtitle=""):
        hdr = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=20, weight="bold"), text_color=C["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(hdr, text=subtitle, font=ctk.CTkFont(size=12), text_color=C["text2"]).pack(side="left", padx=12)

    def _make_scroll(self, parent):
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=C["border"])
        sf.pack(fill="both", expand=True, padx=15, pady=5)
        return sf

    def _no_data_label(self, parent):
        ctk.CTkLabel(
            parent,
            text="No analysis data yet.\nClick 'Analyze Desktop' to start.",
            font=ctk.CTkFont(size=14), text_color=C["text2"], justify="center",
        ).pack(expand=True)

    # ======================== DASHBOARD ========================

    def _page_dashboard(self):
        if not self.analysis_results:
            self._page_welcome()
            return

        r = self.analysis_results
        self._make_header(self.content, "Dashboard", "Scanned: {}".format(r.get("scan_time", "")))
        scroll = self._make_scroll(self.content)

        # --- Stats Row ---
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))
        stats = [
            ("Health", "{}/100".format(r["health_score"]), self._score_color(r["health_score"])),
            ("Files", str(r["total_files"]), C["blue"]),
            ("Folders", str(r["total_folders"]), C["purple"]),
            ("Size", format_size(r["total_size"]), C["orange"]),
            ("Clutter", r["clutter_level"], self._clutter_color(r["clutter_level"])),
            ("Categories", str(len([c for c in r["categories"] if r["categories"][c]["count"] > 0])), C["cyan"]),
        ]
        for i, (lbl, val, col) in enumerate(stats):
            stats_frame.grid_columnconfigure(i, weight=1)
            card = self._stat_card(stats_frame, lbl, val, col)
            card.grid(row=0, column=i, padx=4, sticky="ew")

        # --- Charts Row ---
        charts_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        charts_frame.pack(fill="x", pady=(0, 10))
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)

        # Pie chart: categories
        if HAS_MATPLOTLIB:
            pie_card = ctk.CTkFrame(charts_frame, fg_color=C["card"], corner_radius=12, height=300)
            pie_card.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
            pie_card.pack_propagate(False)
            ctk.CTkLabel(pie_card, text="File Distribution", font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text"]).pack(anchor="w", padx=12, pady=(10, 0))
            self._draw_pie_chart(pie_card, r)

            # Bar chart: age distribution
            bar_card = ctk.CTkFrame(charts_frame, fg_color=C["card"], corner_radius=12, height=300)
            bar_card.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
            bar_card.pack_propagate(False)
            ctk.CTkLabel(bar_card, text="File Age Distribution", font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text"]).pack(anchor="w", padx=12, pady=(10, 0))
            self._draw_bar_chart(bar_card, r.get("age_distribution", {}))

        # --- Recommendations ---
        rec_card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
        rec_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(rec_card, text="AI Recommendations", font=ctk.CTkFont(size=15, weight="bold"), text_color=C["green"]).pack(anchor="w", padx=15, pady=(12, 6))

        for i, rec in enumerate(r["recommendations"], 1):
            row = ctk.CTkFrame(rec_card, fg_color=C["card_hover"], corner_radius=8)
            row.pack(fill="x", padx=10, pady=2)

            # Color based on severity
            if "CRITICAL" in rec:
                icon_col = C["red"]
            elif "WARNING" in rec or "SECURITY" in rec or "PERFORMANCE" in rec:
                icon_col = C["orange"]
            else:
                icon_col = C["green"]

            ctk.CTkLabel(row, text="{}".format(i), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=icon_col, width=25).pack(side="left", padx=(10, 5), pady=8)
            ctk.CTkLabel(row, text=rec, font=ctk.CTkFont(size=12), text_color=C["text2"],
                         wraplength=650, justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=5, pady=8)
        ctk.CTkLabel(rec_card, text="").pack(pady=2)

        # --- Largest Files ---
        if r["largest_files"]:
            large_card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
            large_card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(large_card, text="Top 10 Largest Files", font=ctk.CTkFont(size=15, weight="bold"), text_color=C["orange"]).pack(anchor="w", padx=15, pady=(12, 6))
            for f in r["largest_files"][:10]:
                self._file_row(large_card, f)
            ctk.CTkLabel(large_card, text="").pack(pady=2)

    def _page_welcome(self):
        """Welcome page shown before first analysis."""
        center = ctk.CTkFrame(self.content, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center, text="[ AI ]", font=ctk.CTkFont(size=52, weight="bold"), text_color=C["blue"]).pack(pady=(0, 10))
        ctk.CTkLabel(center, text="Desktop AI Organizer", font=ctk.CTkFont(size=26, weight="bold"), text_color=C["text"]).pack(pady=(0, 5))
        ctk.CTkLabel(center, text="v3.0 — Smart Analysis, Organization & Power Tools", font=ctk.CTkFont(size=14), text_color=C["text2"]).pack(pady=(0, 25))

        features = [
            ("Smart Analysis", "AI-powered file categorization & health scoring"),
            ("Visual Charts", "Pie charts & bar graphs of file distribution"),
            ("Auto Organize", "One-click organization into category folders"),
            ("Duplicate Finder", "Deep hash scan to find exact duplicate files"),
            ("Batch Rename", "Rename files with patterns, numbering & dates"),
            ("Bulk Cleanup", "Find and remove old, temp & large files"),
            ("File Shredder", "Securely delete files with multi-pass overwrite"),
            ("System Info", "Live disk usage, RAM & OS information"),
            ("Undo Support", "Revert organization & renames at any time"),
            ("Live Monitor", "Real-time desktop change detection"),
            ("File Search", "Instantly find any file on your desktop"),
        ]
        for title, desc in features:
            row = ctk.CTkFrame(center, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=C["green"], width=130, anchor="e").pack(side="left")
            ctk.CTkLabel(row, text="  —  {}".format(desc), font=ctk.CTkFont(size=13), text_color=C["text2"], anchor="w").pack(side="left")

        ctk.CTkLabel(center, text="\nClick 'Analyze Desktop' to get started", font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=(15, 0))

    # ======================== CATEGORIES PAGE ========================

    def _page_categories(self):
        if not self.analysis_results:
            self._make_header(self.content, "Categories")
            self._no_data_label(self.content)
            return

        r = self.analysis_results
        self._make_header(self.content, "File Categories", "{} categories detected".format(
            len([c for c in r["categories"] if r["categories"][c]["count"] > 0])
        ))
        scroll = self._make_scroll(self.content)

        sorted_cats = sorted(r["categories"].items(), key=lambda x: x[1]["count"], reverse=True)
        max_count = max((d["count"] for _, d in sorted_cats if d["count"] > 0), default=1)

        for cat_name, cat_data in sorted_cats:
            if cat_data["count"] == 0:
                continue

            color = CAT_COLORS.get(cat_name, C["text2"])
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10)
            card.pack(fill="x", pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 4))

            tag = CATEGORY_EMOJIS.get(cat_name, "?")
            ctk.CTkLabel(top_row, text="[{}]".format(tag), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=color, width=50).pack(side="left")
            ctk.CTkLabel(top_row, text=cat_name, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=color).pack(side="left", padx=5)
            ctk.CTkLabel(top_row, text="{} files".format(cat_data["count"]),
                         font=ctk.CTkFont(size=12), text_color=C["text2"]).pack(side="left", padx=15)
            ctk.CTkLabel(top_row, text=format_size(cat_data["size"]),
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=C["text2"]).pack(side="right")

            # Progress bar
            ratio = cat_data["count"] / max_count if max_count > 0 else 0
            bar = ctk.CTkProgressBar(card, width=400, height=6, progress_color=color, fg_color=C["border"], corner_radius=3)
            bar.pack(fill="x", padx=12, pady=(0, 4))
            bar.set(ratio)

            # Files list (collapsible area - show first 5)
            files_text = ", ".join(cat_data["files"][:8])
            if len(cat_data["files"]) > 8:
                files_text += ", ... (+{} more)".format(len(cat_data["files"]) - 8)
            ctk.CTkLabel(card, text=files_text, font=ctk.CTkFont(size=11),
                         text_color=C["text3"], wraplength=700, justify="left", anchor="w").pack(padx=12, pady=(0, 8), anchor="w")

    # ======================== ALL FILES PAGE ========================

    def _page_files(self):
        if not self.analysis_results:
            self._make_header(self.content, "All Files")
            self._no_data_label(self.content)
            return

        r = self.analysis_results
        all_files = r.get("all_files", [])
        self._make_header(self.content, "All Files", "{} files on desktop".format(len(all_files)))

        # Sort controls
        ctrl = ctk.CTkFrame(self.content, fg_color="transparent", height=35)
        ctrl.pack(fill="x", padx=20, pady=(0, 5))
        ctrl.pack_propagate(False)

        ctk.CTkLabel(ctrl, text="Sort by:", font=ctk.CTkFont(size=12), text_color=C["text2"]).pack(side="left")

        self._file_sort_var = ctk.StringVar(value="size")
        for val, lbl in [("size", "Size"), ("name", "Name"), ("date", "Date"), ("category", "Type")]:
            rb = ctk.CTkRadioButton(ctrl, text=lbl, variable=self._file_sort_var, value=val,
                                    font=ctk.CTkFont(size=12), text_color=C["text2"],
                                    command=lambda: self._refresh_file_list(scroll, all_files))
            rb.pack(side="left", padx=8)

        scroll = self._make_scroll(self.content)
        self._refresh_file_list(scroll, all_files)

    def _refresh_file_list(self, scroll, all_files):
        for w in scroll.winfo_children():
            w.destroy()

        sort_key = self._file_sort_var.get() if hasattr(self, "_file_sort_var") else "size"
        if sort_key == "size":
            sorted_files = sorted(all_files, key=lambda x: x["size"], reverse=True)
        elif sort_key == "name":
            sorted_files = sorted(all_files, key=lambda x: x["name"].lower())
        elif sort_key == "date":
            sorted_files = sorted(all_files, key=lambda x: x["modified"], reverse=True)
        elif sort_key == "category":
            sorted_files = sorted(all_files, key=lambda x: x["category"])
        else:
            sorted_files = all_files

        for f in sorted_files:
            self._file_row(scroll, f, show_date=True)

    # ======================== FOLDERS PAGE ========================

    def _page_folders(self):
        if not self.analysis_results:
            self._make_header(self.content, "Folders")
            self._no_data_label(self.content)
            return

        r = self.analysis_results
        folders = r.get("all_folders", [])
        self._make_header(self.content, "Desktop Folders", "{} folders".format(len(folders)))
        scroll = self._make_scroll(self.content)

        if not folders:
            ctk.CTkLabel(scroll, text="No folders found on desktop.", font=ctk.CTkFont(size=13), text_color=C["text2"]).pack(pady=20)
            return

        for folder in folders:
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=8, height=40)
            card.pack(fill="x", pady=2)
            card.pack_propagate(False)

            ctk.CTkLabel(card, text="DIR", font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["orange"], width=40).pack(side="left", padx=(10, 5))
            ctk.CTkLabel(card, text=folder["name"], font=ctk.CTkFont(size=13),
                         text_color=C["text"], anchor="w").pack(side="left", fill="x", expand=True)

            items_count = folder.get("item_count", -1)
            if items_count >= 0:
                ctk.CTkLabel(card, text="{} items".format(items_count), font=ctk.CTkFont(size=11),
                             text_color=C["text3"]).pack(side="right", padx=10)

            depth = folder.get("depth", 0)
            if depth > 0:
                ctk.CTkLabel(card, text="depth: {}".format(depth), font=ctk.CTkFont(size=11),
                             text_color=C["text3"]).pack(side="right", padx=10)

            ctk.CTkLabel(card, text=folder.get("size_str", "N/A"), font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["purple"]).pack(side="right", padx=10)

    # ======================== SEARCH PAGE ========================

    def _page_search(self):
        self._make_header(self.content, "Search Desktop")

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent", height=45)
        search_frame.pack(fill="x", padx=20, pady=(5, 10))
        search_frame.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Type filename to search...",
            font=ctk.CTkFont(size=14), height=38, corner_radius=8,
            fg_color=C["card"], border_color=C["border"], text_color=C["text"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        ctk.CTkButton(
            search_frame, text="Search", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0", width=100, height=38, corner_radius=8,
            command=self._do_search,
        ).pack(side="right")

        self.search_results_frame = self._make_scroll(self.content)
        ctk.CTkLabel(self.search_results_frame, text="Type a filename and press Enter to search.",
                     font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        for w in self.search_results_frame.winfo_children():
            w.destroy()

        results = search_desktop(query, self.analysis_results)

        ctk.CTkLabel(self.search_results_frame,
                     text='Found {} results for "{}"'.format(len(results), query),
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=C["text"]).pack(anchor="w", pady=(5, 10))

        if not results:
            ctk.CTkLabel(self.search_results_frame, text="No files found matching your search.",
                         font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=10)
        else:
            for f in results:
                self._file_row(self.search_results_frame, f, show_date=True)

    # ======================== QUICK ACTIONS PAGE ========================

    def _page_quick_actions(self):
        self._make_header(self.content, "Quick Actions", "Useful tools for desktop maintenance")
        scroll = self._make_scroll(self.content)

        actions = [
            ("Delete Empty Folders", "Remove all empty folders from your desktop",
             C["red"], self._action_delete_empty),
            ("Export Analysis Report", "Save a detailed text report of your desktop analysis",
             C["blue"], self._action_export_report),
            ("Open Desktop Folder", "Open your desktop in Windows Explorer",
             C["orange"], self._action_open_desktop),
        ]

        for title, desc, color, cmd in actions:
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10)
            card.pack(fill="x", pady=4)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=15, pady=15)

            ctk.CTkLabel(info, text=title, font=ctk.CTkFont(size=15, weight="bold"), text_color=C["text"]).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=12), text_color=C["text2"]).pack(anchor="w")

            ctk.CTkButton(
                card, text="Run", font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=color, hover_color=C["btn_hover"],
                width=80, height=36, corner_radius=8, command=cmd,
            ).pack(side="right", padx=15, pady=15)

    def _action_delete_empty(self):
        if not messagebox.askyesno("Confirm", "Delete all empty folders on your desktop?"):
            return
        result = delete_empty_folders()
        messagebox.showinfo("Done", "Deleted {} empty folders.".format(result["deleted"]))
        if self.analysis_results:
            self._start_analysis()

    def _action_export_report(self):
        if not self.analysis_results:
            messagebox.showinfo("Info", "Run analysis first before exporting.")
            return
        path, _ = export_report(self.analysis_results)
        messagebox.showinfo("Exported", "Report saved to:\n{}".format(path))

    def _action_open_desktop(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.startfile(desktop)

    # ======================== WATCHER PAGE ========================

    def _page_watcher(self):
        self._make_header(self.content, "Live Desktop Monitor", "Watch for real-time changes")

        ctrl = ctk.CTkFrame(self.content, fg_color="transparent", height=45)
        ctrl.pack(fill="x", padx=20, pady=(5, 10))
        ctrl.pack_propagate(False)

        is_running = self.watcher and self.watcher.is_running

        self.watcher_status = ctk.CTkLabel(
            ctrl,
            text="Status: ACTIVE" if is_running else "Status: STOPPED",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C["green"] if is_running else C["red"],
        )
        self.watcher_status.pack(side="left")

        self.watcher_stop_btn = ctk.CTkButton(
            ctrl, text="Stop", font=ctk.CTkFont(size=13),
            fg_color=C["red"], hover_color="#c0392b", width=80, height=36, corner_radius=8,
            command=self._stop_watcher,
            state="normal" if is_running else "disabled",
        )
        self.watcher_stop_btn.pack(side="right", padx=5)

        self.watcher_start_btn = ctk.CTkButton(
            ctrl, text="Start Monitoring", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["green"], hover_color="#2ea043", width=140, height=36, corner_radius=8,
            command=self._start_watcher,
            state="disabled" if is_running else "normal",
        )
        self.watcher_start_btn.pack(side="right", padx=5)

        self.watcher_log_frame = self._make_scroll(self.content)

        # Show existing events
        if self.watcher_events:
            for evt in self.watcher_events[-50:]:
                self._add_watcher_event_row(evt)
        else:
            ctk.CTkLabel(self.watcher_log_frame,
                         text="Click 'Start Monitoring' to begin watching your desktop for changes.",
                         font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _start_watcher(self):
        if self.watcher and self.watcher.is_running:
            return
        self.watcher = DesktopWatcher(callback=self._on_watcher_change)
        self.watcher.start()
        self._show_page("watcher")

    def _stop_watcher(self):
        if self.watcher:
            self.watcher.stop()
        self._show_page("watcher")

    def _on_watcher_change(self, changes):
        for change in changes:
            timestamp = datetime.now().strftime("%H:%M:%S")
            evt = {"time": timestamp, **change}
            self.watcher_events.append(evt)
            if self.current_page == "watcher" and hasattr(self, "watcher_log_frame"):
                self.after(0, lambda e=evt: self._add_watcher_event_row(e))

    def _add_watcher_event_row(self, evt):
        if not hasattr(self, "watcher_log_frame") or not self.watcher_log_frame.winfo_exists():
            return

        colors = {"added": C["green"], "removed": C["red"], "modified": C["orange"]}
        labels = {"added": "+ ADDED", "removed": "- REMOVED", "modified": "~ MODIFIED"}

        row = ctk.CTkFrame(self.watcher_log_frame, fg_color=C["card"], corner_radius=6, height=32)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        color = colors.get(evt["type"], C["text2"])
        ctk.CTkLabel(row, text=evt["time"], font=ctk.CTkFont(size=11), text_color=C["text3"], width=70).pack(side="left", padx=8)
        ctk.CTkLabel(row, text=labels.get(evt["type"], "?"), font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=color, width=90).pack(side="left")
        ctk.CTkLabel(row, text=evt["name"], font=ctk.CTkFont(size=12), text_color=C["text"]).pack(side="left", padx=8)
        ctk.CTkLabel(row, text="({})".format(evt["item_type"]), font=ctk.CTkFont(size=11), text_color=C["text3"]).pack(side="left")

    # ======================== SETTINGS & ABOUT ========================

    def _page_settings(self):
        self._make_header(self.content, "Settings", "Appearance and interface scale")
        scroll = self._make_scroll(self.content)

        card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            card, text="Appearance",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=C["blue"],
        ).pack(anchor="w", padx=15, pady=(12, 6))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(
            row1, text="Theme mode", font=ctk.CTkFont(size=13),
            text_color=C["text2"], width=130, anchor="w",
        ).pack(side="left")
        app_var = ctk.StringVar(value=self._settings.get("appearance", "dark"))
        ctk.CTkOptionMenu(
            row1, values=["dark", "light", "system"], variable=app_var,
            width=200, height=32, corner_radius=8,
            fg_color=C["border"], button_color=C["blue"], button_hover_color="#4090e0",
        ).pack(side="left")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(12, 8))
        scale_val = float(self._settings.get("ui_scale", 1.0))
        scale_lbl = ctk.CTkLabel(
            row2, text="UI scale: {:.0f}%".format(scale_val * 100),
            font=ctk.CTkFont(size=13), text_color=C["text2"], width=130, anchor="w",
        )
        scale_lbl.pack(side="left")
        scale_var = ctk.DoubleVar(value=scale_val)

        def _on_scale(v):
            scale_lbl.configure(text="UI scale: {:.0f}%".format(float(v) * 100))

        slider = ctk.CTkSlider(
            row2, from_=0.8, to=1.25, number_of_steps=9,
            variable=scale_var, command=_on_scale,
            width=320, height=16, progress_color=C["blue"], fg_color=C["border"],
        )
        slider.pack(side="left", padx=(0, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 14))

        def _save_settings():
            self._settings["appearance"] = app_var.get()
            self._settings["ui_scale"] = float(scale_var.get())
            self._apply_settings_from_disk()
            if self._save_settings_to_disk():
                messagebox.showinfo("Settings", "Settings saved.")

        ctk.CTkButton(
            btn_row, text="Save settings", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["green"], hover_color="#2ea043", height=36, corner_radius=8,
            command=_save_settings,
        ).pack(side="left")

        ctk.CTkLabel(
            scroll,
            text="Settings file: {}".format(_settings_path()),
            font=ctk.CTkFont(size=11), text_color=C["text3"], anchor="w", justify="left",
        ).pack(anchor="w", padx=20, pady=(8, 4))

    def _page_about(self):
        self._make_header(self.content, "About", "Desktop AI Organizer")
        scroll = self._make_scroll(self.content)

        card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            card, text="Desktop AI Organizer",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=C["text"],
        ).pack(pady=(18, 4))
        ctk.CTkLabel(
            card, text="Version 3.0",
            font=ctk.CTkFont(size=13), text_color=C["text2"],
        ).pack()
        ctk.CTkLabel(
            card,
            text="A Windows desktop app to analyze clutter, organize files, find duplicates, "
                 "batch rename, clean up, and monitor changes—with charts and smart suggestions.",
            font=ctk.CTkFont(size=13), text_color=C["text2"],
            wraplength=640, justify="center",
        ).pack(padx=24, pady=14)

        ctk.CTkLabel(
            card, text="Maintainer",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["purple"],
        ).pack(anchor="w", padx=18, pady=(6, 4))
        ctk.CTkLabel(
            card, text="WerList99 — developer & tech blogger",
            font=ctk.CTkFont(size=13), text_color=C["text"],
        ).pack(anchor="w", padx=18)

        links = ctk.CTkFrame(card, fg_color="transparent")
        links.pack(fill="x", padx=15, pady=(14, 18))
        link_defs = [
            ("Telegram @werlist99", "https://t.me/werlist99"),
            ("GitHub — zougar99", "https://github.com/zougar99"),
            ("Tech blog", "https://werlist99.blogspot.com/"),
            ("Firefox add-ons (AMO)", "https://addons.mozilla.org/en-US/firefox/user/19705561/"),
            ("Extensions hub", "https://extefw99.blogspot.com/"),
        ]
        for label, url in link_defs:
            ctk.CTkButton(
                links, text=label, font=ctk.CTkFont(size=13),
                fg_color=C["border"], hover_color=C["btn_hover"], text_color=C["text"],
                height=36, corner_radius=8, anchor="w",
                command=lambda u=url: webbrowser.open(u),
            ).pack(fill="x", pady=3)

        ctk.CTkLabel(
            card, text="License: MIT",
            font=ctk.CTkFont(size=12), text_color=C["text3"],
        ).pack(pady=(0, 16))

    # ======================== DUPLICATE FINDER PAGE ========================

    def _page_duplicates(self):
        self._make_header(self.content, "Duplicate Finder", "Deep scan to find exact duplicate files")

        ctrl = ctk.CTkFrame(self.content, fg_color="transparent", height=50)
        ctrl.pack(fill="x", padx=20, pady=(5, 10))
        ctrl.pack_propagate(False)

        self._dup_scan_btn = ctk.CTkButton(
            ctrl, text="Scan for Duplicates", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0", width=180, height=38, corner_radius=8,
            command=self._start_dup_scan,
        )
        self._dup_scan_btn.pack(side="left")

        self._dup_status = ctk.CTkLabel(ctrl, text="", font=ctk.CTkFont(size=12), text_color=C["text2"])
        self._dup_status.pack(side="left", padx=15)

        self._dup_progress = ctk.CTkProgressBar(ctrl, width=200, height=8, progress_color=C["blue"], fg_color=C["border"])
        self._dup_progress.pack(side="right", padx=10)
        self._dup_progress.set(0)

        self._dup_scroll = self._make_scroll(self.content)
        ctk.CTkLabel(self._dup_scroll, text="Click 'Scan for Duplicates' to find exact duplicate files by content.",
                     font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _start_dup_scan(self):
        self._dup_scan_btn.configure(state="disabled", text="Scanning...")
        self._dup_progress.set(0)

        for w in self._dup_scroll.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._dup_scroll, text="Hashing files... This may take a moment.",
                     font=ctk.CTkFont(size=13), text_color=C["text2"]).pack(pady=20)

        def on_progress(p):
            self.after(0, lambda: self._dup_progress.set(p))

        def run():
            try:
                result = find_duplicates(progress_callback=on_progress)
                self.after(0, lambda: self._dup_scan_done(result))
            except Exception as e:
                self.after(0, lambda: self._dup_scan_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _dup_scan_done(self, result):
        self._dup_scan_btn.configure(state="normal", text="Re-Scan")
        self._dup_progress.set(1)
        self._dup_status.configure(
            text="{} duplicate groups found | {} wasted space".format(
                result["total_groups"], result["total_wasted_str"]
            )
        )

        for w in self._dup_scroll.winfo_children():
            w.destroy()

        if not result["groups"]:
            ctk.CTkLabel(self._dup_scroll, text="No duplicate files found! Your desktop is clean.",
                         font=ctk.CTkFont(size=14), text_color=C["green"]).pack(pady=20)
            return

        summary = ctk.CTkFrame(self._dup_scroll, fg_color=C["card"], corner_radius=10)
        summary.pack(fill="x", pady=(0, 10))
        row = ctk.CTkFrame(summary, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=12)
        for lbl, val, col in [
            ("Groups", str(result["total_groups"]), C["blue"]),
            ("Duplicates", str(result["total_duplicates"]), C["orange"]),
            ("Wasted Space", result["total_wasted_str"], C["red"]),
            ("Files Scanned", str(result["total_scanned"]), C["text2"]),
        ]:
            f = ctk.CTkFrame(row, fg_color="transparent")
            f.pack(side="left", expand=True)
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=col).pack()
            ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=11), text_color=C["text2"]).pack()

        for group in result["groups"]:
            card = ctk.CTkFrame(self._dup_scroll, fg_color=C["card"], corner_radius=10)
            card.pack(fill="x", pady=3)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(10, 4))
            ctk.CTkLabel(header, text="{} copies".format(group["count"]),
                         font=ctk.CTkFont(size=13, weight="bold"), text_color=C["red"]).pack(side="left")
            ctk.CTkLabel(header, text="Wasted: {}".format(group["wasted_str"]),
                         font=ctk.CTkFont(size=12), text_color=C["orange"]).pack(side="right")

            for f_info in group["files"]:
                f_row = ctk.CTkFrame(card, fg_color=C["card_hover"], corner_radius=6, height=32)
                f_row.pack(fill="x", padx=10, pady=1)
                f_row.pack_propagate(False)

                ctk.CTkLabel(f_row, text=f_info["name"], font=ctk.CTkFont(size=12),
                             text_color=C["text"], anchor="w").pack(side="left", padx=10, fill="x", expand=True)
                ctk.CTkLabel(f_row, text=f_info["size_str"], font=ctk.CTkFont(size=11),
                             text_color=C["text2"]).pack(side="right", padx=10)

                ctk.CTkButton(
                    f_row, text="Delete", width=60, height=24, corner_radius=6,
                    fg_color=C["red"], hover_color="#c0392b", font=ctk.CTkFont(size=11),
                    command=lambda p=f_info["path"]: self._delete_dup_file(p),
                ).pack(side="right", padx=5)

            ctk.CTkLabel(card, text="").pack(pady=2)

    def _delete_dup_file(self, filepath):
        name = os.path.basename(filepath)
        if not messagebox.askyesno("Confirm Delete", "Permanently delete '{}'?".format(name)):
            return
        result = delete_duplicate(filepath)
        if result["success"]:
            messagebox.showinfo("Deleted", result["message"])
        else:
            messagebox.showerror("Error", result["message"])

    def _dup_scan_error(self, msg):
        self._dup_scan_btn.configure(state="normal", text="Scan for Duplicates")
        messagebox.showerror("Error", "Duplicate scan failed:\n{}".format(msg))

    # ======================== BATCH RENAME PAGE ========================

    def _page_rename(self):
        self._make_header(self.content, "Batch Rename", "Rename multiple files with patterns")

        ctrl = ctk.CTkFrame(self.content, fg_color=C["card"], corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=(5, 10))

        # Pattern selection
        pat_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        pat_row.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(pat_row, text="Pattern:", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        self._rename_pattern = ctk.StringVar(value="prefix")
        patterns = [
            ("prefix", "Add Prefix"), ("suffix", "Add Suffix"), ("numbering", "Numbering"),
            ("date_prefix", "Date Prefix"), ("replace", "Find & Replace"),
            ("lowercase", "Lowercase"), ("uppercase", "Uppercase"), ("remove_spaces", "Remove Spaces"),
        ]

        for val, lbl in patterns:
            ctk.CTkRadioButton(
                pat_row, text=lbl, variable=self._rename_pattern, value=val,
                font=ctk.CTkFont(size=11), text_color=C["text2"],
                command=self._rename_preview_update,
            ).pack(side="left", padx=6)

        # Value input
        val_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        val_row.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(val_row, text="Value:", font=ctk.CTkFont(size=13), text_color=C["text"]).pack(side="left")

        self._rename_value = ctk.CTkEntry(
            val_row, placeholder_text="e.g. 'Project_' or 'old|new' for replace",
            font=ctk.CTkFont(size=13), height=34, corner_radius=8,
            fg_color=C["bg"], border_color=C["border"], text_color=C["text"], width=300,
        )
        self._rename_value.pack(side="left", padx=10)
        self._rename_value.bind("<KeyRelease>", lambda e: self._rename_preview_update())

        # Filter by extension
        ctk.CTkLabel(val_row, text="Filter ext:", font=ctk.CTkFont(size=12), text_color=C["text2"]).pack(side="left", padx=(15, 5))
        self._rename_ext = ctk.CTkEntry(
            val_row, placeholder_text=".png",
            font=ctk.CTkFont(size=12), height=34, corner_radius=8,
            fg_color=C["bg"], border_color=C["border"], text_color=C["text"], width=80,
        )
        self._rename_ext.pack(side="left")

        # Buttons
        btn_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(
            btn_row, text="Preview", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0", width=100, height=34, corner_radius=8,
            command=self._rename_preview_update,
        ).pack(side="left", padx=(0, 8))

        self._rename_exec_btn = ctk.CTkButton(
            btn_row, text="Rename All", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["green"], hover_color="#2ea043", width=120, height=34, corner_radius=8,
            command=self._rename_execute, state="disabled",
        )
        self._rename_exec_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Undo Last Rename", font=ctk.CTkFont(size=12),
            fg_color=C["border"], hover_color=C["btn_hover"], text_color=C["orange"],
            width=140, height=34, corner_radius=8, command=self._rename_undo,
        ).pack(side="left")

        self._rename_scroll = self._make_scroll(self.content)
        self._rename_plan = []
        ctk.CTkLabel(self._rename_scroll, text="Select a pattern and click Preview to see changes.",
                     font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _rename_preview_update(self):
        pattern = self._rename_pattern.get()
        value = self._rename_value.get() if hasattr(self, "_rename_value") else ""
        ext_filter = self._rename_ext.get().strip() if hasattr(self, "_rename_ext") else ""

        self._rename_plan = batch_rename_preview(
            pattern=pattern, value=value,
            filter_ext=ext_filter if ext_filter else None,
        )

        for w in self._rename_scroll.winfo_children():
            w.destroy()

        changed = [p for p in self._rename_plan if p["changed"]]
        self._rename_exec_btn.configure(state="normal" if changed else "disabled")

        if not self._rename_plan:
            ctk.CTkLabel(self._rename_scroll, text="No files found on desktop.",
                         font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)
            return

        ctk.CTkLabel(self._rename_scroll,
                     text="{} files will be renamed".format(len(changed)),
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=C["blue"]).pack(anchor="w", pady=(5, 8))

        for item in self._rename_plan:
            row = ctk.CTkFrame(self._rename_scroll, fg_color=C["card"], corner_radius=6, height=34)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            color = C["green"] if item["changed"] else C["text3"]
            ctk.CTkLabel(row, text=item["original"], font=ctk.CTkFont(size=12),
                         text_color=C["text2"], anchor="w", width=280).pack(side="left", padx=10)
            ctk.CTkLabel(row, text="->", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=item["new_name"], font=ctk.CTkFont(size=12),
                         text_color=color, anchor="w").pack(side="left", padx=10, fill="x", expand=True)

    def _rename_execute(self):
        changed = [p for p in self._rename_plan if p["changed"]]
        if not changed:
            return
        if not messagebox.askyesno("Confirm Rename", "Rename {} files? This can be undone.".format(len(changed))):
            return
        result = batch_rename_execute(self._rename_plan)
        messagebox.showinfo("Done", "Renamed {} files.".format(result["renamed"]))
        self._rename_preview_update()

    def _rename_undo(self):
        if not messagebox.askyesno("Confirm Undo", "Undo the last batch rename?"):
            return
        result = undo_batch_rename()
        messagebox.showinfo("Undo", result["message"])

    # ======================== BULK CLEANUP PAGE ========================

    def _page_cleanup(self):
        self._make_header(self.content, "Bulk Cleanup", "Find and remove old, temp, and large files")

        ctrl = ctk.CTkFrame(self.content, fg_color=C["card"], corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=(5, 10))

        opt_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        opt_row.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(opt_row, text="Min age (days):", font=ctk.CTkFont(size=12), text_color=C["text"]).pack(side="left")
        self._cleanup_age = ctk.CTkEntry(
            opt_row, width=60, height=32, font=ctk.CTkFont(size=12),
            fg_color=C["bg"], border_color=C["border"], text_color=C["text"],
        )
        self._cleanup_age.pack(side="left", padx=(5, 15))
        self._cleanup_age.insert(0, "180")

        ctk.CTkLabel(opt_row, text="Min size (MB):", font=ctk.CTkFont(size=12), text_color=C["text"]).pack(side="left")
        self._cleanup_size = ctk.CTkEntry(
            opt_row, width=60, height=32, font=ctk.CTkFont(size=12),
            fg_color=C["bg"], border_color=C["border"], text_color=C["text"],
        )
        self._cleanup_size.pack(side="left", padx=(5, 15))
        self._cleanup_size.insert(0, "50")

        self._cleanup_temp_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_row, text="Include temp files", variable=self._cleanup_temp_var,
            font=ctk.CTkFont(size=12), text_color=C["text2"],
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            opt_row, text="Scan", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0", width=80, height=34, corner_radius=8,
            command=self._run_cleanup_scan,
        ).pack(side="right")

        self._cleanup_scroll = self._make_scroll(self.content)
        self._cleanup_selected = []
        ctk.CTkLabel(self._cleanup_scroll, text="Configure filters and click Scan to find cleanup candidates.",
                     font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _run_cleanup_scan(self):
        try:
            age = int(self._cleanup_age.get())
        except ValueError:
            age = 180
        try:
            size_mb = int(self._cleanup_size.get())
        except ValueError:
            size_mb = 50

        result = bulk_cleanup_scan(
            min_age_days=age, min_size_mb=size_mb,
            include_temp=self._cleanup_temp_var.get(),
        )

        for w in self._cleanup_scroll.winfo_children():
            w.destroy()

        self._cleanup_selected = []
        self._cleanup_checkboxes = {}

        total = len(result["temp_files"]) + len(result["old_files"]) + len(result["large_files"])
        if total == 0:
            ctk.CTkLabel(self._cleanup_scroll, text="No cleanup candidates found. Your desktop is clean!",
                         font=ctk.CTkFont(size=14), text_color=C["green"]).pack(pady=20)
            return

        summary = ctk.CTkFrame(self._cleanup_scroll, fg_color=C["card"], corner_radius=10)
        summary.pack(fill="x", pady=(0, 10))
        s_row = ctk.CTkFrame(summary, fg_color="transparent")
        s_row.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(s_row, text="Potential space to reclaim: {}".format(result["total_reclaimable_str"]),
                     font=ctk.CTkFont(size=15, weight="bold"), text_color=C["green"]).pack(side="left")

        btn_row = ctk.CTkFrame(summary, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkButton(
            btn_row, text="Delete Selected (Recycle Bin)", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["orange"], hover_color="#b8860b", height=34, corner_radius=8,
            command=lambda: self._cleanup_delete("recycle"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Delete Selected (Permanent)", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["red"], hover_color="#c0392b", height=34, corner_radius=8,
            command=lambda: self._cleanup_delete("delete"),
        ).pack(side="left")

        sections = [
            ("Temporary Files", result["temp_files"], C["orange"]),
            ("Old Files ({}+ days)".format(age), result["old_files"], C["purple"]),
            ("Large Files ({}+ MB)".format(size_mb), result["large_files"], C["red"]),
        ]

        for title, files, color in sections:
            if not files:
                continue

            ctk.CTkLabel(self._cleanup_scroll, text="{} ({})".format(title, len(files)),
                         font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="w", pady=(10, 5), padx=5)

            for f_info in files:
                row = ctk.CTkFrame(self._cleanup_scroll, fg_color=C["card"], corner_radius=6, height=36)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)

                var = ctk.BooleanVar(value=False)
                cb = ctk.CTkCheckBox(row, text="", variable=var, width=24,
                                     checkbox_width=18, checkbox_height=18)
                cb.pack(side="left", padx=(8, 4))

                self._cleanup_checkboxes[f_info["path"]] = var

                ctk.CTkLabel(row, text=f_info["name"], font=ctk.CTkFont(size=12),
                             text_color=C["text"], anchor="w").pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(row, text=f_info["modified_str"], font=ctk.CTkFont(size=11),
                             text_color=C["text3"]).pack(side="right", padx=8)
                ctk.CTkLabel(row, text=f_info["size_str"], font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=C["orange"]).pack(side="right", padx=8)

    def _cleanup_delete(self, mode):
        selected = [path for path, var in self._cleanup_checkboxes.items() if var.get()]
        if not selected:
            messagebox.showinfo("Info", "No files selected. Check the boxes next to files you want to delete.")
            return

        mode_label = "Recycle Bin" if mode == "recycle" else "permanently delete"
        if not messagebox.askyesno("Confirm", "Send {} files to {}?".format(len(selected), mode_label)):
            return

        result = bulk_cleanup_execute(selected, mode=mode)
        msg = "Deleted {} files.".format(result["deleted"])
        if result["errors"]:
            msg += "\n{} errors occurred.".format(len(result["errors"]))
        messagebox.showinfo("Done", msg)
        self._run_cleanup_scan()

    # ======================== FILE SHREDDER PAGE ========================

    def _page_shredder(self):
        self._make_header(self.content, "File Shredder", "Securely delete files by overwriting data")

        warn = ctk.CTkFrame(self.content, fg_color="#2d1b1b", corner_radius=10)
        warn.pack(fill="x", padx=20, pady=(5, 10))
        ctk.CTkLabel(warn, text="WARNING: Shredded files CANNOT be recovered. Use with caution!",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=C["red"]).pack(padx=15, pady=12)

        ctrl = ctk.CTkFrame(self.content, fg_color=C["card"], corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=(0, 10))

        opt_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        opt_row.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(opt_row, text="Overwrite passes:", font=ctk.CTkFont(size=12), text_color=C["text"]).pack(side="left")
        self._shred_passes = ctk.CTkEntry(
            opt_row, width=50, height=32, font=ctk.CTkFont(size=12),
            fg_color=C["bg"], border_color=C["border"], text_color=C["text"],
        )
        self._shred_passes.pack(side="left", padx=(5, 15))
        self._shred_passes.insert(0, "3")

        ctk.CTkButton(
            opt_row, text="Load Desktop Files", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["blue"], hover_color="#4090e0", width=160, height=34, corner_radius=8,
            command=self._shredder_load_files,
        ).pack(side="left", padx=(0, 10))

        self._shred_exec_btn = ctk.CTkButton(
            opt_row, text="SHRED Selected", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["red"], hover_color="#c0392b", width=140, height=34, corner_radius=8,
            command=self._shredder_execute, state="disabled",
        )
        self._shred_exec_btn.pack(side="left")

        self._shred_progress = ctk.CTkProgressBar(opt_row, width=150, height=8,
                                                    progress_color=C["red"], fg_color=C["border"])
        self._shred_progress.pack(side="right", padx=10)
        self._shred_progress.set(0)

        self._shred_scroll = self._make_scroll(self.content)
        self._shred_checkboxes = {}
        ctk.CTkLabel(self._shred_scroll, text="Click 'Load Desktop Files' to select files for secure deletion.",
                     font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)

    def _shredder_load_files(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        for w in self._shred_scroll.winfo_children():
            w.destroy()

        self._shred_checkboxes = {}

        files = []
        try:
            for item in sorted(os.listdir(desktop)):
                item_path = os.path.join(desktop, item)
                if os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        files.append({"name": item, "path": item_path, "size": size, "size_str": format_size(size)})
                    except (OSError, PermissionError):
                        pass
        except (PermissionError, OSError):
            pass

        if not files:
            ctk.CTkLabel(self._shred_scroll, text="No files found on desktop.",
                         font=ctk.CTkFont(size=13), text_color=C["text3"]).pack(pady=20)
            return

        self._shred_exec_btn.configure(state="normal")

        ctk.CTkLabel(self._shred_scroll, text="Select files to shred ({} files on desktop):".format(len(files)),
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=C["text"]).pack(anchor="w", pady=(5, 8))

        for f_info in files:
            row = ctk.CTkFrame(self._shred_scroll, fg_color=C["card"], corner_radius=6, height=36)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(row, text="", variable=var, width=24, checkbox_width=18, checkbox_height=18)
            cb.pack(side="left", padx=(8, 4))
            self._shred_checkboxes[f_info["path"]] = var

            ctk.CTkLabel(row, text=f_info["name"], font=ctk.CTkFont(size=12),
                         text_color=C["text"], anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=f_info["size_str"], font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["orange"]).pack(side="right", padx=10)

    def _shredder_execute(self):
        selected = [path for path, var in self._shred_checkboxes.items() if var.get()]
        if not selected:
            messagebox.showinfo("Info", "No files selected.")
            return

        try:
            passes = int(self._shred_passes.get())
        except ValueError:
            passes = 3
        passes = max(1, min(passes, 10))

        confirm = messagebox.askyesno(
            "CONFIRM SHRED",
            "You are about to PERMANENTLY DESTROY {} files with {} overwrite passes.\n\n"
            "This action CANNOT be undone!\n\nAre you absolutely sure?".format(len(selected), passes)
        )
        if not confirm:
            return

        self._shred_exec_btn.configure(state="disabled", text="Shredding...")
        self._shred_progress.set(0)

        def on_progress(p):
            self.after(0, lambda: self._shred_progress.set(p))

        def run():
            result = shred_files(selected, passes=passes, progress_callback=on_progress)
            self.after(0, lambda: self._shredder_done(result))

        threading.Thread(target=run, daemon=True).start()

    def _shredder_done(self, result):
        self._shred_exec_btn.configure(state="normal", text="SHRED Selected")
        self._shred_progress.set(1)
        msg = "Securely shredded {} / {} files.".format(result["shredded"], result["total"])
        if result["errors"]:
            msg += "\n{} errors occurred.".format(len(result["errors"]))
        messagebox.showinfo("Shredder Complete", msg)
        self._shredder_load_files()

    # ======================== SYSTEM INFO PAGE ========================

    def _page_sysinfo(self):
        self._make_header(self.content, "System Info", "System and disk information")
        scroll = self._make_scroll(self.content)

        info = get_system_info()

        # OS Info Card
        os_card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
        os_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(os_card, text="Operating System", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C["blue"]).pack(anchor="w", padx=15, pady=(12, 6))

        os_items = [
            ("OS", "{} {} ({})".format(info["os"], info["os_release"], info["machine"])),
            ("Version", info["os_version"]),
            ("Hostname", info["hostname"]),
            ("Processor", info["processor"]),
            ("Python", info["python_version"]),
        ]
        for label, value in os_items:
            row = ctk.CTkFrame(os_card, fg_color=C["card_hover"], corner_radius=6, height=32)
            row.pack(fill="x", padx=10, pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["text2"], width=120, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12),
                         text_color=C["text"], anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(os_card, text="").pack(pady=2)

        # Disk Usage Card
        disk_card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
        disk_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(disk_card, text="Disk Usage ({})".format(info.get("disk_drive", "?")),
                     font=ctk.CTkFont(size=15, weight="bold"), text_color=C["orange"]).pack(anchor="w", padx=15, pady=(12, 6))

        disk_percent = info.get("disk_percent", 0)
        bar_color = C["green"] if disk_percent < 70 else C["orange"] if disk_percent < 90 else C["red"]

        usage_row = ctk.CTkFrame(disk_card, fg_color="transparent")
        usage_row.pack(fill="x", padx=15, pady=(0, 5))

        for lbl, val, col in [
            ("Total", info.get("disk_total_str", "N/A"), C["text"]),
            ("Used", info.get("disk_used_str", "N/A"), bar_color),
            ("Free", info.get("disk_free_str", "N/A"), C["green"]),
        ]:
            f = ctk.CTkFrame(usage_row, fg_color="transparent")
            f.pack(side="left", expand=True)
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=20, weight="bold"), text_color=col).pack()
            ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=11), text_color=C["text2"]).pack()

        bar = ctk.CTkProgressBar(disk_card, width=500, height=14, progress_color=bar_color, fg_color=C["border"], corner_radius=7)
        bar.pack(fill="x", padx=15, pady=(5, 5))
        bar.set(disk_percent / 100)

        ctk.CTkLabel(disk_card, text="{}% used".format(disk_percent),
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=bar_color).pack(pady=(0, 12))

        # RAM Card
        if info.get("ram_total_str", "N/A") != "N/A":
            ram_card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
            ram_card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(ram_card, text="Memory (RAM)", font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=C["purple"]).pack(anchor="w", padx=15, pady=(12, 6))

            ram_percent = info.get("ram_percent", 0)
            ram_color = C["green"] if ram_percent < 70 else C["orange"] if ram_percent < 90 else C["red"]

            ram_row = ctk.CTkFrame(ram_card, fg_color="transparent")
            ram_row.pack(fill="x", padx=15, pady=(0, 5))

            for lbl, val, col in [
                ("Total", info.get("ram_total_str", "N/A"), C["text"]),
                ("Used", info.get("ram_used_str", "N/A"), ram_color),
                ("Available", info.get("ram_available_str", "N/A"), C["green"]),
            ]:
                f = ctk.CTkFrame(ram_row, fg_color="transparent")
                f.pack(side="left", expand=True)
                ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=20, weight="bold"), text_color=col).pack()
                ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=11), text_color=C["text2"]).pack()

            ram_bar = ctk.CTkProgressBar(ram_card, width=500, height=14, progress_color=ram_color,
                                          fg_color=C["border"], corner_radius=7)
            ram_bar.pack(fill="x", padx=15, pady=(5, 5))
            ram_bar.set(ram_percent / 100)

            ctk.CTkLabel(ram_card, text="{}% used".format(ram_percent),
                         font=ctk.CTkFont(size=13, weight="bold"), text_color=ram_color).pack(pady=(0, 12))

    # ======================== HELPER WIDGETS ========================

    def _stat_card(self, parent, label, value, color):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=12, height=85)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(pady=(16, 1))
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color=C["text2"]).pack()
        return card

    def _file_row(self, parent, f, show_date=False):
        row = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=6, height=34)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        cat = f.get("category", "Other")
        color = CAT_COLORS.get(cat, C["text2"])
        tag = CATEGORY_EMOJIS.get(cat, "?")

        ctk.CTkLabel(row, text="[{}]".format(tag), font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=color, width=45).pack(side="left", padx=(8, 2))
        ctk.CTkLabel(row, text=f["name"], font=ctk.CTkFont(size=12),
                     text_color=C["text"], anchor="w").pack(side="left", fill="x", expand=True)

        if show_date:
            date_str = f.get("modified_str", "")
            ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=11), text_color=C["text3"]).pack(side="right", padx=8)

        ctk.CTkLabel(row, text=cat, font=ctk.CTkFont(size=11), text_color=color).pack(side="right", padx=8)
        ctk.CTkLabel(row, text=f.get("size_str", ""), font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["orange"]).pack(side="right", padx=8)

    def _score_color(self, score):
        if score >= 80: return C["green"]
        elif score >= 50: return C["orange"]
        return C["red"]

    def _clutter_color(self, level):
        return {"LOW": C["green"], "MODERATE": C["orange"], "HIGH": C["red"],
                "CRITICAL": C["red"], "EMPTY": C["text2"]}.get(level, C["text2"])

    # ======================== CHARTS ========================

    def _draw_pie_chart(self, parent, results):
        if not HAS_MATPLOTLIB:
            ctk.CTkLabel(parent, text="Install matplotlib for charts", text_color=C["text3"]).pack()
            return

        cats = {k: v for k, v in results["categories"].items() if v["count"] > 0}
        if not cats:
            return

        labels = list(cats.keys())
        sizes = [cats[k]["count"] for k in labels]
        colors = [CAT_COLORS.get(k, "#6e7681") for k in labels]

        fig = Figure(figsize=(4.2, 2.5), dpi=100, facecolor="#161b22")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#161b22")

        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, colors=colors, autopct="%1.0f%%",
            startangle=90, pctdistance=0.78,
            textprops={"fontsize": 8, "color": "#f0f6fc"},
        )

        for t in autotexts:
            t.set_fontsize(7)
            t.set_color("#f0f6fc")

        # Legend
        legend = ax.legend(
            wedges, ["{} ({})".format(l, s) for l, s in zip(labels, sizes)],
            loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7,
            facecolor="#161b22", edgecolor="#30363d", labelcolor="#8b949e",
        )

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def _draw_bar_chart(self, parent, data):
        if not HAS_MATPLOTLIB or not data:
            return

        labels = list(data.keys())
        values = list(data.values())
        colors_list = [C["green"], C["blue"], C["orange"], C["red"], C["purple"]]

        fig = Figure(figsize=(4.2, 2.5), dpi=100, facecolor="#161b22")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#161b22")

        bars = ax.bar(range(len(labels)), values, color=colors_list[:len(labels)], width=0.6, edgecolor="none")

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=7, color="#8b949e", rotation=15, ha="right")
        ax.tick_params(axis="y", labelsize=7, colors="#8b949e")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#30363d")
        ax.spines["bottom"].set_color("#30363d")

        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        str(val), ha="center", fontsize=8, color="#f0f6fc")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    # ======================== ANALYSIS ========================

    def _start_analysis(self):
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.organize_btn.configure(state="disabled")
        self._clear_content()

        # Loading screen
        center = ctk.CTkFrame(self.content, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center, text="Scanning...", font=ctk.CTkFont(size=30, weight="bold"), text_color=C["blue"]).pack(pady=(0, 10))
        ctk.CTkLabel(center, text="AI is analyzing your desktop files...", font=ctk.CTkFont(size=14), text_color=C["text2"]).pack(pady=(0, 18))

        self._progress = ctk.CTkProgressBar(center, width=350, height=8, progress_color=C["blue"], fg_color=C["border"])
        self._progress.pack()
        self._progress.set(0)
        self._animate_loading()

        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()

    def _animate_loading(self):
        if hasattr(self, "_progress") and self._progress.winfo_exists():
            curr = self._progress.get()
            if curr < 0.95:
                self._progress.set(curr + 0.015)
            self.after(80, self._animate_loading)

    def _run_analysis(self):
        try:
            results = analyze_desktop()
            self.analysis_results = results
            self.organization_plan = get_organization_plan(results)
            self.after(0, self._analysis_done)
        except Exception as e:
            self.after(0, lambda: self._analysis_error(str(e)))

    def _analysis_done(self):
        self.analyze_btn.configure(state="normal", text="Re-Analyze")
        self.organize_btn.configure(state="normal")
        self.undo_btn.configure(state="normal" if has_undo_history() else "disabled")
        self._show_page("dashboard")

    def _analysis_error(self, msg):
        self.analyze_btn.configure(state="normal", text="Analyze Desktop")
        messagebox.showerror("Error", "Analysis failed:\n{}".format(msg))
        self._show_page("dashboard")

    # ======================== ORGANIZATION ========================

    def _start_organization(self):
        if not self.organization_plan:
            messagebox.showinfo("Info", "No files to organize. Run analysis first.")
            return

        count = len(self.organization_plan)
        folders = set(item["folder"] for item in self.organization_plan)
        folder_list = "\n".join("  {}/".format(f) for f in sorted(folders))

        confirm = messagebox.askyesno(
            "Confirm Organization",
            "This will move {} files into {} category folders:\n\n{}\n\n"
            "You can undo this action later.\nProceed?".format(count, len(folders), folder_list),
        )
        if not confirm:
            return

        self.organize_btn.configure(state="disabled", text="Organizing...")
        thread = threading.Thread(target=self._run_organization, daemon=True)
        thread.start()

    def _run_organization(self):
        try:
            result = execute_organization(self.organization_plan)
            self.after(0, lambda: self._organization_done(result))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.organize_btn.configure(state="normal", text="Organize Desktop"))

    def _organization_done(self, result):
        msg = "Successfully organized {} files!".format(result["moved"])
        if result["errors"]:
            msg += "\n\n{} files had errors.".format(len(result["errors"]))
        messagebox.showinfo("Done!", msg)

        self.organize_btn.configure(text="Organize Desktop")
        self.undo_btn.configure(state="normal")
        self._start_analysis()

    def _undo_organization(self):
        if not messagebox.askyesno("Confirm Undo", "Move all files back to their original location?"):
            return
        result = undo_organization()
        messagebox.showinfo("Undo Complete", result["message"])
        self.undo_btn.configure(state="disabled")
        self._start_analysis()


# ======================== MAIN ========================

def main():
    app = DesktopAIOrganizer()
    app.mainloop()


if __name__ == "__main__":
    main()

"""
Desktop AI Analyzer Module — Enhanced v2.0
Analyzes desktop contents and provides AI-powered insights and recommendations.
Includes: undo support, file search, desktop watcher, export report.
"""

import os
import sys
import json
import time
import math
import shutil
import hashlib
import threading
from collections import defaultdict
from datetime import datetime, timedelta


# ===================== FILE CATEGORIES =====================

FILE_CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".tif", ".raw", ".psd", ".ai"},
    "Videos": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"},
    "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".epub"},
    "Text Files": {".txt", ".log", ".csv", ".md", ".json", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf"},
    "Code / Scripts": {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".cs", ".java", ".cpp", ".c", ".h",
                       ".bat", ".ps1", ".sh", ".vbs", ".rb", ".go", ".rs", ".php", ".sql", ".r", ".swift", ".kt"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".cab"},
    "Executables": {".exe", ".msi", ".dll", ".sys", ".com", ".scr", ".apk", ".dmg", ".deb", ".rpm"},
    "Fonts": {".ttf", ".otf", ".woff", ".woff2", ".eot"},
    "3D / CAD": {".stl", ".obj", ".fbx", ".blend", ".step", ".stp", ".dwg", ".dxf"},
    "Databases": {".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"},
}

CATEGORY_EMOJIS = {
    "Images": "IMG",
    "Videos": "VID",
    "Audio": "AUD",
    "Documents": "DOC",
    "Text Files": "TXT",
    "Code / Scripts": "CODE",
    "Archives": "ZIP",
    "Executables": "EXE",
    "Fonts": "FONT",
    "3D / CAD": "3D",
    "Databases": "DB",
    "Other": "?",
}


def get_category(filename):
    """Determine the category of a file based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    i = min(i, len(units) - 1)
    size = round(size_bytes / (1024 ** i), 2)
    return "{} {}".format(size, units[i])


def get_file_hash(filepath, chunk_size=8192):
    """Get MD5 hash of a file for duplicate detection."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


# ===================== MAIN ANALYSIS =====================

def analyze_desktop(desktop_path=None, deep_scan=False):
    """
    Perform a comprehensive AI analysis of the desktop.
    Returns a dictionary with analysis results.
    """
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    results = {
        "total_files": 0,
        "total_folders": 0,
        "total_size": 0,
        "categories": defaultdict(lambda: {"count": 0, "size": 0, "files": []}),
        "largest_files": [],
        "oldest_files": [],
        "newest_files": [],
        "duplicate_names": [],
        "duplicate_hashes": [],
        "empty_folders": [],
        "deep_folders": [],
        "recommendations": [],
        "health_score": 100,
        "clutter_level": "",
        "desktop_path": desktop_path,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "all_files": [],
        "all_folders": [],
        "extensions_map": defaultdict(int),
        "age_distribution": {"< 1 week": 0, "1-4 weeks": 0, "1-6 months": 0, "6-12 months": 0, "> 1 year": 0},
        "size_distribution": {"< 1 MB": 0, "1-10 MB": 0, "10-100 MB": 0, "100 MB - 1 GB": 0, "> 1 GB": 0},
    }

    all_files = []
    all_folders = []
    name_count = defaultdict(list)
    hash_map = defaultdict(list) if deep_scan else None

    # Scan desktop
    try:
        for item in os.listdir(desktop_path):
            item_path = os.path.join(desktop_path, item)

            if os.path.isfile(item_path):
                results["total_files"] += 1
                try:
                    stat = os.stat(item_path)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    created = datetime.fromtimestamp(stat.st_ctime)
                except (OSError, PermissionError):
                    size = 0
                    modified = datetime.now()
                    created = datetime.now()

                category = get_category(item)
                ext = os.path.splitext(item)[1].lower()
                if ext:
                    results["extensions_map"][ext] += 1

                results["total_size"] += size
                results["categories"][category]["count"] += 1
                results["categories"][category]["size"] += size
                results["categories"][category]["files"].append(item)

                # Age distribution
                age = (datetime.now() - modified).days
                if age < 7:
                    results["age_distribution"]["< 1 week"] += 1
                elif age < 30:
                    results["age_distribution"]["1-4 weeks"] += 1
                elif age < 180:
                    results["age_distribution"]["1-6 months"] += 1
                elif age < 365:
                    results["age_distribution"]["6-12 months"] += 1
                else:
                    results["age_distribution"]["> 1 year"] += 1

                # Size distribution
                if size < 1024 * 1024:
                    results["size_distribution"]["< 1 MB"] += 1
                elif size < 10 * 1024 * 1024:
                    results["size_distribution"]["1-10 MB"] += 1
                elif size < 100 * 1024 * 1024:
                    results["size_distribution"]["10-100 MB"] += 1
                elif size < 1024 * 1024 * 1024:
                    results["size_distribution"]["100 MB - 1 GB"] += 1
                else:
                    results["size_distribution"]["> 1 GB"] += 1

                file_info = {
                    "name": item,
                    "size": size,
                    "size_str": format_size(size),
                    "modified": modified,
                    "modified_str": modified.strftime("%Y-%m-%d %H:%M"),
                    "created": created,
                    "created_str": created.strftime("%Y-%m-%d %H:%M"),
                    "category": category,
                    "extension": ext,
                    "path": item_path,
                    "age_days": age,
                }
                all_files.append(file_info)

                base_name = os.path.splitext(item)[0].lower()
                name_count[base_name].append(item)

                # Deep scan: hash duplicates
                if deep_scan and size > 0 and size < 500 * 1024 * 1024:
                    file_hash = get_file_hash(item_path)
                    if file_hash:
                        hash_map[file_hash].append(item)

            elif os.path.isdir(item_path):
                results["total_folders"] += 1
                folder_info = {"name": item, "path": item_path}

                # Check if folder is empty
                try:
                    contents = os.listdir(item_path)
                    if len(contents) == 0:
                        results["empty_folders"].append(item)
                    folder_info["item_count"] = len(contents)
                except PermissionError:
                    folder_info["item_count"] = -1

                # Check folder depth
                try:
                    depth = _get_folder_depth(item_path)
                    folder_info["depth"] = depth
                    if depth > 5:
                        results["deep_folders"].append({"name": item, "depth": depth})
                except (PermissionError, OSError):
                    folder_info["depth"] = 0

                # Count subfolder size
                try:
                    folder_size = _get_folder_size(item_path)
                    results["total_size"] += folder_size
                    folder_info["size"] = folder_size
                    folder_info["size_str"] = format_size(folder_size)
                except (PermissionError, OSError):
                    folder_info["size"] = 0
                    folder_info["size_str"] = "N/A"

                all_folders.append(folder_info)

    except PermissionError:
        results["recommendations"].append("Cannot access desktop - permission denied.")
        return results

    # Sort and get top files
    if all_files:
        sorted_by_size = sorted(all_files, key=lambda x: x["size"], reverse=True)
        results["largest_files"] = sorted_by_size[:15]

        sorted_by_date_old = sorted(all_files, key=lambda x: x["modified"])
        results["oldest_files"] = sorted_by_date_old[:10]

        sorted_by_date_new = sorted(all_files, key=lambda x: x["modified"], reverse=True)
        results["newest_files"] = sorted_by_date_new[:10]

    # Find duplicates by name
    for name, files in name_count.items():
        if len(files) > 1:
            results["duplicate_names"].append({"base_name": name, "files": files})

    # Find duplicates by hash
    if deep_scan and hash_map:
        for h, files in hash_map.items():
            if len(files) > 1:
                results["duplicate_hashes"].append({"hash": h, "files": files})

    results["all_files"] = all_files
    results["all_folders"] = sorted(all_folders, key=lambda x: x.get("size", 0), reverse=True)

    # Calculate health score and generate recommendations
    _generate_ai_insights(results, all_files, all_folders)

    return results


def _get_folder_depth(path, max_depth=10):
    """Get the maximum depth of a folder."""
    if max_depth <= 0:
        return 0
    max_d = 0
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                d = _get_folder_depth(item_path, max_depth - 1) + 1
                max_d = max(max_d, d)
    except (PermissionError, OSError):
        pass
    return max_d


def _get_folder_size(path, max_depth=5):
    """Get total size of a folder."""
    total = 0
    if max_depth <= 0:
        return total
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                try:
                    total += os.path.getsize(item_path)
                except OSError:
                    pass
            elif os.path.isdir(item_path):
                total += _get_folder_size(item_path, max_depth - 1)
    except (PermissionError, OSError):
        pass
    return total


def _generate_ai_insights(results, all_files, all_folders):
    """Generate AI-powered insights and recommendations."""
    score = 100
    total_items = results["total_files"] + results["total_folders"]

    # --- Clutter Analysis ---
    if total_items > 100:
        results["clutter_level"] = "CRITICAL"
        score -= 40
        results["recommendations"].append(
            "CRITICAL: Your desktop is extremely cluttered with {} items. "
            "This can slow down your PC and make it hard to find things. "
            "Use 'Organize Desktop' to automatically sort files into categories.".format(total_items)
        )
    elif total_items > 50:
        results["clutter_level"] = "HIGH"
        score -= 25
        results["recommendations"].append(
            "WARNING: Your desktop has {} items which is quite cluttered. "
            "Organizing into folders will improve productivity and system performance.".format(total_items)
        )
    elif total_items > 20:
        results["clutter_level"] = "MODERATE"
        score -= 10
        results["recommendations"].append(
            "Your desktop has {} items. Consider organizing less-used files into folders.".format(total_items)
        )
    elif total_items > 0:
        results["clutter_level"] = "LOW"
        results["recommendations"].append(
            "Great job! Your desktop is relatively clean with only {} items.".format(total_items)
        )
    else:
        results["clutter_level"] = "EMPTY"
        results["recommendations"].append("Your desktop is empty!")

    # --- Large Files Analysis ---
    large_files = [f for f in all_files if f["size"] > 100 * 1024 * 1024]
    if large_files:
        score -= min(len(large_files) * 5, 20)
        names = ", ".join(f["name"] for f in large_files[:3])
        total_large = sum(f["size"] for f in large_files)
        results["recommendations"].append(
            "Found {} large files (>100MB) taking up {}. Examples: {}. "
            "Move them to a dedicated storage folder or external drive.".format(
                len(large_files), format_size(total_large), names
            )
        )

    # --- Old Files Analysis ---
    six_months_ago = datetime.now() - timedelta(days=180)
    old_files = [f for f in all_files if f["modified"] < six_months_ago]
    if old_files:
        score -= min(len(old_files) * 2, 15)
        results["recommendations"].append(
            "Found {} files not modified in 6+ months. "
            "Consider archiving or removing these unused files to free up space.".format(len(old_files))
        )

    # --- Executable Safety ---
    exe_data = results["categories"].get("Executables", {"count": 0})
    if isinstance(exe_data, dict) and exe_data.get("count", 0) > 5:
        score -= 10
        results["recommendations"].append(
            "SECURITY: You have {} executable files on desktop. "
            "For security, keep only trusted executables and scan unknown ones with antivirus.".format(exe_data["count"])
        )

    # --- Duplicate Analysis ---
    if results["duplicate_names"]:
        score -= min(len(results["duplicate_names"]) * 3, 15)
        dup_count = sum(len(d["files"]) for d in results["duplicate_names"])
        results["recommendations"].append(
            "Found {} potential duplicate file groups ({} files total). "
            "Review and remove duplicates to save space.".format(len(results["duplicate_names"]), dup_count)
        )

    # --- Empty Folders ---
    if results["empty_folders"]:
        score -= min(len(results["empty_folders"]) * 2, 10)
        examples = ", ".join(results["empty_folders"][:5])
        results["recommendations"].append(
            "Found {} empty folders: {}. "
            "Use 'Quick Actions' to clean them up.".format(len(results["empty_folders"]), examples)
        )

    # --- Size Analysis ---
    if results["total_size"] > 10 * 1024 * 1024 * 1024:
        score -= 15
        results["recommendations"].append(
            "PERFORMANCE: Your desktop takes up {} of space! "
            "This significantly impacts system performance and startup time. "
            "Move large projects and media files to other drives.".format(format_size(results["total_size"]))
        )
    elif results["total_size"] > 1 * 1024 * 1024 * 1024:
        score -= 5
        results["recommendations"].append(
            "Desktop size is {}. Consider moving large files to Documents or another drive.".format(
                format_size(results["total_size"])
            )
        )

    # --- Category Balance ---
    active_categories = len([c for c in results["categories"] if results["categories"][c]["count"] > 0])
    if active_categories >= 6:
        score -= 5
        results["recommendations"].append(
            "Files span {} different categories. Your desktop mixes code, documents, media, and more. "
            "Organizing by category will make things much easier to find.".format(active_categories)
        )

    # --- Performance Tip ---
    if results["total_folders"] > 20:
        score -= 5
        results["recommendations"].append(
            "PERFORMANCE: Having {} folders on desktop can slow down Windows icon rendering "
            "and increase boot time. Consider consolidating into fewer top-level folders.".format(results["total_folders"])
        )

    # --- Shortcut tip ---
    shortcut_count = results["extensions_map"].get(".lnk", 0)
    if shortcut_count > 15:
        results["recommendations"].append(
            "You have {} shortcuts on desktop. Consider using the Start Menu or taskbar "
            "for frequently used apps and remove unused shortcuts.".format(shortcut_count)
        )

    results["health_score"] = max(0, score)


# ===================== ORGANIZATION =====================

def get_organization_plan(analysis_results):
    """Generate a smart organization plan based on analysis results."""
    plan = []
    desktop_path = analysis_results["desktop_path"]

    for category, data in analysis_results["categories"].items():
        if data["count"] > 0:
            folder_name = "_{}".format(category.replace(" / ", "-").replace(" ", "-"))
            target_folder = os.path.join(desktop_path, folder_name)
            for filename in data["files"]:
                source = os.path.join(desktop_path, filename)
                destination = os.path.join(target_folder, filename)
                plan.append({
                    "source": source,
                    "destination": destination,
                    "category": category,
                    "folder": folder_name,
                    "filename": filename,
                })

    return plan


def execute_organization(plan, desktop_path=None):
    """Execute the organization plan by moving files. Saves undo info."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    moved = 0
    errors = []
    undo_log = []

    # Create category folders
    folders_needed = set(item["folder"] for item in plan)
    for folder in folders_needed:
        folder_path = os.path.join(desktop_path, folder)
        os.makedirs(folder_path, exist_ok=True)

    # Move files
    for item in plan:
        try:
            if os.path.exists(item["source"]):
                dest = item["destination"]
                if os.path.exists(dest):
                    base, ext = os.path.splitext(item["filename"])
                    counter = 1
                    while os.path.exists(dest):
                        new_name = "{} ({}){}".format(base, counter, ext)
                        dest = os.path.join(os.path.dirname(item["destination"]), new_name)
                        counter += 1

                shutil.move(item["source"], dest)
                undo_log.append({"from": dest, "to": item["source"]})
                moved += 1
        except (PermissionError, OSError) as e:
            errors.append({"file": item["filename"], "error": str(e)})

    # Save undo log
    if undo_log:
        _save_undo_log(undo_log, desktop_path)

    return {"moved": moved, "errors": errors, "can_undo": len(undo_log) > 0}


def _save_undo_log(undo_log, desktop_path):
    """Save undo log to a JSON file."""
    app_data_dir = os.path.join(desktop_path, "Desktop-AI-Organizer", ".data")
    os.makedirs(app_data_dir, exist_ok=True)
    log_path = os.path.join(app_data_dir, "undo_log.json")

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "moves": undo_log,
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def undo_organization(desktop_path=None):
    """Undo the last organization by moving files back."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    log_path = os.path.join(desktop_path, "Desktop-AI-Organizer", ".data", "undo_log.json")

    if not os.path.exists(log_path):
        return {"restored": 0, "errors": [], "message": "No undo history found."}

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    restored = 0
    errors = []

    for move in data.get("moves", []):
        try:
            src = move["from"]
            dst = move["to"]
            if os.path.exists(src):
                shutil.move(src, dst)
                restored += 1
        except (PermissionError, OSError) as e:
            errors.append({"file": move.get("from", "?"), "error": str(e)})

    # Clean up empty category folders
    try:
        for item in os.listdir(desktop_path):
            item_path = os.path.join(desktop_path, item)
            if os.path.isdir(item_path) and item.startswith("_"):
                try:
                    if len(os.listdir(item_path)) == 0:
                        os.rmdir(item_path)
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass

    # Remove undo log
    try:
        os.remove(log_path)
    except OSError:
        pass

    return {"restored": restored, "errors": errors, "message": "Restored {} files.".format(restored)}


def has_undo_history(desktop_path=None):
    """Check if undo history exists."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    log_path = os.path.join(desktop_path, "Desktop-AI-Organizer", ".data", "undo_log.json")
    return os.path.exists(log_path)


# ===================== QUICK ACTIONS =====================

def delete_empty_folders(desktop_path=None):
    """Delete all empty folders on the desktop."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    deleted = 0
    errors = []

    try:
        for item in os.listdir(desktop_path):
            item_path = os.path.join(desktop_path, item)
            if os.path.isdir(item_path):
                try:
                    if len(os.listdir(item_path)) == 0:
                        os.rmdir(item_path)
                        deleted += 1
                except (PermissionError, OSError) as e:
                    errors.append({"folder": item, "error": str(e)})
    except (PermissionError, OSError) as e:
        errors.append({"folder": "desktop", "error": str(e)})

    return {"deleted": deleted, "errors": errors}


# ===================== SEARCH =====================

def search_desktop(query, analysis_results=None, desktop_path=None):
    """Search for files on the desktop matching the query."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    query_lower = query.lower().strip()
    results = []

    # If we have analysis data, search in memory
    if analysis_results and "all_files" in analysis_results:
        for f in analysis_results["all_files"]:
            if query_lower in f["name"].lower():
                results.append(f)
    else:
        # Scan desktop directly
        try:
            for item in os.listdir(desktop_path):
                item_path = os.path.join(desktop_path, item)
                if os.path.isfile(item_path) and query_lower in item.lower():
                    try:
                        stat = os.stat(item_path)
                        results.append({
                            "name": item,
                            "size": stat.st_size,
                            "size_str": format_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "modified_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                            "category": get_category(item),
                            "path": item_path,
                        })
                    except (OSError, PermissionError):
                        pass
        except (PermissionError, OSError):
            pass

    return results


# ===================== EXPORT REPORT =====================

def export_report(analysis_results, output_path=None):
    """Export analysis results to a text report."""
    if output_path is None:
        desktop_path = analysis_results.get("desktop_path", os.path.join(os.path.expanduser("~"), "Desktop"))
        output_path = os.path.join(desktop_path, "Desktop-AI-Organizer", "desktop_report.txt")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = []
    lines.append("=" * 60)
    lines.append("  DESKTOP AI ORGANIZER — ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Scan Date: {}".format(analysis_results.get("scan_time", "N/A")))
    lines.append("Desktop Path: {}".format(analysis_results.get("desktop_path", "N/A")))
    lines.append("")
    lines.append("-" * 40)
    lines.append("  OVERVIEW")
    lines.append("-" * 40)
    lines.append("  Health Score:   {}/100".format(analysis_results["health_score"]))
    lines.append("  Clutter Level:  {}".format(analysis_results["clutter_level"]))
    lines.append("  Total Files:    {}".format(analysis_results["total_files"]))
    lines.append("  Total Folders:  {}".format(analysis_results["total_folders"]))
    lines.append("  Total Size:     {}".format(format_size(analysis_results["total_size"])))
    lines.append("")

    lines.append("-" * 40)
    lines.append("  FILE CATEGORIES")
    lines.append("-" * 40)
    sorted_cats = sorted(
        analysis_results["categories"].items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )
    for cat_name, cat_data in sorted_cats:
        if cat_data["count"] > 0:
            lines.append("  {:20s}  {:>4} files  {:>12s}".format(
                cat_name, cat_data["count"], format_size(cat_data["size"])
            ))
    lines.append("")

    lines.append("-" * 40)
    lines.append("  AGE DISTRIBUTION")
    lines.append("-" * 40)
    for age_range, count in analysis_results.get("age_distribution", {}).items():
        if count > 0:
            lines.append("  {:20s}  {:>4} files".format(age_range, count))
    lines.append("")

    lines.append("-" * 40)
    lines.append("  SIZE DISTRIBUTION")
    lines.append("-" * 40)
    for size_range, count in analysis_results.get("size_distribution", {}).items():
        if count > 0:
            lines.append("  {:20s}  {:>4} files".format(size_range, count))
    lines.append("")

    lines.append("-" * 40)
    lines.append("  AI RECOMMENDATIONS")
    lines.append("-" * 40)
    for i, rec in enumerate(analysis_results["recommendations"], 1):
        lines.append("  {}. {}".format(i, rec))
    lines.append("")

    lines.append("-" * 40)
    lines.append("  LARGEST FILES")
    lines.append("-" * 40)
    for f in analysis_results["largest_files"][:10]:
        lines.append("  {:>12s}  {}".format(f["size_str"], f["name"]))
    lines.append("")

    if analysis_results["empty_folders"]:
        lines.append("-" * 40)
        lines.append("  EMPTY FOLDERS")
        lines.append("-" * 40)
        for folder in analysis_results["empty_folders"]:
            lines.append("  - {}".format(folder))
        lines.append("")

    lines.append("=" * 60)
    lines.append("  Report generated by Desktop AI Organizer v2.0")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return output_path, report_text


# ===================== DESKTOP WATCHER =====================

class DesktopWatcher:
    """Monitors desktop for real-time changes."""

    def __init__(self, desktop_path=None, callback=None):
        self.desktop_path = desktop_path or os.path.join(os.path.expanduser("~"), "Desktop")
        self.callback = callback
        self._running = False
        self._thread = None
        self._last_snapshot = {}

    def start(self):
        """Start watching the desktop."""
        if self._running:
            return
        self._running = True
        self._last_snapshot = self._take_snapshot()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop watching the desktop."""
        self._running = False

    def _take_snapshot(self):
        """Take a snapshot of current desktop state."""
        snapshot = {}
        try:
            for item in os.listdir(self.desktop_path):
                item_path = os.path.join(self.desktop_path, item)
                try:
                    stat = os.stat(item_path)
                    snapshot[item] = {
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "is_dir": os.path.isdir(item_path),
                    }
                except (OSError, PermissionError):
                    pass
        except (PermissionError, OSError):
            pass
        return snapshot

    def _watch_loop(self):
        """Main watch loop."""
        while self._running:
            try:
                time.sleep(3)
                new_snapshot = self._take_snapshot()

                changes = []

                # Check for new items
                for name in new_snapshot:
                    if name not in self._last_snapshot:
                        item_type = "folder" if new_snapshot[name]["is_dir"] else "file"
                        changes.append({
                            "type": "added",
                            "name": name,
                            "item_type": item_type,
                        })

                # Check for removed items
                for name in self._last_snapshot:
                    if name not in new_snapshot:
                        item_type = "folder" if self._last_snapshot[name]["is_dir"] else "file"
                        changes.append({
                            "type": "removed",
                            "name": name,
                            "item_type": item_type,
                        })

                # Check for modified items
                for name in new_snapshot:
                    if name in self._last_snapshot:
                        old = self._last_snapshot[name]
                        new = new_snapshot[name]
                        if old["mtime"] != new["mtime"] or old["size"] != new["size"]:
                            changes.append({
                                "type": "modified",
                                "name": name,
                                "item_type": "folder" if new["is_dir"] else "file",
                            })

                self._last_snapshot = new_snapshot

                if changes and self.callback:
                    self.callback(changes)

            except Exception:
                pass

    @property
    def is_running(self):
        return self._running


# ===================== DUPLICATE FINDER =====================

def find_duplicates(desktop_path=None, progress_callback=None):
    """
    Deep scan to find duplicate files by content hash.
    Returns groups of duplicate files.
    """
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    size_map = defaultdict(list)

    all_files = []
    for item in os.listdir(desktop_path):
        item_path = os.path.join(desktop_path, item)
        if os.path.isfile(item_path):
            try:
                size = os.path.getsize(item_path)
                all_files.append((item, item_path, size))
                size_map[size].append((item, item_path))
            except (OSError, PermissionError):
                pass

    candidates = {s: files for s, files in size_map.items() if len(files) > 1}

    hash_groups = defaultdict(list)
    total = sum(len(files) for files in candidates.values())
    scanned = 0

    for size, files in candidates.items():
        for name, path in files:
            file_hash = get_file_hash(path)
            if file_hash:
                hash_groups[file_hash].append({
                    "name": name,
                    "path": path,
                    "size": size,
                    "size_str": format_size(size),
                })
            scanned += 1
            if progress_callback:
                progress_callback(scanned / total if total > 0 else 1)

    duplicates = []
    total_wasted = 0
    for h, files in hash_groups.items():
        if len(files) > 1:
            wasted = files[0]["size"] * (len(files) - 1)
            total_wasted += wasted
            duplicates.append({
                "hash": h,
                "files": files,
                "count": len(files),
                "wasted_space": wasted,
                "wasted_str": format_size(wasted),
            })

    duplicates.sort(key=lambda x: x["wasted_space"], reverse=True)

    return {
        "groups": duplicates,
        "total_groups": len(duplicates),
        "total_duplicates": sum(d["count"] for d in duplicates),
        "total_wasted": total_wasted,
        "total_wasted_str": format_size(total_wasted),
        "total_scanned": len(all_files),
    }


def delete_duplicate(filepath):
    """Delete a single duplicate file."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"success": True, "message": "Deleted: {}".format(os.path.basename(filepath))}
    except (OSError, PermissionError) as e:
        return {"success": False, "message": str(e)}
    return {"success": False, "message": "File not found"}


# ===================== BATCH RENAME =====================

def batch_rename_preview(desktop_path=None, pattern="prefix", value="", filter_ext=None):
    """
    Preview batch rename results.
    Patterns: prefix, suffix, replace, numbering, date_prefix, lowercase, uppercase
    """
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    preview = []
    files = []

    for item in sorted(os.listdir(desktop_path)):
        item_path = os.path.join(desktop_path, item)
        if not os.path.isfile(item_path):
            continue
        if filter_ext and not item.lower().endswith(filter_ext.lower()):
            continue
        files.append((item, item_path))

    for i, (name, path) in enumerate(files, 1):
        base, ext = os.path.splitext(name)

        if pattern == "prefix":
            new_name = "{}{}".format(value, name)
        elif pattern == "suffix":
            new_name = "{}{}{}".format(base, value, ext)
        elif pattern == "replace":
            parts = value.split("|", 1)
            if len(parts) == 2:
                new_name = name.replace(parts[0], parts[1])
            else:
                new_name = name
        elif pattern == "numbering":
            pad = len(str(len(files)))
            new_name = "{}{:0{}d} - {}".format(value, i, pad, name)
        elif pattern == "date_prefix":
            try:
                mtime = os.path.getmtime(path)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                new_name = "{} {}".format(date_str, name)
            except OSError:
                new_name = name
        elif pattern == "lowercase":
            new_name = name.lower()
        elif pattern == "uppercase":
            new_name = name.upper()
        elif pattern == "remove_spaces":
            new_name = name.replace(" ", "_")
        else:
            new_name = name

        preview.append({
            "original": name,
            "new_name": new_name,
            "path": path,
            "changed": name != new_name,
        })

    return preview


def batch_rename_execute(rename_plan, desktop_path=None):
    """Execute batch rename from a preview plan."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    renamed = 0
    errors = []
    undo_renames = []

    for item in rename_plan:
        if not item.get("changed", False):
            continue
        old_path = item["path"]
        new_path = os.path.join(desktop_path, item["new_name"])

        if os.path.exists(new_path) and old_path != new_path:
            errors.append({"file": item["original"], "error": "Target name already exists"})
            continue

        try:
            os.rename(old_path, new_path)
            undo_renames.append({"from": new_path, "to": old_path})
            renamed += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": item["original"], "error": str(e)})

    if undo_renames:
        app_data_dir = os.path.join(desktop_path, "Desktop-AI-Organizer", ".data")
        os.makedirs(app_data_dir, exist_ok=True)
        log_path = os.path.join(app_data_dir, "rename_undo.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "renames": undo_renames}, f, indent=2)

    return {"renamed": renamed, "errors": errors}


def undo_batch_rename(desktop_path=None):
    """Undo the last batch rename."""
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    log_path = os.path.join(desktop_path, "Desktop-AI-Organizer", ".data", "rename_undo.json")
    if not os.path.exists(log_path):
        return {"restored": 0, "message": "No rename history found."}

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    restored = 0
    for item in data.get("renames", []):
        try:
            if os.path.exists(item["from"]):
                os.rename(item["from"], item["to"])
                restored += 1
        except (OSError, PermissionError):
            pass

    try:
        os.remove(log_path)
    except OSError:
        pass

    return {"restored": restored, "message": "Restored {} filenames.".format(restored)}


# ===================== SYSTEM INFO =====================

def get_system_info():
    """Gather system and disk information."""
    import platform

    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or "N/A",
        "python_version": platform.python_version(),
        "hostname": platform.node(),
    }

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    drive = os.path.splitdrive(desktop_path)[0] or "/"

    try:
        if sys.platform == "win32":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                drive + "\\", None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes)
            )
            info["disk_total"] = total_bytes.value
            info["disk_free"] = free_bytes.value
            info["disk_used"] = total_bytes.value - free_bytes.value
            info["disk_total_str"] = format_size(total_bytes.value)
            info["disk_free_str"] = format_size(free_bytes.value)
            info["disk_used_str"] = format_size(total_bytes.value - free_bytes.value)
            info["disk_percent"] = round((1 - free_bytes.value / total_bytes.value) * 100, 1) if total_bytes.value > 0 else 0
            info["disk_drive"] = drive
        else:
            st = os.statvfs(desktop_path)
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            info["disk_total"] = total
            info["disk_free"] = free
            info["disk_used"] = total - free
            info["disk_total_str"] = format_size(total)
            info["disk_free_str"] = format_size(free)
            info["disk_used_str"] = format_size(total - free)
            info["disk_percent"] = round((1 - free / total) * 100, 1) if total > 0 else 0
            info["disk_drive"] = "/"
    except Exception:
        info["disk_total_str"] = "N/A"
        info["disk_free_str"] = "N/A"
        info["disk_used_str"] = "N/A"
        info["disk_percent"] = 0
        info["disk_drive"] = drive

    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.pointer(mem))
            info["ram_total"] = mem.ullTotalPhys
            info["ram_available"] = mem.ullAvailPhys
            info["ram_used"] = mem.ullTotalPhys - mem.ullAvailPhys
            info["ram_total_str"] = format_size(mem.ullTotalPhys)
            info["ram_available_str"] = format_size(mem.ullAvailPhys)
            info["ram_used_str"] = format_size(mem.ullTotalPhys - mem.ullAvailPhys)
            info["ram_percent"] = mem.dwMemoryLoad
    except Exception:
        info["ram_total_str"] = "N/A"
        info["ram_available_str"] = "N/A"
        info["ram_percent"] = 0

    return info


# ===================== BULK CLEANUP =====================

def bulk_cleanup_scan(desktop_path=None, min_age_days=180, min_size_mb=0, include_temp=True):
    """
    Scan for files that are candidates for cleanup.
    Returns categorized cleanup suggestions.
    """
    if desktop_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    temp_extensions = {".tmp", ".temp", ".bak", ".old", ".cache", ".log", ".dmp", ".crash", ".~"}
    results = {
        "old_files": [],
        "large_files": [],
        "temp_files": [],
        "total_reclaimable": 0,
    }

    cutoff = datetime.now() - timedelta(days=min_age_days)
    min_size_bytes = min_size_mb * 1024 * 1024

    try:
        for item in os.listdir(desktop_path):
            item_path = os.path.join(desktop_path, item)
            if not os.path.isfile(item_path):
                continue

            try:
                stat = os.stat(item_path)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                ext = os.path.splitext(item)[1].lower()
            except (OSError, PermissionError):
                continue

            file_info = {
                "name": item,
                "path": item_path,
                "size": size,
                "size_str": format_size(size),
                "modified": modified,
                "modified_str": modified.strftime("%Y-%m-%d"),
                "age_days": (datetime.now() - modified).days,
                "category": get_category(item),
            }

            if include_temp and ext in temp_extensions:
                results["temp_files"].append(file_info)
                results["total_reclaimable"] += size

            if modified < cutoff:
                results["old_files"].append(file_info)
                if ext not in temp_extensions:
                    results["total_reclaimable"] += size

            if min_size_bytes > 0 and size >= min_size_bytes:
                results["large_files"].append(file_info)

    except (PermissionError, OSError):
        pass

    results["old_files"].sort(key=lambda x: x["modified"])
    results["large_files"].sort(key=lambda x: x["size"], reverse=True)
    results["total_reclaimable_str"] = format_size(results["total_reclaimable"])

    return results


def bulk_cleanup_execute(file_paths, mode="recycle"):
    """
    Execute cleanup on selected files.
    mode: 'recycle' (move to recycle bin) or 'delete' (permanent delete)
    """
    deleted = 0
    errors = []

    for filepath in file_paths:
        try:
            if os.path.exists(filepath):
                if mode == "recycle" and sys.platform == "win32":
                    try:
                        import ctypes
                        from ctypes import wintypes
                        shell32 = ctypes.windll.shell32
                        SHFileOperationW = shell32.SHFileOperationW

                        class SHFILEOPSTRUCT(ctypes.Structure):
                            _fields_ = [
                                ("hwnd", wintypes.HWND),
                                ("wFunc", ctypes.c_uint),
                                ("pFrom", ctypes.c_wchar_p),
                                ("pTo", ctypes.c_wchar_p),
                                ("fFlags", ctypes.c_ushort),
                                ("fAnyOperationsAborted", wintypes.BOOL),
                                ("hNameMappings", ctypes.c_void_p),
                                ("lpszProgressTitle", ctypes.c_wchar_p),
                            ]

                        FO_DELETE = 3
                        FOF_ALLOWUNDO = 0x0040
                        FOF_NOCONFIRMATION = 0x0010
                        FOF_SILENT = 0x0004

                        op = SHFILEOPSTRUCT()
                        op.wFunc = FO_DELETE
                        op.pFrom = filepath + "\0"
                        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

                        result = SHFileOperationW(ctypes.byref(op))
                        if result == 0:
                            deleted += 1
                        else:
                            errors.append({"file": os.path.basename(filepath), "error": "Shell operation failed"})
                    except Exception:
                        os.remove(filepath)
                        deleted += 1
                else:
                    os.remove(filepath)
                    deleted += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": os.path.basename(filepath), "error": str(e)})

    return {"deleted": deleted, "errors": errors}


# ===================== FILE SHREDDER =====================

def shred_file(filepath, passes=3):
    """
    Securely delete a file by overwriting with random data before deletion.
    Uses multiple passes for security.
    """
    try:
        if not os.path.exists(filepath):
            return {"success": False, "message": "File not found"}

        file_size = os.path.getsize(filepath)
        name = os.path.basename(filepath)

        with open(filepath, "r+b") as f:
            for p in range(passes):
                f.seek(0)
                if p % 3 == 0:
                    data = b'\x00' * min(file_size, 1024 * 1024)
                elif p % 3 == 1:
                    data = b'\xff' * min(file_size, 1024 * 1024)
                else:
                    data = os.urandom(min(file_size, 1024 * 1024))

                written = 0
                while written < file_size:
                    chunk = min(len(data), file_size - written)
                    f.write(data[:chunk])
                    written += chunk
                f.flush()
                os.fsync(f.fileno())

        os.remove(filepath)
        return {"success": True, "message": "Securely shredded: {} ({} passes)".format(name, passes)}

    except (OSError, PermissionError) as e:
        return {"success": False, "message": str(e)}


def shred_files(file_paths, passes=3, progress_callback=None):
    """Shred multiple files with progress reporting."""
    results = {"shredded": 0, "errors": [], "total": len(file_paths)}

    for i, filepath in enumerate(file_paths):
        result = shred_file(filepath, passes)
        if result["success"]:
            results["shredded"] += 1
        else:
            results["errors"].append({"file": os.path.basename(filepath), "error": result["message"]})

        if progress_callback:
            progress_callback((i + 1) / len(file_paths))

    return results

#!/usr/bin/env python3
import os
import json
import time

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build"
}

def format_size(bytes_size: int) -> str:
    for unit in ['B','KB','MB','GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f}TB"

def tree(path, prefix="", summary=None):
    if summary is None:
        summary = {"files": 0, "dirs": 0, "by_extension": {}}

    entries = []
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        print(prefix + " [Permission Denied]")
        return summary

    entries = [e for e in entries if e not in IGNORE_DIRS]

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        connector = "└── " if index == len(entries) - 1 else "├── "
        if os.path.isdir(full_path):
            print(prefix + connector + f"[{entry}]")
            summary["dirs"] += 1
            extension_prefix = "    " if index == len(entries) - 1 else "│   "
            tree(full_path, prefix + extension_prefix, summary)
        else:
            size = os.path.getsize(full_path)
            ext = os.path.splitext(entry)[1] or "<no_ext>"
            summary["files"] += 1
            summary["by_extension"][ext] = summary["by_extension"].get(ext, 0) + 1

            print(prefix + connector + f"{entry}  ({format_size(size)})")

    return summary


def main():
    print("=== ATOM Project Structure Dumper ===")
    path = input("Enter your ATOM project directory path: ").strip()

    if not os.path.isdir(path):
        print("❌ Invalid directory.")
        return

    print("\n--- PROJECT TREE ---\n")
    summary = tree(path)

    print("\n--- SUMMARY ---")
    print(f"Total Directories: {summary['dirs']}")
    print(f"Total Files: {summary['files']}")
    print("\nFiles by Extension:")
    for ext, count in sorted(summary["by_extension"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {ext}: {count}")

    export = input("\nExport structure as JSON? (y/n): ").lower().strip()
    if export == "y":
        export_path = os.path.join(path, "atom_structure.json")
        data = {
            "path": path,
            "generated_at": time.ctime(),
            "summary": summary
        }
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved → {export_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
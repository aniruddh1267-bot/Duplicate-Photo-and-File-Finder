"""
Duplicate Photo and File Finder - DAA Project
Python 3.10+
Finds exact duplicate files using size grouping and SHA-256 hashing.
Includes a naive pairwise baseline for algorithm analysis.
"""

from __future__ import annotations

import hashlib
import os
import threading
import tkinter as tk
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable


CHUNK_SIZE = 1024 * 1024  # Read files in 1 MiB chunks to limit memory use.


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int
    sha256: str


def sha256_file(path: Path) -> str:
    """Return a SHA-256 fingerprint for a file, reading it in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    """Yield files under root, skipping entries that cannot be accessed."""
    for current_root, _, filenames in os.walk(root, onerror=lambda _error: None):
        for filename in filenames:
            path = Path(current_root) / filename
            try:
                if path.is_file():
                    yield path
            except OSError:
                continue


def find_duplicates(root: Path) -> tuple[list[list[FileRecord]], int, int]:
    """
    Find exact duplicates efficiently.
    Returns (duplicate_groups, files_scanned, bytes_read_for_hashing).
    Size is used as a fast filter; SHA-256 confirms matching content.
    """
    by_size: dict[int, list[Path]] = defaultdict(list)
    files_scanned = 0

    for path in iter_files(root):
        try:
            by_size[path.stat().st_size].append(path)
            files_scanned += 1
        except OSError:
            continue

    groups: dict[str, list[FileRecord]] = defaultdict(list)
    bytes_hashed = 0

    for size, paths in by_size.items():
        # A single file of a given size cannot have a duplicate within that size group.
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                record = FileRecord(path=path, size=size, sha256=sha256_file(path))
                groups[f"{size}:{record.sha256}"].append(record)
                bytes_hashed += size
            except (OSError, PermissionError):
                continue

    duplicate_groups = [records for records in groups.values() if len(records) > 1]
    duplicate_groups.sort(key=lambda group: (-group[0].size, str(group[0].path).lower()))
    return duplicate_groups, files_scanned, bytes_hashed


def naive_pairwise_duplicate_count(paths: list[Path]) -> int:
    """
    Baseline algorithm for DAA analysis.
    Compares every pair of files by bytes. O(n^2) pair comparisons in the worst case.
    This is intentionally for small test sets; do not use it on huge folders.
    """
    comparisons = 0
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            comparisons += 1
            try:
                if paths[i].stat().st_size != paths[j].stat().st_size:
                    continue
                if paths[i].read_bytes() == paths[j].read_bytes():
                    pass
            except OSError:
                pass
    return comparisons


class DuplicateFinderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Duplicate Photo & File Finder | DAA Project")
        self.root.geometry("1050x680")
        self.root.minsize(800, 520)
        self.duplicate_groups: list[list[FileRecord]] = []
        self.selected_root: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="Duplicate Photo & File Finder",
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="Design and Analysis of Algorithms project • Exact duplicate detection using SHA-256",
        ).pack(anchor="w", pady=(2, 14))

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 10))
        self.folder_var = tk.StringVar(value="No folder selected")
        ttk.Entry(controls, textvariable=self.folder_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(controls, text="Choose Folder", command=self.choose_folder).pack(side="left", padx=4)
        self.scan_button = ttk.Button(controls, text="Scan for Duplicates", command=self.start_scan)
        self.scan_button.pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="Choose a folder to begin.")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(0, 8))

        columns = ("group", "name", "size", "path")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("group", text="Group")
        self.tree.heading("name", text="File name")
        self.tree.heading("size", text="Size")
        self.tree.heading("path", text="Full path")
        self.tree.column("group", width=70, anchor="center", stretch=False)
        self.tree.column("name", width=180)
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("path", width=560)
        yscroll = ttk.Scrollbar(outer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        table_frame = ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True)
        self.tree.pack(in_=table_frame, side="left", fill="both", expand=True)
        yscroll.pack(in_=table_frame, side="right", fill="y")

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Open Selected File Location", command=self.open_location).pack(side="left")
        ttk.Button(actions, text="Delete Selected (to Recycle Bin not supported)", command=self.delete_selected).pack(side="left", padx=8)
        ttk.Button(actions, text="Export Report", command=self.export_report).pack(side="left")
        ttk.Label(
            outer,
            text="Safety: scan results are informational. Review each file carefully before deleting anything.",
            foreground="#8a4b08",
        ).pack(anchor="w", pady=(10, 0))

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select folder to scan")
        if folder:
            self.selected_root = Path(folder)
            self.folder_var.set(folder)
            self.status_var.set("Ready to scan.")

    def start_scan(self) -> None:
        if not self.selected_root:
            messagebox.showinfo("Choose folder", "Please choose a folder first.")
            return
        self.scan_button.configure(state="disabled")
        self.status_var.set("Scanning files and calculating hashes…")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self) -> None:
        try:
            groups, count, bytes_hashed = find_duplicates(self.selected_root)  # type: ignore[arg-type]
            self.root.after(0, lambda: self._show_results(groups, count, bytes_hashed))
        except Exception as exc:
            self.root.after(0, lambda: self._scan_error(str(exc)))

    def _scan_error(self, error: str) -> None:
        self.scan_button.configure(state="normal")
        self.status_var.set("Scan failed.")
        messagebox.showerror("Scan error", error)

    def _show_results(self, groups: list[list[FileRecord]], count: int, bytes_hashed: int) -> None:
        self.duplicate_groups = groups
        for item in self.tree.get_children():
            self.tree.delete(item)
        for group_number, group in enumerate(groups, start=1):
            for record in group:
                self.tree.insert(
                    "", "end",
                    values=(group_number, record.path.name, format_size(record.size), str(record.path)),
                    tags=(str(record.path),),
                )
        duplicate_files = sum(len(group) - 1 for group in groups)
        reclaimable = sum((len(group) - 1) * group[0].size for group in groups)
        self.status_var.set(
            f"Scanned {count} files • Found {len(groups)} duplicate group(s) • "
            f"{duplicate_files} extra copies • Potential savings: {format_size(reclaimable)} • "
            f"Data hashed: {format_size(bytes_hashed)}"
        )
        self.scan_button.configure(state="normal")
        if not groups:
            messagebox.showinfo("Scan complete", "No exact duplicate files were found.")

    def _selected_path(self) -> Path | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a file", "Select a file row first.")
            return None
        values = self.tree.item(selection[0], "values")
        return Path(values[3])

    def open_location(self) -> None:
        path = self._selected_path()
        if not path:
            return
        try:
            if os.name == "nt":
                os.startfile(path.parent)  # type: ignore[attr-defined]
            elif os.name == "posix":
                import subprocess
                subprocess.Popen(["xdg-open", str(path.parent)])
        except Exception as exc:
            messagebox.showerror("Unable to open location", str(exc))

    def delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select files", "Select one or more rows first.")
            return
        messagebox.showwarning(
            "Deletion disabled for safety",
            "This starter version does not delete files automatically. "
            "Use 'Open Selected File Location' and delete only after checking that the file is truly redundant."
        )

    def export_report(self) -> None:
        if not self.duplicate_groups:
            messagebox.showinfo("No report", "Scan a folder with duplicates before exporting.")
            return
        destination = filedialog.asksaveasfilename(
            title="Save duplicate report",
            defaultextension=".csv",
            filetypes=[("CSV report", "*.csv")],
            initialfile="duplicate_report.csv",
        )
        if not destination:
            return
        import csv
        try:
            with open(destination, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Group", "File name", "Size (bytes)", "SHA-256", "Full path"])
                for group_number, group in enumerate(self.duplicate_groups, start=1):
                    for record in group:
                        writer.writerow([group_number, record.path.name, record.size, record.sha256, str(record.path)])
            messagebox.showinfo("Report exported", f"Saved report to:\n{destination}")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))


def format_size(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista" if os.name == "nt" else "clam")
    except tk.TclError:
        pass
    DuplicateFinderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

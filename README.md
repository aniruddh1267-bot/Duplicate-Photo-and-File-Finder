# Duplicate-Photo-and-File-Finder
DAA Mini Project - Python Duplicate File Finder
A Python 3.10+ desktop application that finds **exact duplicate files** in a selected folder using file size as a quick filter and SHA-256 hashing to compare contents. It includes a Tkinter GUI and CSV report export.

## Features
- Scan a folder and its subfolders.
- Find exact duplicate files of any type, including photos, documents, PDFs, and videos.
- Group duplicates by file size and SHA-256 fingerprint.
- Show duplicate groups, file paths, and potential storage savings.
- Export results to CSV.
- Does not automatically delete files (safe default).

> This version detects exact duplicates, not visually similar photos. A resized or edited image will generally have a different hash.

## Requirements
- Python 3.10 or newer
- Tkinter (usually included with Python on Windows)

No third-party packages are required.

## Run on Windows
1. Install Python 3.10+ from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract this project ZIP.
3. Open the extracted `Duplicate_File_Finder_DAA` folder.
4. Double-click `run_windows.bat`, or open Command Prompt in the folder and run:

```bat
py -3 duplicate_finder\app.py
```

## Run on macOS/Linux

```bash
python3 duplicate_finder/app.py
```

## How to test it
1. Open the `sample_files` folder.
2. Create a small test folder elsewhere.
3. Copy `sample_files/original_demo.txt` twice under different names.
4. Run the app and select that test folder.
5. Click **Scan for Duplicates**. The two matching copies should appear in one group.

## Algorithm
1. Walk through files and record each file's size.
2. Group paths by size. Files with unique sizes cannot be exact duplicates.
3. For each size group with two or more files, calculate SHA-256 in chunks.
4. Group files by `(size, SHA-256)`.
5. Any group with at least two files is reported as a duplicate group.

### Complexity analysis
Let:
- `n` = number of files
- `B` = total bytes read while hashing candidates
- `k` = number of files that share sizes with at least one other file

Expected grouping work is `O(n)` with a hash map, plus `O(B)` to read and hash candidate contents. Extra memory is approximately `O(n)` for file paths and records, excluding buffers. SHA-256 work is proportional to the bytes processed.

The naive pairwise baseline has `n(n-1)/2` pair comparisons, i.e. `O(n^2)` comparisons, and can read file contents repeatedly. The production scanner avoids hashing files whose sizes are unique.

## Project structure

```text
Duplicate_File_Finder_DAA/
├── duplicate_finder/
│   └── app.py
├── tests/
│   └── test_duplicate_finder.py
├── sample_files/
│   └── original_demo.txt
├── run_windows.bat
├── run_mac_linux.sh
├── requirements.txt
└── README.md
```

## Limitations / future improvements
- Exact duplicates only; perceptual image hashing can be added for similar photos.
- Hashing very large files can take time.
- Files that change during scanning may produce inconsistent results.
- Future work: progress bar, cancel scan, recycle-bin integration, image previews, and perceptual-hash photo matching.

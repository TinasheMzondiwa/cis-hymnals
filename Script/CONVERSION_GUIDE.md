# JSON to V2 Format Conversion Guide

This guide explains how to convert hymnal JSON files to the new v2 structure.

## 📋 Overview

Three conversion scripts are available:

1. **`convert_to_v2.py`** - Converts old JSON files (with HTML content) to v2 format
2. **`convert_markdown_to_v2.py`** - Converts markdown JSON files (from New_Files/) to v2 format
3. **`batch_convert_to_v2.py`** - Batch converts all files from New_Files/ directory

## 🔄 Format Differences

### Old Format (HTML)
```json
{
  "title": "1 Watchman Blow The Gospel Trumpet.",
  "number": 1,
  "content": "<h1><b>1 Watchman...</b></h1><p>Verse text...</p>"
}
```

### Markdown Format (New_Files/)
```json
{
  "title": "1 Watchman Blow The Gospel Trumpet.",
  "number": 1,
  "markdown": "### 1 Watchman...\n\nVerse text...\n\n**CHORUS:**\n..."
}
```

### V2 Format (Target)
```json
{
  "index": "001",
  "number": 1,
  "title": "Watchman Blow The Gospel Trumpet.",
  "lyrics": [
    {
      "type": "verse",
      "index": 1,
      "lines": ["Line 1", "Line 2", "Line 3"]
    },
    {
      "type": "refrain",
      "lines": ["Chorus line 1", "Chorus line 2"]
    }
  ],
  "revision": 1
}
```

## 🚀 Usage

### 1. Convert Single HTML File

```bash
python Script/convert_to_v2.py english.json
```

Output: `v2/english_v2.json`

Or specify output path:
```bash
python Script/convert_to_v2.py english.json v2/my_output.json
```

### 2. Convert Single Markdown File

```bash
python Script/convert_markdown_to_v2.py New_Files/english.json
```

Output: `v2/english_v2.json`

Or specify output path:
```bash
python Script/convert_markdown_to_v2.py New_Files/english.json v2/english_v2.json
```

### 3. Batch Convert All New_Files/

```bash
python Script/batch_convert_to_v2.py
```

This will convert all JSON files in `New_Files/` directory to `v2/` directory.

## 📦 Dependencies

Install required packages:

```bash
pip install beautifulsoup4
```

## ✨ Features

- **Automatic title cleaning**: Removes hymn number prefix from title
- **Zero-padded index**: Creates 3-digit index (e.g., "001", "042", "123")
- **Structured lyrics**: Separates verses and refrains with line arrays
- **CHORUS/REFRAIN detection**: Automatically identifies and labels chorus sections
- **HTML parsing**: Cleans HTML tags and extracts plain text
- **Markdown parsing**: Handles markdown formatting from processed files

## 📁 Directory Structure

```
cis-hymnals-main/
├── english.json              # Original HTML format
├── New_Files/
│   └── english.json          # Markdown format (processed)
├── v2/
│   └── english_v2.json       # New v2 format (output)
└── Script/
    ├── convert_to_v2.py
    ├── convert_markdown_to_v2.py
    └── batch_convert_to_v2.py
```

## 🔍 Example Conversion

**Input (HTML):**
```json
{
  "title": "1 Watchman Blow The Gospel Trumpet.",
  "number": 1,
  "content": "<h1><b>1 Watchman...</b></h1><p>Watchman, blow the gospel trumpet,<br/>Every soul a warning give;</p><p><i><b>CHORUS</b><br/>Blow the trumpet, trusty watchman,</i></p>"
}
```

**Output (V2):**
```json
{
  "index": "001",
  "number": 1,
  "title": "Watchman Blow The Gospel Trumpet.",
  "lyrics": [
    {
      "type": "verse",
      "index": 1,
      "lines": [
        "Watchman, blow the gospel trumpet,",
        "Every soul a warning give;"
      ]
    },
    {
      "type": "refrain",
      "lines": [
        "Blow the trumpet, trusty watchman,"
      ]
    }
  ],
  "revision": 1
}
```

## 🛠️ Troubleshooting

- **Missing BeautifulSoup**: Run `pip install beautifulsoup4`
- **File not found**: Ensure you're running from the repository root
- **Encoding errors**: Scripts use UTF-8 encoding by default


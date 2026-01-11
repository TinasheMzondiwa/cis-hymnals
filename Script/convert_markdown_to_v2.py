"""
Convert markdown format (from New_Files/) to v2 structure.
Usage: python convert_markdown_to_v2.py <input_file.json> [output_file.json]
"""

import json
import re
import sys
import os


def extract_title_number(title_str):
    """Extract hymn number and clean title from title string."""
    # Match pattern like "1 Watchman Blow The Gospel Trumpet."
    match = re.match(r'^(\d+)\s+(.+)$', title_str.strip())
    if match:
        number = int(match.group(1))
        clean_title = match.group(2).strip()
        return number, clean_title
    return None, title_str.strip()


def parse_markdown_to_lyrics(markdown_content):
    """Parse markdown content into structured lyrics array."""
    lyrics = []
    verse_index = 0
    refrain_lines = None

    # Remove the title header (### Title)
    markdown_content = re.sub(r'^###\s+.*?\n+', '', markdown_content, flags=re.MULTILINE)

    # Split by double newlines to get sections
    sections_raw = re.split(r'\n\s*\n+', markdown_content.strip())

    # First pass: collect all sections
    sections = []
    for section in sections_raw:
        section = section.strip()
        if not section:
            continue

        # Check if this is a chorus/refrain
        is_refrain = False
        if re.search(r'\*\*\s*(CHORUS|REFRAIN|GUSUBIRAMO|Coro|Côro|Припев|CIINDULULO|Nnyeso)\s*:?\s*\*\*', section, re.IGNORECASE):
            is_refrain = True
            # Remove CHORUS/REFRAIN label
            section = re.sub(r'\*\*\s*(CHORUS|REFRAIN|GUSUBIRAMO|Coro|Côro|Припев|CIINDULULO|Nnyeso)\s*:?\s*\*\*\s*', '', section, flags=re.IGNORECASE)

        # Split into lines and clean
        lines = []
        for line in section.split('\n'):
            line = line.strip()
            # Remove trailing spaces and markdown line breaks
            line = re.sub(r'\s+$', '', line)
            if line:
                lines.append(line)

        if not lines:
            continue

        sections.append({
            'is_refrain': is_refrain,
            'lines': lines
        })

    # Second pass: build lyrics with refrain repetition
    for section in sections:
        if section['is_refrain']:
            # Store the refrain for later repetition
            refrain_lines = section['lines']
            # Add refrain after the previous verse
            if lyrics:  # Only add if there's already a verse
                lyrics.append({
                    "type": "refrain",
                    "lines": refrain_lines
                })
        else:
            # Add verse
            verse_index += 1
            lyrics.append({
                "type": "verse",
                "index": verse_index,
                "lines": section['lines']
            })
            # Add refrain after this verse if we have one
            if refrain_lines and verse_index > 1:
                lyrics.append({
                    "type": "refrain",
                    "lines": refrain_lines
                })

    return lyrics


def convert_hymn_to_v2(hymn):
    """Convert a single hymn from markdown format to v2 format."""
    # Extract number and clean title
    number, clean_title = extract_title_number(hymn.get('title', ''))
    
    # If extraction failed, use the original number field
    if number is None:
        number = hymn.get('number', 0)
    
    # Parse markdown content to structured lyrics
    markdown_content = hymn.get('markdown', hymn.get('content', ''))
    lyrics = parse_markdown_to_lyrics(markdown_content)
    
    # Create v2 structure
    v2_hymn = {
        "index": f"{number:03d}",
        "number": number,
        "title": clean_title,
        "lyrics": lyrics,
        "revision": 1
    }
    
    return v2_hymn


def convert_file_to_v2(input_path, output_path):
    """Convert entire JSON file from markdown format to v2."""
    print(f"Reading from: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        old_hymns = json.load(f)
    
    print(f"Converting {len(old_hymns)} hymns...")
    
    v2_hymns = []
    for hymn in old_hymns:
        v2_hymn = convert_hymn_to_v2(hymn)
        v2_hymns.append(v2_hymn)
    
    print(f"Writing to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(v2_hymns, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Successfully converted {len(v2_hymns)} hymns to v2 format!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_markdown_to_v2.py <input_file.json> [output_file.json]")
        print("Example: python convert_markdown_to_v2.py New_Files/english.json v2/english_v2.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Auto-generate output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"v2/{base_name}_v2.json"
    
    # Ensure v2 directory exists
    os.makedirs('v2', exist_ok=True)
    
    convert_file_to_v2(input_file, output_file)


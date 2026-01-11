"""
Convert old JSON format (with HTML content) to v2 structure.
Usage: python convert_to_v2.py <input_file.json> [output_file.json]
"""

import json
import re
import sys
import os
from bs4 import BeautifulSoup


def extract_title_number(title_str):
    """Extract hymn number and clean title from title string."""
    # Match pattern like "1 Watchman Blow The Gospel Trumpet."
    match = re.match(r'^(\d+)\s+(.+)$', title_str.strip())
    if match:
        number = int(match.group(1))
        clean_title = match.group(2).strip()
        return number, clean_title
    return None, title_str.strip()


def parse_html_to_lyrics(html_content):
    """Parse HTML content into structured lyrics array."""
    soup = BeautifulSoup(html_content, 'html.parser')
    lyrics = []
    verse_index = 0
    refrain_lines = None

    # Remove h1/h3 headers (title)
    for tag in soup.find_all(['h1', 'h3']):
        tag.decompose()

    # First pass: collect all sections
    sections = []
    for p in soup.find_all('p'):
        text = p.get_text(separator='\n').strip()
        if not text:
            continue

        # Check if this is a chorus/refrain
        is_refrain = False
        if re.search(r'\b(CHORUS|REFRAIN)\b', text, re.IGNORECASE):
            is_refrain = True
            # Remove CHORUS/REFRAIN label
            text = re.sub(r'^.*?\b(CHORUS|REFRAIN)\b:?\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]

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
    """Convert a single hymn from old format to v2 format."""
    # Extract number and clean title
    number, clean_title = extract_title_number(hymn.get('title', ''))
    
    # If extraction failed, use the original number field
    if number is None:
        number = hymn.get('number', 0)
    
    # Parse HTML content to structured lyrics
    html_content = hymn.get('content', '')
    lyrics = parse_html_to_lyrics(html_content)
    
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
    """Convert entire JSON file from old format to v2."""
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
        print("Usage: python convert_to_v2.py <input_file.json> [output_file.json]")
        print("Example: python convert_to_v2.py english.json v2/english_v2.json")
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


"""
Batch convert all files from New_Files/ directory to v2 format.
Usage: python batch_convert_to_v2.py
"""

import os
import json
from convert_markdown_to_v2 import convert_file_to_v2


def batch_convert_new_files():
    """Convert all JSON files from New_Files/ to v2/ directory."""
    new_files_dir = "New_Files"
    v2_dir = "v2"
    
    # Ensure v2 directory exists
    os.makedirs(v2_dir, exist_ok=True)
    
    # Get all JSON files from New_Files directory
    if not os.path.exists(new_files_dir):
        print(f"❌ Error: {new_files_dir} directory not found!")
        return
    
    json_files = [f for f in os.listdir(new_files_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"❌ No JSON files found in {new_files_dir}/")
        return
    
    print(f"Found {len(json_files)} JSON files to convert\n")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for json_file in sorted(json_files):
        input_path = os.path.join(new_files_dir, json_file)
        
        # Generate output filename
        base_name = os.path.splitext(json_file)[0]
        output_file = f"{base_name}_v2.json"
        output_path = os.path.join(v2_dir, output_file)
        
        try:
            print(f"\n📄 Converting: {json_file}")
            convert_file_to_v2(input_path, output_path)
            success_count += 1
        except Exception as e:
            print(f"❌ Error converting {json_file}: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"\n✅ Conversion complete!")
    print(f"   Success: {success_count} files")
    if error_count > 0:
        print(f"   Errors:  {error_count} files")
    print(f"\n📁 Output directory: {v2_dir}/")


if __name__ == "__main__":
    print("🔄 Batch Converting New_Files/ to v2 format...")
    print("=" * 60)
    batch_convert_new_files()


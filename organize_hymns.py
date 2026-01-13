import os
import json
import shutil

def main():
    base_dir = '/Users/tinashe/Dev/FaithUnfeigned/cis-hymnals'
    v2_dir = os.path.join(base_dir, 'v2')
    config_path = os.path.join(base_dir, 'config.json')

    # Load config to map keys to languages
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Map key -> Language Name (e.g. 'english' -> 'English', 'sdah' -> 'English')
        key_to_lang = {item['key']: item['language'] for item in config}
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return

    if not os.path.exists(v2_dir):
        print(f"Error: Directory {v2_dir} does not exist.")
        return

    # Get all subdirectories in v2 (which are currently the keys from the previous step)
    # The previous step effectively moved [key]_v2.json -> [key]/hymns.json
    # So now we iterate over [key] directories.
    
    items = os.listdir(v2_dir)
    
    # Pre-calculate moves to avoid issues while iterating and modifying
    moves = []

    for item in items:
        item_path = os.path.join(v2_dir, item)
        
        # We are looking for directories that match our keys
        if os.path.isdir(item_path):
            key = item
            
            # Use language name from config, or fallback to Capitalized Key
            if key in key_to_lang:
                language_name = key_to_lang[key]
            else:
                # Handle cases not in config if any (e.g. if we missed one)
                # Currently Twi and Kirundi were observed not being in grep, 
                # but let's see. If not in config, we can just title case the key.
                print(f"Warning: Key '{key}' not found in config. Using capitalized key as language name.")
                language_name = key.title()

            # Sanitize language name for filesystem (remove slashes, etc.)
            # 'Ndebele/IsiZulu' -> 'Ndebele-IsiZulu' or just keep 'Ndebele' if simple. 
            # Simple replace / with - is usually safe enough.
            language_name = language_name.replace('/', '-')

            # Target Directory: v2/English
            target_lang_dir = os.path.join(v2_dir, language_name)
            
            # Source File: v2/english/hymns.json
            src_file = os.path.join(item_path, 'hymns.json')
            
            # Target File: v2/English/english.json
            # We want to name the file based on the key: [key].json
            dst_file = os.path.join(target_lang_dir, f"{key}.json")
            
            if os.path.exists(src_file):
                moves.append({
                    'src_dir': item_path,
                    'src_file': src_file,
                    'dst_dir': target_lang_dir,
                    'dst_file': dst_file,
                    'key': key
                })
            else:
                print(f"Skipping {key}: 'hymns.json' not found in {item_path}")

    print(f"Planned moves: {len(moves)}")
    
    for move in moves:
        # Create target language directory
        if not os.path.exists(move['dst_dir']):
            os.makedirs(move['dst_dir'])
            print(f"Created: {move['dst_dir']}")
            
        # Move file
        try:
            shutil.move(move['src_file'], move['dst_file'])
            print(f"Moved: {move['src_file']} -> {move['dst_file']}")
            
            # Remove old directory if empty
            # Since we moved the only file 'hymns.json', it should be empty 
            # unless there are hidden files.
            try:
                os.rmdir(move['src_dir'])
                print(f"Removed old dir: {move['src_dir']}")
            except OSError:
                print(f"Note: Could not remove old dir {move['src_dir']} (not empty?)")
                
        except Exception as e:
            print(f"Error moving {move['src_file']}: {e}")

if __name__ == "__main__":
    main()

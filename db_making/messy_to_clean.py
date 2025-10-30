
#!/usr/bin/env python3
'''
Kaomoji Processing Script
Cleans and processes kaomoji data from messy JSON to structured format
'''
import json
import re
import os
from pathlib import Path
import tempfile
import subprocess
import datetime

# Dot art characters from design doc
DOT_ART_CHARS = set("⠀⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿⢀⢁⢂⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿")

# Basic emoji ranges (simplified - would need expansion)
def load_emoji_ranges():
    """Load emoji code points from emoji_data.txt"""
    # Cache the result to avoid reloading
    if hasattr(load_emoji_ranges, '_cached_emoji_points'):
        return load_emoji_ranges._cached_emoji_points
    
    emoji_points = set()
    try:
        with open('emoji_data.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse code point (first field before semicolon)
                code_point_str = line.split(';')[0].strip()
                if code_point_str:
                    # Handle multi-code-point sequences (e.g., "0023 20E3")
                    for cp in code_point_str.split():
                        try:
                            emoji_points.add(int(cp, 16))
                        except ValueError:
                            # Skip invalid code points
                            continue
    except FileNotFoundError:
        print("Warning: emoji_data.txt not found, using fallback ranges")
        return get_fallback_ranges()
    
    # Cache the result
    load_emoji_ranges._cached_emoji_points = emoji_points
    return emoji_points

def get_fallback_ranges():
    """Fallback emoji ranges if emoji_data.txt is not available"""
    return set(range(0x1F600, 0x1F64F + 1)) | set(range(0x1F300, 0x1F5FF + 1)) | \
           set(range(0x1F680, 0x1F6FF + 1)) | set(range(0x1F1E6, 0x1F1FF + 1)) | \
           set(range(0x2600, 0x26FF + 1)) | set(range(0x2700, 0x27BF + 1)) | \
           set(range(0xFE00, 0xFE0F + 1))

def is_dot_art(content):
    """Check if content is primarily dot art characters"""
    if not content:
        return False
    
    dot_count = sum(1 for char in content if char in DOT_ART_CHARS or char.isspace())
    return dot_count / len(content) > 0.7

def has_emoji(content):
    """Check if content contains emoji characters"""
    emoji_points = load_emoji_ranges()
    for char in content:
        code_point = ord(char)
        if code_point in emoji_points:
            return True
    return False

def is_multiline(content):
    """Check if content contains newlines"""
    # Unicode line and paragraph separators
    line_breaks = {
        '\n',        # Line Feed (LF)
        '\r',        # Carriage Return (CR)
        '\u000B',    # Vertical Tab (VT)
        '\u000C',    # Form Feed (FF)
        '\u0085',    # Next Line (NEL)
        '\u2028',    # Line Separator
        '\u2029',    # Paragraph Separator
    }
    return any(break_char in content for break_char in line_breaks)

def clean_content(content):
    """Clean content by normalizing whitespace"""
    # Only normalize invisible/control characters, preserve visible layout
    # Replace invisible Unicode whitespace with visible braille space
    content = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F\u2060\u3000\ufeff]', '⠀', content)
    # Preserve newlines and multiple spaces for layout
    return content

def auto_tag_species(misc_tags):
    """Extract species tags from misc tags"""
    species_keywords = load_keywords('species.txt')
    return [tag for tag in misc_tags if tag.lower() in species_keywords]

def auto_tag_emotion(misc_tags):
    """Extract emotion tags from misc tags"""
    emotion_keywords = load_keywords('emotions.txt')
    return [tag for tag in misc_tags if tag.lower() in emotion_keywords]

def load_keywords(filename):
    """Load keywords from a file, one per line"""
    keywords = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    keywords.add(line.lower())
    except FileNotFoundError:
        print(f"Warning: {filename} not found, using empty keyword set")
    return keywords

def process_kaomoji(kaomoji_id, kaomoji_data):
    """Process a single kaomoji entry"""
    content = kaomoji_data.get('content', '')
    
    # Auto-populate fields
    processed = {
        'content': clean_content(content),
        'species': auto_tag_species(kaomoji_data.get('misc', [])),
        'emotion': auto_tag_emotion(kaomoji_data.get('misc', [])),
        'misc': kaomoji_data.get('misc', []),
        'dotArt': is_dot_art(content),
        'hasEmoji': has_emoji(content),
        'multiLine': is_multiline(content)
    }
    
    # Manual verification
    return manual_verify_kaomoji(kaomoji_id, processed)

def manual_verify_kaomoji(kaomoji_id, kaomoji_data):
    """Open kaomoji in editor for manual verification and editing"""
    editor = os.environ.get('EDITOR', 'vim')
    
    # Add delete field for manual control
    kaomoji_data['delete'] = False
    
    # Create temporary file with a more editable format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write in a format that's easy to edit
        f.write(f"# Kaomoji ID: {kaomoji_id}\n")
        f.write("# Edit the content below, then save and exit\n")
        f.write("# Set 'delete': true to skip this kaomoji\n")
        f.write("# Lines starting with # are comments\n\n")
        
        f.write("CONTENT:\n")
        f.write(kaomoji_data['content'])
        f.write("\n\n")
        
        f.write("SPECIES:\n")
        f.write(json.dumps(kaomoji_data['species'], ensure_ascii=False))
        f.write("\n\n")
        
        f.write("EMOTION:\n")
        f.write(json.dumps(kaomoji_data['emotion'], ensure_ascii=False))
        f.write("\n\n")
        
        f.write("MISC:\n")
        f.write(json.dumps(kaomoji_data['misc'], ensure_ascii=False))
        f.write("\n\n")
        
        f.write("METADATA:\n")
        metadata = {
            'dotArt': kaomoji_data['dotArt'],
            'hasEmoji': kaomoji_data['hasEmoji'],
            'multiLine': kaomoji_data['multiLine'],
            'delete': kaomoji_data['delete']
        }
        f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # Append current species and emotion lists for reference
        f.write("\n\n# Available species (for reference):\n")
        species_list = load_keywords('species.txt')
        f.write('# ' + ', '.join(sorted(species_list)) + '\n')
        
        f.write("\n# Available emotions (for reference):\n")
        emotion_list = load_keywords('emotions.txt')
        f.write('# ' + ', '.join(sorted(emotion_list)) + '\n')
        
        temp_path = f.name
    
    try:
        print(f"\nEditing kaomoji {kaomoji_id}")
        print("Content preview:")
        print("─" * 40)
        preview = kaomoji_data['content']
        if len(preview) > 10000:
            preview = preview[:10000] + "..."
        print(preview)
        print("─" * 40)
        print("Instructions:")
        print("  - Edit fields as needed")
        print("  - Set 'delete': true to skip this kaomoji")
        print("  - Press 's' to skip without editing")
        print("  - Save and exit to continue")
        
        response = input("Press Enter to open in editor, or 's' to skip: ")
        if response.lower() == 's':
            print("Kaomoji skipped.")
            return None
        
        # Open in editor
        subprocess.run([editor, temp_path])
        
        # Check if file still exists and has content
        if not os.path.exists(temp_path):
            print("ERROR: Temporary file was deleted!")
            return manual_verify_kaomoji(kaomoji_id, kaomoji_data)
            
        # Parse the edited file
        with open(temp_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        print(f"DEBUG - File size: {len(file_content)} bytes")
        print(f"DEBUG - First 500 chars:\n{file_content[:500]}\n--- End preview ---")
        
        if not file_content.strip():
            print("ERROR: File is empty!")
            return manual_verify_kaomoji(kaomoji_id, kaomoji_data)
        
        # Extract content and metadata
        sections = {}
        
        # Use regex to extract sections
        import re
        
        # Find section boundaries
        content_start = file_content.find('CONTENT:')
        species_start = file_content.find('SPECIES:')
        emotion_start = file_content.find('EMOTION:')
        misc_start = file_content.find('MISC:')
        metadata_start = file_content.find('METADATA:')
        
        # Extract CONTENT (everything between CONTENT: and SPECIES:)
        if content_start != -1 and species_start != -1:
            sections['CONTENT'] = file_content[content_start + len('CONTENT:'):species_start].strip()
        
        # Extract JSON sections (everything between header and next section)
        section_boundaries = [
            ('SPECIES', species_start, emotion_start if emotion_start != -1 else misc_start if misc_start != -1 else metadata_start if metadata_start != -1 else len(file_content)),
            ('EMOTION', emotion_start, misc_start if misc_start != -1 else metadata_start if metadata_start != -1 else len(file_content)),
            ('MISC', misc_start, metadata_start if metadata_start != -1 else len(file_content)),
            ('METADATA', metadata_start, file_content.find('# Available species') if file_content.find('# Available species') != -1 else len(file_content))
        ]
        
        for section_name, start, end in section_boundaries:
            if start != -1 and end != -1 and start < end:
                content = file_content[start + len(section_name + ':'):end].strip()
                sections[section_name] = content
        
        # Reconstruct the data
        edited_data = kaomoji_data.copy()
        edited_data['content'] = sections.get('CONTENT', '')
        
        # Debug: print what we're trying to parse
        print(f"DEBUG - Parsing sections:")
        for section_name in ['SPECIES', 'EMOTION', 'MISC', 'METADATA']:
            section_content = sections.get(section_name, 'NOT FOUND')
            print(f"  {section_name}: '{section_content}'")
        
        try:
            edited_data['species'] = json.loads(sections.get('SPECIES', '[]'))
            edited_data['emotion'] = json.loads(sections.get('EMOTION', '[]'))
            edited_data['misc'] = json.loads(sections.get('MISC', '[]'))
            edited_data.update(json.loads(sections.get('METADATA', '{}')))
            
            # Update species and emotion files with any new entries
            update_keyword_files(edited_data['species'], edited_data['emotion'])
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Please fix the format and try again...")
            input("Press Enter to reopen editor...")
            subprocess.run([editor, temp_path])
            # Recursively try again
            return manual_verify_kaomoji(kaomoji_id, kaomoji_data)
        
        # Check if marked for deletion
        if edited_data.get('delete', False):
            print("Kaomoji marked for deletion, skipping...")
            return None
        else:
            # Remove delete field before returning
            edited_data.pop('delete', None)
            print("Changes saved. Continue to next kaomoji...")
            return edited_data
        
    finally:
        # Clean up temp file
        os.unlink(temp_path)

def update_keyword_files(species_tags, emotion_tags):
    """Update species.txt and emotions.txt with any new tags"""
    # Load current lists
    current_species = load_keywords('species.txt')
    current_emotions = load_keywords('emotions.txt')
    
    # Find new entries
    new_species = [tag for tag in species_tags if tag.lower() not in current_species]
    new_emotions = [tag for tag in emotion_tags if tag.lower() not in current_emotions]
    
    # Append new entries to files
    if new_species:
        with open('species.txt', 'a', encoding='utf-8') as f:
            for tag in new_species:
                f.write(f"\n{tag}")
        print(f"Added new species to species.txt: {', '.join(new_species)}")
    
    if new_emotions:
        with open('emotions.txt', 'a', encoding='utf-8') as f:
            for tag in new_emotions:
                f.write(f"\n{tag}")
        print(f"Added new emotions to emotions.txt: {', '.join(new_emotions)}")

def main():
    # Process all JSON files in dirty_json directory
    dirty_dir = Path('dirty_json')
    cleaned_dir = Path('../cleaned')
    cleaned_dir.mkdir(exist_ok=True)
    
    if not dirty_dir.exists():
        print("Error: dirty_json directory not found")
        return
    
    json_files = list(dirty_dir.glob('*.json'))
    
    if not json_files:
        print("No JSON files found in dirty_json directory")
        return
    
    # Create timestamped output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = cleaned_dir / f"cleaned_kaomoji_{timestamp}.json"
    
    # Initialize output file with empty dict
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2, ensure_ascii=False)
    
    processed_count = 0
    skipped_count = 0
    
    for json_file in json_files:
        print(f"Processing {json_file.name}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            messy_data = json.load(f)
        
        # Track which kaomojis to remove from this file
        kaomojis_to_remove = []
        
        # Process each kaomoji
        for kaomoji_id, kaomoji_data in messy_data.items():
            processed = process_kaomoji(kaomoji_id, kaomoji_data)
            if processed is not None:
                # Load current output, add kaomoji, and save immediately
                with open(output_path, 'r', encoding='utf-8') as f:
                    cleaned_data = json.load(f)
                cleaned_data[kaomoji_id] = processed
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                processed_count += 1
            else:
                skipped_count += 1
            
            # Mark for removal from dirty file (whether saved or skipped)
            kaomojis_to_remove.append(kaomoji_id)
        
        # Remove processed kaomojis from dirty file
        for kaomoji_id in kaomojis_to_remove:
            messy_data.pop(kaomoji_id, None)
        
        # Save updated dirty file (with processed kaomojis removed)
        if messy_data:  # Only save if there are remaining kaomojis
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(messy_data, f, indent=2, ensure_ascii=False)
        else:
            # Delete empty file
            json_file.unlink()
            print(f"  Deleted empty file: {json_file.name}")
        
        print(f"  Processed {len(kaomojis_to_remove)} kaomojis from {json_file.name}")
    
    print(f"\nSummary:")
    print(f"  Saved: {processed_count} kaomojis")
    print(f"  Skipped: {skipped_count} kaomojis")
    print(f"  Output: {output_path}")

if __name__ == "__main__":
    main()

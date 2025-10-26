
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any
import sys
import argparse
import requests
from urllib.parse import urljoin


def extract_kaomoji_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract kaomoji data from emojicombos.com HTML content.
    
    Args:
        html_content: Raw HTML content from emojicombos.com
        
    Returns:
        List of dictionaries containing kaomoji data
    """
    kaomoji_list = []
    
    # Regex patterns to find kaomoji containers
    combo_pattern = r'<div class="box-module combo-ctn[^>]*data-combo-hash="([^"]*)"[^>]*data-keyphrases="([^"]*)"[^>]*data-combo="([^"]*)"[^>]*>'
    
    # Find all kaomoji containers
    matches = re.findall(combo_pattern, html_content, re.DOTALL)
    
    for combo_hash, keyphrases, content in matches:
        # Clean up the content - remove HTML entities and extra whitespace
        content = re.sub(r'&#x[0-9A-Fa-f]+;', '', content)  # Remove HTML entities
        content = content.strip()
        
        # Parse keyphrases into tags
        tags = [tag.strip() for tag in keyphrases.split(',')]
        
        # Create unique ID by hashing the content
        emoji_id = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        kaomoji_data = {
            "emoji_id": emoji_id,
            "content": content,
            "tags": tags,
            "combo_hash": combo_hash
        }
        
        kaomoji_list.append(kaomoji_data)
    
    return kaomoji_list


def process_html_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Process an HTML file and extract kaomoji data into the messy JSON format.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Dictionary with emoji_id as keys and kaomoji data as values
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    kaomoji_list = extract_kaomoji_from_html(html_content)
    
    # Convert to the desired JSON format
    messy_json = {}
    for kaomoji in kaomoji_list:
        emoji_id = kaomoji["emoji_id"]
        messy_json[emoji_id] = {
            "content": kaomoji["content"],
            "species": [],  # Will be populated later
            "emotion": [],  # Will be populated later
            "misc": kaomoji["tags"],  # All tags go to misc initially
            "dotArt": False,  # Will be determined by regex later
            "hasEmoji": False,  # Will be determined by regex later
            "multiLine": "\n" in kaomoji["content"]  # Check for newlines
        }
    
    return messy_json


def save_messy_json(data: Dict[str, Dict[str, Any]], output_path: str):
    """
    Save the messy JSON data to a file.
    
    Args:
        data: The kaomoji data dictionary
        output_path: Path where to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Download kaomoji from emojicombos.com and convert to JSON')
    parser.add_argument('category', help='Category name (e.g., wolf, cat, happy)')
    args = parser.parse_args()
    
    category = args.category.lower()
    url = f"https://emojicombos.com/{category}"
    
    # Create dirty_json directory if it doesn't exist
    output_dir = Path("dirty_json")
    output_dir.mkdir(exist_ok=True)
    
    # Download HTML content
    print(f"Downloading kaomoji from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        print(f"Error downloading from {url}: {e}")
        sys.exit(1)
    
    # Extract kaomoji data
    kaomoji_list = extract_kaomoji_from_html(html_content)
    
    if not kaomoji_list:
        print("No kaomoji found in the HTML content. The page structure might have changed.")
        sys.exit(1)
    
    # Convert to the desired JSON format
    messy_json = {}
    for kaomoji in kaomoji_list:
        emoji_id = kaomoji["emoji_id"]
        messy_json[emoji_id] = {
            "content": kaomoji["content"],
            "species": [],  # Will be populated later
            "emotion": [],  # Will be populated later
            "misc": kaomoji["tags"],  # All tags go to misc initially
            "dotArt": False,  # Will be determined by regex later
            "hasEmoji": False,  # Will be determined by regex later
            "multiLine": "\n" in kaomoji["content"]  # Check for newlines
        }
    
    # Save to dirty_json directory
    output_file = output_dir / f"{category}_kaomoji_messy.json"
    save_messy_json(messy_json, str(output_file))
    print(f"Extracted {len(messy_json)} kaomoji and saved to {output_file}")


if __name__ == "__main__":
    main()

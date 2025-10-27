
#!/bin/zsh

# Kaomoji search using fzf with priority: species > emotion > misc
# Character prefixes for filtering:
#   [letter] - no restrictions
#   .        - dot art only
#   ,        - single line only
#   :        - has emoji
#   ;        - no emoji

KAMOJI_FILE="cleaned/cleaned_kaomoji_20251026_180515.json"

if [[ ! -f "$KAMOJI_FILE" ]]; then
    echo "Error: Kaomoji file not found at $KAMOJI_FILE"
    exit 1
fi

# Parse JSON and create searchable entries
search_data=$(jq -r 'to_entries[] | 
    [
        .key,
        (.value.species | join(", ")),
        (.value.emotion | join(", ")),
        (.value.misc | join(", ")),
        (.value.dotArt | tostring),
        (.value.hasEmoji | tostring),
        (.value.multiLine | tostring),
        (.value.content | gsub("\n"; "\\n"))
    ] | join("\t")
' "$KAMOJI_FILE")

# Function to determine filter type from first character
get_filter_type() {
    local first_char="${1:0:1}"
    case "$first_char" in
        ".") echo "dot" ;;
        ",") echo "single" ;;
        ":") echo "emoji" ;;
        ";") echo "noemoji" ;;
        *) echo "any" ;;
    esac
}

# Function to apply filters
apply_filters() {
    local filter_type="$1"
    local line="$2"
    
    IFS=$'\t' read -r id species emotion misc dot_art has_emoji multi_line content <<< "$line"
    
    case "$filter_type" in
        "dot")
            [[ "$dot_art" == "true" ]] && echo "$line"
            ;;
        "single")
            [[ "$multi_line" == "false" ]] && echo "$line"
            ;;
        "emoji")
            [[ "$has_emoji" == "true" ]] && echo "$line"
            ;;
        "noemoji")
            [[ "$has_emoji" == "false" ]] && echo "$line"
            ;;
        "any")
            echo "$line"
            ;;
    esac
}

# Main search function
search_kaomoji() {
    local query="$1"
    local filter_type=$(get_filter_type "$query")
    
    # Remove filter character from query if present
    if [[ "$filter_type" != "any" ]]; then
        query="${query:1}"
    fi
    
    echo "$search_data" | while IFS= read -r line; do
        IFS=$'\t' read -r id species emotion misc dot_art has_emoji multi_line content <<< "$line"
        
        # Apply content filter first
        local filtered_line=$(apply_filters "$filter_type" "$line")
        [[ -z "$filtered_line" ]] && continue
        
        # Search with priority: species > emotion > misc
        local match_found=false
        
        # Species match (highest priority)
        if [[ -n "$query" ]] && [[ "$species" == *"$query"* ]]; then
            match_found=true
            priority=1
        # Emotion match (medium priority)
        elif [[ -n "$query" ]] && [[ "$emotion" == *"$query"* ]]; then
            match_found=true
            priority=2
        # Misc match (lowest priority)
        elif [[ -n "$query" ]] && [[ "$misc" == *"$query"* ]]; then
            match_found=true
            priority=3
        # No query - show all
        elif [[ -z "$query" ]]; then
            match_found=true
            priority=0
        fi
        
        if $match_found; then
            # Format for fzf: priority|display_text|full_data
            # Handle empty arrays by showing "-" for missing fields
            local species_display="${species:--}"
            local emotion_display="${emotion:--}"
            local misc_display="${misc:--}"
            local display_text="$species_display | $emotion_display | $misc_display"
            echo "${priority}|${display_text}|${line}"
        fi
    done | sort -t'|' -k1,1n -k2,2 | cut -d'|' -f2-
}

# Preview function for fzf
preview_kaomoji() {
    local selected="$1"
    IFS=$'|' read -r display_text full_data <<< "$selected"
    IFS=$'\t' read -r id species emotion misc dot_art has_emoji multi_line content <<< "$full_data"
    
    # Format preview
    cat << EOF
Content:
$(echo -e "$content")

ID: $id
Species: $species
Emotion: $emotion
Misc: $misc
Dot Art: $dot_art
Has Emoji: $has_emoji
Multi-line: $multi_line
EOF
}

# Main execution
if [[ -z "$1" ]]; then
    # Get absolute path to this script
    SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
    
    # Interactive mode with fzf
    selected=$(search_kaomoji "" | \
        fzf --height=40% --layout=reverse --border \
            --preview="$SCRIPT_PATH --preview {}" \
            --preview-window=right:60%:wrap \
            --bind="change:reload:$SCRIPT_PATH --search {q}" \
            --bind="ctrl-r:reload:$SCRIPT_PATH --search {q}" \
            --delimiter='|')
    
    if [[ -n "$selected" ]]; then
        IFS=$'|' read -r display_text full_data <<< "$selected"
        IFS=$'\t' read -r id species emotion misc dot_art has_emoji multi_line content <<< "$full_data"
        
        # Cross-platform clipboard copy
        local copied=false
        if command -v wl-copy >/dev/null 2>&1; then
            # Wayland
            echo -e "$content" | wl-copy
            copied=true
        elif command -v pbcopy >/dev/null 2>&1; then
            # macOS
            echo -e "$content" | pbcopy
            copied=true
        elif command -v xclip >/dev/null 2>&1; then
            # Linux with xclip
            echo -e "$content" | xclip -selection clipboard
            copied=true
        elif command -v xsel >/dev/null 2>&1; then
            # Linux with xsel
            echo -e "$content" | xsel --clipboard --input
            copied=true
        fi
        
        if $copied; then
            echo "Copied to clipboard!"
        else
            echo -e "$content"
            echo "\n(No clipboard utility found - content printed above)"
        fi
    fi
else
    case "$1" in
        --search)
            search_kaomoji "$2"
            ;;
        --preview)
            preview_kaomoji "$2"
            ;;
        *)
            echo "Usage: $0 [--search query] [--preview data]"
            echo ""
            echo "Filter prefixes:"
            echo "  . - dot art only"
            echo "  , - single line only"  
            echo "  : - has emoji"
            echo "  ; - no emoji"
            echo "  [letter] - no restrictions"
            ;;
    esac
fi

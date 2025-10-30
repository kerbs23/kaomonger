#!/usr/bin/env zsh

search_kaomoji() {
    # Get script directory (handles symlinks)
    
    local script_dir="$(cd "$(dirname "${(%):-%x}")" && pwd -P)"
    
    local source_dir="$script_dir/cleaned"
    local query
    local codeblock=false
    local dotArtFilter
    local hasEmojiFilter
    local multiLineFilter
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                cat << 'EOF'
Usage: search_kaomoji [OPTIONS] [QUERY]

Search and select kaomoji from the JSON files based on the tags.

OPTIONS:
  -h, --help           Show this help message
  -s, --source DIR     Source directory for JSON files (default: ./cleaned)
  -cb, --codeblock     Copy result in markdown codeblock format
  
  FILTERS (default: show all):
  -da, --dotArt        Show only dot art kaomoji
  -nda, --nodotArt     Show only non-dot art kaomoji
  -he, --hasEmoji      Show only kaomoji with emoji
  -nhe, --nohasEmoji   Show only kaomoji without emoji
  -ml, --multiLine     Show only multi-line kaomoji
  -nml, --nomultiLine  Show only single-line kaomoji

QUERY:
  Search term for fzf. Can also be piped via stdin.

EXAMPLES:
  search_kaomoji cat
  search_kaomoji -da --dotArt
  search_kaomoji -s ~/my_kaomoji -he -ml
  echo "happy" | search_kaomoji
EOF
                return 0
                ;;
            -s|--source)
                source_dir="$2"
                shift 2
                ;;
            -cb|--codeblock)
                codeblock=true
                shift
                ;;
            -da|--dotArt)
                dotArtFilter=true
                shift
                ;;
            -nda|--nodotArt)
                dotArtFilter=false
                shift
                ;;
            -he|--hasEmoji)
                hasEmojiFilter=true
                shift
                ;;
            -nhe|--nohasEmoji)
                hasEmojiFilter=false
                shift
                ;;
            -ml|--multiLine)
                multiLineFilter=true
                shift
                ;;
            -nml|--nomultiLine)
                multiLineFilter=false
                shift
                ;;
            -*)
                echo "Unknown option: $1"
                return 1
                ;;
            *)
                query="$1"
                shift
                ;;
        esac
    done
    
    # Read from stdin if no query provided
    if [[ -z "$query" ]] && [ ! -t 0 ]; then
        query=$(cat)
    fi
    
    # Find all JSON files in source directory
    local json_files=("$source_dir"/*.json)
    if [[ ${#json_files[@]} -eq 0 ]]; then
        echo "No JSON files found in $source_dir"
        return 1
    fi
    
    local result
    result=$(jq -r --arg dotArtFilter "$dotArtFilter" --arg hasEmojiFilter "$hasEmojiFilter" --arg multiLineFilter "$multiLineFilter" 'to_entries[] | 
        (if $dotArtFilter != "" then select(.value.dotArt == ($dotArtFilter == "true")) else . end) |
        (if $hasEmojiFilter != "" then select(.value.hasEmoji == ($hasEmojiFilter == "true")) else . end) |
        (if $multiLineFilter != "" then select(.value.multiLine == ($multiLineFilter == "true")) else . end) |
        [.key, 
         ("🐾 " + (.value.species | join(", "))), 
         ("💖 " + (.value.emotion | join(", "))), 
         ("✨ " + (.value.misc    | join(", "))), 
         .value.content] | 
        @tsv' "${json_files[@]}" | \
    fzf --query="$query" \
        --delimiter=$'\t' \
        --with-nth=2,3,4 \
        --preview='echo -e "Content:\n\n{5}\n\n---\nSpecies: \033[1;32m{2}\033[0m\nEmotion: \033[1;33m{3}\033[0m\nMisc: \033[1;36m{4}\033[0m"' | \
        cut -f5)
    
    if [[ -n "$result" ]]; then
        if [[ "$codeblock" == true ]]; then
            echo '```'"\n$result\n"'```' | wl-copy
        else
            echo "$result" | wl-copy
        fi
        echo "Copied to clipboard :3"
    fi

}

# If script is executed directly, run the function
if [[ ${1:-} == "--direct" ]]; then
    ZSH_SCRIPT="$0" search_kaomoji "$@"
elif [[ -z ${ZSH_VERSION:-} ]]; then
    echo "This script must be sourced in zsh or run with --direct" >&2
    exit 1
fi

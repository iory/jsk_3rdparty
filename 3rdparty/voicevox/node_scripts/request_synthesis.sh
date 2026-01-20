#!/bin/bash
# -*- coding:utf-8 -*-
# VOICEVOX text-to-speech using curl (bash version for faster startup)

set -e

VOICEVOX_DEFAULT_SPEAKER_ID="${VOICEVOX_DEFAULT_SPEAKER_ID:-2}"
VOICEVOX_TEXTTOSPEECH_URL="${VOICEVOX_TEXTTOSPEECH_URL:-localhost}"
VOICEVOX_TEXTTOSPEECH_PORT="${VOICEVOX_TEXTTOSPEECH_PORT:-50021}"
CACHE_ENABLED="${ROS_VOICEVOX_TEXTTOSPEECH_CACHE_ENABLED:-true}"
BASE_URL="http://${VOICEVOX_TEXTTOSPEECH_URL}:${VOICEVOX_TEXTTOSPEECH_PORT}"

get_voicevox_cache_dir() {
    local ros_home="${ROS_HOME:-$HOME/.ros}"
    echo "${ros_home}/voicevox"
}

log_message() {
    echo "[Text2Wave][$(date +%s.%N)] $1"
}

get_speakers_from_server() {
    curl -s "${BASE_URL}/speakers" | jq -r '
        [.[] | .name as $name | .styles[] | {key: (.id | tostring), value: ($name + "-" + .name)}]
        | from_entries
    '
}

get_speaker_id_from_name() {
    local speaker_name="$1"
    local speakers_json="$2"

    if [[ "$speaker_name" =~ ^[0-9]+$ ]]; then
        echo "$speaker_name"
        return
    fi

    local speaker_id
    speaker_id=$(echo "$speakers_json" | jq -r --arg name "$speaker_name" '
        to_entries | map(select(.value | startswith($name))) | .[0].key // empty
    ')

    if [[ -n "$speaker_id" ]]; then
        echo "$speaker_id"
    else
        echo "$VOICEVOX_DEFAULT_SPEAKER_ID"
    fi
}

request_synthesis() {
    local text="$1"
    local output_path="$2"
    local speaker_id="$3"

    local encoded_text
    encoded_text=$(printf '%s' "$text" | jq -sRr @uri)

    local audio_query
    audio_query=$(curl -s -X POST \
        "${BASE_URL}/audio_query?text=${encoded_text}&speaker=${speaker_id}")

    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$audio_query" \
        "${BASE_URL}/synthesis?speaker=${speaker_id}" \
        -o "$output_path"
}

usage() {
    echo "Usage: $0 -eval <speaker_name_or_id> -o <output_file> <text_file>"
    exit 1
}

# Parse arguments
evaluate=""
output=""
text_file=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -eval|--evaluate)
            evaluate="$2"
            shift 2
            ;;
        -o|--output)
            output="$2"
            shift 2
            ;;
        *)
            text_file="$1"
            shift
            ;;
    esac
done

if [[ -z "$evaluate" ]] || [[ -z "$output" ]] || [[ -z "$text_file" ]]; then
    usage
fi

# Create cache directory
cache_dir=$(get_voicevox_cache_dir)
mkdir -p "$cache_dir"

# Get speaker_id_to_name from rosparam or server
speakers_json=""
speakers_cache_file="${cache_dir}/speakers.json"

if command -v rosparam &> /dev/null && rosparam get /voicevox/speakers &> /dev/null; then
    log_message "Loading speaker id from rosparam"
    speakers_json=$(rosparam get /voicevox/speakers)
elif [[ -f "$speakers_cache_file" ]]; then
    log_message "Loading speaker id from cache file"
    speakers_json=$(cat "$speakers_cache_file")
else
    log_message "Loading speaker id from voicevox server"
    speakers_json=$(get_speakers_from_server)

    echo "$speakers_json" | jq -r 'to_entries | sort_by(.key | tonumber) | .[] | "[Text2Wave][\(now)] \(.key) : \(.value)"'

    echo "$speakers_json" > "$speakers_cache_file"

    if command -v rosparam &> /dev/null; then
        rosparam set /voicevox/speakers "$speakers_json"
    fi
fi

# Read text from file (first line only)
speech_text=$(head -n 1 "$text_file")

# Get speaker_id
speaker_id="$VOICEVOX_DEFAULT_SPEAKER_ID"
echo "speaker_id = $speaker_id"

speaker_name="${evaluate#\(}"
speaker_name="${speaker_name%\)}"

speaker_id=$(get_speaker_id_from_name "$speaker_name" "$speakers_json")

# Check cache
if [[ "$CACHE_ENABLED" == "true" ]]; then
    text_hash=$(printf '%s' "$speech_text" | md5sum | cut -d' ' -f1)
    cache_filename="${cache_dir}/${text_hash}--${speaker_id}.wav"

    if [[ -f "$cache_filename" ]]; then
        log_message "Using cached file (${cache_filename}) for ${speech_text}"
        cp "$cache_filename" "$output"
        exit 0
    fi
fi

# Synthesize
log_message "speak ${speech_text} with ${speaker_name}(${speaker_id})"
request_synthesis "$speech_text" "$output" "$speaker_id"

# Save to cache
if [[ "$CACHE_ENABLED" == "true" ]]; then
    cp "$output" "$cache_filename"
fi

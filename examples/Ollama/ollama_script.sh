#!/usr/bin/env bash

# Read all stdin into a variable
INPUT_JSON=$(cat)

echo "$INPUT_JSON" >input.json

# Extract fields using jq
PROMPT=$(echo "$INPUT_JSON" | jq -r '.prompt')
SYSTEM=$(echo "$INPUT_JSON" | jq -r '.system')

# Combine system + prompt into a single prompt string
FULL_PROMPT="${SYSTEM}

${PROMPT}"

# Call ollama
ollama run llama3-chatqa "$FULL_PROMPT"

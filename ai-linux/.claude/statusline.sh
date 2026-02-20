#!/usr/bin/env bash
# Custom statusline script for Claude Code
# Displays: {current_dir}({git_branch}) | 🤖 {version} {model}

set -euo pipefail

# Read JSON input from stdin (provided by Claude Code)
json_input=""
if [[ -p /dev/stdin ]]; then
    json_input=$(cat)
fi

# Get Claude CLI version
version=""
if command -v claude >/dev/null 2>&1; then
    version=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || echo "")
fi

# Get model name from JSON input or fallback to settings.json
model_name="sonnet"
if [[ -n "${json_input}" ]] && command -v jq >/dev/null 2>&1; then
    model_name=$(echo "${json_input}" | jq -r '.model.display_name // "sonnet"' 2>/dev/null || echo "sonnet")
else
    # Fallback: read from settings.json
    settings_file="${HOME}/.claude/settings.json"
    if [[ -f "${settings_file}" ]] && command -v jq >/dev/null 2>&1; then
        model_name=$(jq -r '.model // "sonnet"' "${settings_file}" 2>/dev/null || echo "sonnet")
    fi
fi

# Get current directory from JSON or PWD (shortened)
current_dir="${PWD/#$HOME/~}"
if [[ -n "${json_input}" ]] && command -v jq >/dev/null 2>&1; then
    workspace_dir=$(echo "${json_input}" | jq -r '.workspace.current_dir // ""' 2>/dev/null || echo "")
    if [[ -n "${workspace_dir}" ]]; then
        current_dir="${workspace_dir/#$HOME/~}"
    fi
fi

# Get Git branch if in a git repository
git_branch=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null || echo "")
    if [[ -n "${branch}" ]]; then
        # Check for uncommitted changes
        if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
            git_branch="${branch}*"
        else
            git_branch="${branch}"
        fi
    fi
fi

# Build statusline output
# Format: "{current_dir}({git_branch}) | 🤖 {version} {model}"
output=""

# Start with current directory
if [[ -n "${current_dir}" ]]; then
    output="${current_dir}"

    # Add git branch in parentheses if available
    if [[ -n "${git_branch}" ]]; then
        output="${output} (${git_branch})"
    fi
fi

# Add model info
model_info=""
if [[ -n "${version}" ]]; then
    model_info="${version}"
fi
if [[ -n "${model_name}" ]]; then
    if [[ -n "${model_info}" ]]; then
        model_info="${model_info} ${model_name}"
    else
        model_info="${model_name}"
    fi
fi

if [[ -n "${model_info}" ]]; then
    if [[ -n "${output}" ]]; then
        output="${output} | 🤖 ${model_info}"
    else
        output="🤖 ${model_info}"
    fi
fi

echo "${output}"

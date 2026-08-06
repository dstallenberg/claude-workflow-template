#!/usr/bin/env bash
# PostToolUse hook (Write|Edit|NotebookEdit): format the file Claude just edited,
# then run a fast per-file lint and hand any failures back to Claude as context.
#
# Contract:
#   - stdin  : hook JSON (see https://code.claude.com/docs/en/hooks)
#   - stdout : optional {"hookSpecificOutput":{...,"additionalContext":"..."}}
#   - exit   : ALWAYS 0. A missing or broken formatter must never block a session.
#
# Tooling is auto-detected. Anything that isn't installed is silently skipped,
# so this works unchanged in a polyglot repo and in a project with no formatter.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

input="$(cat)"
file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)"
[[ -n "$file" && -f "$file" ]] || exit 0

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Only touch files inside the project, and never inside build output or vendored trees.
case "$file" in
    "$root"/*) ;;
    *) exit 0 ;;
esac
case "$file" in
    */.git/*|*/node_modules/*|*/target/*|*/dist/*|*/build/*|*/vendor/*|*/.venv/*|*/venv/*) exit 0 ;;
esac

# Skip generated/ignored files — formatting them just creates noise.
git -C "$root" check-ignore -q "$file" 2>/dev/null && exit 0

# Resolve a binary, preferring the project's own copy over anything global.
bin() {
    local name="$1"
    if [[ -x "$root/node_modules/.bin/$name" ]]; then
        printf '%s' "$root/node_modules/.bin/$name"
    elif command -v "$name" >/dev/null 2>&1; then
        command -v "$name"
    fi
}

has_config() {
    local pattern
    for pattern in "$@"; do
        compgen -G "$root/$pattern" >/dev/null 2>&1 && return 0
    done
    return 1
}

lint_output=""
lint_tool=""
record_lint() {
    lint_tool="$1"
    lint_output="$2"
}

ext="${file##*.}"

case "$ext" in
    rs)
        rustfmt_bin="$(bin rustfmt)"
        if [[ -n "$rustfmt_bin" ]]; then
            # rustfmt on a bare file defaults to edition 2015 and fails to parse
            # modern syntax, so pass the crate's edition when we can find it.
            edition="$(grep -m1 -E '^[[:space:]]*edition[[:space:]]*=' "$root/Cargo.toml" 2>/dev/null | grep -oE '20[0-9]{2}')"
            rustfmt_args=()
            [[ -n "$edition" ]] && rustfmt_args=(--edition "$edition")
            "$rustfmt_bin" ${rustfmt_args[@]+"${rustfmt_args[@]}"} "$file" >/dev/null 2>&1
        fi
        # No per-file lint: cargo check/clippy are crate-wide and too slow for an
        # edit hook. /dev and /refactor run the build gate before committing.
        ;;
    ts|tsx|js|jsx|mjs|cjs|json|jsonc|css|scss|less|html|vue|svelte|md|mdx|yml|yaml)
        biome_bin="$(bin biome)"
        prettier_bin="$(bin prettier)"
        if [[ -n "$biome_bin" ]] && has_config "biome.json" "biome.jsonc"; then
            "$biome_bin" format --write "$file" >/dev/null 2>&1
        elif [[ -n "$prettier_bin" ]]; then
            # A global prettier with no project config would reformat to its own
            # defaults, so only run it when the project actually opts in.
            if [[ "$prettier_bin" == "$root/node_modules/.bin/prettier" ]] \
                || has_config ".prettierrc*" "prettier.config.*"; then
                "$prettier_bin" --write "$file" >/dev/null 2>&1
            fi
        fi
        case "$ext" in
            ts|tsx|js|jsx|mjs|cjs)
                eslint_bin="$(bin eslint)"
                if [[ -n "$eslint_bin" ]] && has_config "eslint.config.*" ".eslintrc*"; then
                    if ! out="$("$eslint_bin" --format unix "$file" 2>&1)"; then
                        record_lint eslint "$out"
                    fi
                fi
                ;;
        esac
        ;;
    py)
        ruff_bin="$(bin ruff)"
        if [[ -n "$ruff_bin" ]]; then
            "$ruff_bin" format -q "$file" >/dev/null 2>&1
            if ! out="$("$ruff_bin" check --no-cache "$file" 2>&1)"; then
                record_lint ruff "$out"
            fi
        elif command -v black >/dev/null 2>&1; then
            black -q "$file" >/dev/null 2>&1
        fi
        ;;
    go)
        if command -v goimports >/dev/null 2>&1; then
            goimports -w "$file" >/dev/null 2>&1
        elif command -v gofmt >/dev/null 2>&1; then
            gofmt -w "$file" >/dev/null 2>&1
        fi
        if command -v go >/dev/null 2>&1; then
            if ! out="$(go vet "$file" 2>&1)"; then
                record_lint "go vet" "$out"
            fi
        fi
        ;;
    sh|bash)
        command -v shfmt >/dev/null 2>&1 && shfmt -w "$file" >/dev/null 2>&1
        if command -v shellcheck >/dev/null 2>&1; then
            if ! out="$(shellcheck -f gcc "$file" 2>&1)"; then
                record_lint shellcheck "$out"
            fi
        fi
        ;;
esac

if [[ -n "$lint_output" ]]; then
    rel="${file#"$root"/}"
    msg="$lint_tool reported issues in $rel — fix them now, before moving on:"$'\n'"$(printf '%s' "$lint_output" | head -n 30)"
    jq -n --arg ctx "$msg" \
        '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
fi

exit 0

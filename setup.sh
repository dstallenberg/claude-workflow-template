#!/usr/bin/env bash
# Scaffold the Claude milestone workflow into the project in the current directory.
# Non-interactive: the project name defaults to the directory name and the preset
# is detected from the repo. Existing documents are never overwritten.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/template"
PRESETS_DIR="$SCRIPT_DIR/presets"

SKILLS=(dev requirements design refactor refactor-investigation status)

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${CYAN}>${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1" >&2; }

PROJECT_NAME=""
PRESET=""
FORCE=0

usage() {
    cat <<EOF
Claude Workflow Template Setup

Usage: setup.sh [options]     (run from inside the target project)

Options:
  --name NAME      Project name (default: the current directory's name)
  --preset NAME    Preset to inject (default: detected from the repo, else custom)
  --force          Refresh the machinery — skills, hooks, .claude/settings.json.
                   Documents (REQUIREMENTS.md, CLAUDE.md, milestones/) are never
                   touched. Overwritten files are backed up as <file>.bak.
  --list-presets   List available presets and exit
  -h, --help       Show this help

Documents are only created when missing, so re-running is safe.
EOF
}

list_presets() {
    for preset_dir in "$PRESETS_DIR"/*/; do
        [[ -d "$preset_dir" ]] && basename "$preset_dir"
    done
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)   PROJECT_NAME="${2:-}"; shift 2 ;;
        --preset) PRESET="${2:-}"; shift 2 ;;
        --force)  FORCE=1; shift ;;
        --list-presets) list_presets; exit 0 ;;
        -h|--help) usage; exit 0 ;;
        *) err "Unknown option: $1"; echo; usage; exit 1 ;;
    esac
done

# --- Resolve project name and preset ---

if [[ -z "$PROJECT_NAME" ]]; then
    PROJECT_NAME="$(basename "$PWD")"
fi

# Detect the language family, then pick the preset only if exactly one matches.
detect_preset() {
    local family=""
    if [[ -f "Cargo.toml" ]]; then
        family="rust"
    elif [[ -f "package.json" || -f "tsconfig.json" ]]; then
        family="typescript"
    elif [[ -f "pyproject.toml" || -f "setup.py" ]]; then
        family="python"
    elif [[ -f "go.mod" ]]; then
        family="go"
    fi
    [[ -z "$family" ]] && return 0

    local matches=()
    local name
    while read -r name; do
        [[ "$name" == "$family" || "$name" == "$family-"* ]] && matches+=("$name")
    done < <(list_presets)

    if [[ ${#matches[@]} -eq 1 ]]; then
        PRESET="${matches[0]}"
        info "Detected a $family project — using preset '$PRESET'"
    elif [[ ${#matches[@]} -gt 1 ]]; then
        warn "Detected a $family project, but several presets match: ${matches[*]}"
        warn "Continuing without a preset. Re-run with --preset <name> --force to inject one."
    fi
}

if [[ -z "$PRESET" ]]; then
    detect_preset
fi
PRESET="${PRESET:-custom}"

if [[ "$PRESET" != "custom" && ! -d "$PRESETS_DIR/$PRESET" ]]; then
    err "Preset '$PRESET' not found. Available:"
    list_presets | sed 's/^/    /' >&2
    exit 1
fi
PRESET_PATH="$PRESETS_DIR/$PRESET"

echo -e "${BOLD}Claude Workflow Template${NC} — project '$PROJECT_NAME', preset '$PRESET'"
echo ""

# --- Helpers ---

# install_file SRC DST [--exec]
# Returns 0 when the file was written, 1 when it was left alone.
install_file() {
    local src="$1" dst="$2" mode="${3:-}"
    if [[ -e "$dst" ]]; then
        if [[ "$FORCE" -eq 0 ]]; then
            info "Skipping $dst (already exists)"
            return 1
        fi
        # --force always rewrites (so preset injection re-runs); back up only real edits.
        if ! cmp -s "$src" "$dst"; then
            cp "$dst" "$dst.bak"
            warn "Backed up $dst → $dst.bak"
        fi
    fi
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    [[ "$mode" == "--exec" ]] && chmod +x "$dst"
    ok "Wrote $dst"
    return 0
}

# Replace <!-- INJECT:NAME --> in a file with the contents of a preset file.
inject_marker() {
    local target="$1" marker_name="$2" preset_file="$3" tmp
    [[ -f "$preset_file" ]] || return 0
    tmp="$(mktemp)"
    awk -v marker="<!-- INJECT:${marker_name} -->" -v file="$preset_file" '
        index($0, marker) > 0 {
            while ((getline line < file) > 0) print line
            close(file)
            next
        }
        { print }
    ' "$target" > "$tmp" && mv "$tmp" "$target"
}

# Substitute a literal placeholder without relying on GNU sed -i.
replace_placeholder() {
    local target="$1" needle="$2" value="$3" tmp
    tmp="$(mktemp)"
    awk -v needle="$needle" -v value="$value" '
        {
            while ((i = index($0, needle)) > 0) {
                $0 = substr($0, 1, i - 1) value substr($0, i + length(needle))
            }
            print
        }
    ' "$target" > "$tmp" && mv "$tmp" "$target"
}

# Drop any marker line the preset didn't fill in (always the case for `custom`).
strip_markers() {
    local target="$1" tmp
    tmp="$(mktemp)"
    awk '!/^[[:space:]]*<!-- INJECT:[A-Z_]+ -->[[:space:]]*$/' "$target" > "$tmp" && mv "$tmp" "$target"
}

# --- Skills ---

for skill in "${SKILLS[@]}"; do
    target=".claude/skills/${skill}/SKILL.md"
    if install_file "$TEMPLATE_DIR/.claude/skills/${skill}/SKILL.md" "$target"; then
        if [[ "$PRESET" != "custom" ]]; then
            case "$skill" in
                dev)
                    inject_marker "$target" "ROLE" "$PRESET_PATH/dev-role.md"
                    inject_marker "$target" "CODE_STYLE" "$PRESET_PATH/dev-codestyle.md"
                    inject_marker "$target" "IMPLEMENTATION_WIRING" "$PRESET_PATH/dev-wiring.md"
                    inject_marker "$target" "TEST_STYLE" "$PRESET_PATH/dev-teststyle.md"
                    inject_marker "$target" "BUILD_COMMANDS" "$PRESET_PATH/dev-buildcommands.md"
                    ;;
                requirements)
                    inject_marker "$target" "ROLE" "$PRESET_PATH/requirements-role.md"
                    inject_marker "$target" "SOURCE_DIRS" "$PRESET_PATH/requirements-sourcedirs.md"
                    ;;
                design)
                    inject_marker "$target" "DESIGN_ROLE" "$PRESET_PATH/design-role.md"
                    inject_marker "$target" "ANALYSIS_CATEGORIES" "$PRESET_PATH/design-categories.md"
                    inject_marker "$target" "DOMAIN_REFERENCES" "$PRESET_PATH/design-references.md"
                    ;;
                refactor)
                    inject_marker "$target" "CODE_STYLE" "$PRESET_PATH/dev-codestyle.md"
                    inject_marker "$target" "BUILD_COMMANDS" "$PRESET_PATH/dev-buildcommands.md"
                    ;;
                refactor-investigation)
                    inject_marker "$target" "SOURCE_DIRS" "$PRESET_PATH/requirements-sourcedirs.md"
                    ;;
            esac
        fi
        strip_markers "$target"
    fi
done

# --- Hooks ---

install_file "$TEMPLATE_DIR/.claude/hooks/format-edited-file.sh" \
    ".claude/hooks/format-edited-file.sh" --exec || true

# --- Project settings (committed: hooks, worktree base, permissions) ---

settings_src="$TEMPLATE_DIR/.claude/settings.json.template"
merged_settings="$(mktemp)"
cp "$settings_src" "$merged_settings"

preset_perms="$PRESET_PATH/settings-permissions.json"
if [[ "$PRESET" != "custom" && -f "$preset_perms" ]]; then
    if command -v jq >/dev/null 2>&1; then
        tmp="$(mktemp)"
        jq --slurpfile preset "$preset_perms" '
            .permissions.allow = ((.permissions.allow + ($preset[0].permissions.allow // [])) | unique)
        ' "$merged_settings" > "$tmp" && mv "$tmp" "$merged_settings"
    else
        warn "jq not found — preset permissions were not merged into .claude/settings.json"
        warn "Add the entries from $preset_perms by hand, or install jq and re-run with --force."
    fi
fi

install_file "$merged_settings" ".claude/settings.json" || true
rm -f "$merged_settings"

# --- Documents (created once, never refreshed by --force) ---

if [[ ! -f "REQUIREMENTS.md" ]]; then
    cp "$TEMPLATE_DIR/REQUIREMENTS.md.template" "REQUIREMENTS.md"
    replace_placeholder "REQUIREMENTS.md" "PROJECT_NAME" "$PROJECT_NAME"
    ok "Wrote REQUIREMENTS.md"
else
    info "Skipping REQUIREMENTS.md (already exists)"
fi

if [[ ! -f "CLAUDE.md" ]]; then
    cp "$TEMPLATE_DIR/CLAUDE.md.template" "CLAUDE.md"
    replace_placeholder "CLAUDE.md" "PROJECT_NAME" "$PROJECT_NAME"

    sections_file="$PRESET_PATH/claude-sections.md"
    if [[ "$PRESET" != "custom" && -f "$sections_file" ]]; then
        # Section names come from the template's own markers, so adding a marker
        # to CLAUDE.md.template needs no change here.
        while read -r section; do
            section_content="$(awk -v sec="## $section" '
                $0 == sec { found=1; next }
                found && /^## / { found=0 }
                found { print }
            ' "$sections_file")"
            [[ -n "$section_content" ]] || continue
            section_tmp="$(mktemp)"
            printf '%s\n' "$section_content" > "$section_tmp"
            inject_marker "CLAUDE.md" "$section" "$section_tmp"
            rm -f "$section_tmp"
        done < <(grep -oE '<!-- INJECT:[A-Z_]+ -->' "$TEMPLATE_DIR/CLAUDE.md.template" \
            | sed -E 's/<!-- INJECT:([A-Z_]+) -->/\1/' | sort -u)
    fi
    strip_markers "CLAUDE.md"
    ok "Wrote CLAUDE.md (fill in the TODO sections)"
else
    info "Skipping CLAUDE.md (already exists)"
fi

if [[ ! -f "milestones/M-EXAMPLE.md" ]]; then
    mkdir -p milestones
    cp "$TEMPLATE_DIR/milestones/M-EXAMPLE.md" "milestones/M-EXAMPLE.md"
    ok "Wrote milestones/M-EXAMPLE.md (format reference)"
else
    info "Skipping milestones/M-EXAMPLE.md (already exists)"
fi

if [[ ! -f ".worktreeinclude" ]]; then
    cp "$TEMPLATE_DIR/.worktreeinclude.template" ".worktreeinclude"
    ok "Wrote .worktreeinclude (list gitignored files worktrees need)"
else
    info "Skipping .worktreeinclude (already exists)"
fi

# --- .gitignore (append only what's missing) ---

added_ignores=0
while read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    if ! { [[ -f .gitignore ]] && grep -qxF "$line" .gitignore; }; then
        if [[ "$added_ignores" -eq 0 ]]; then
            [[ -f .gitignore && -s .gitignore ]] && printf '\n' >> .gitignore
            printf '# Claude Code\n' >> .gitignore
        fi
        printf '%s\n' "$line" >> .gitignore
        added_ignores=$((added_ignores + 1))
    fi
done < "$TEMPLATE_DIR/gitignore.append"
if [[ "$added_ignores" -gt 0 ]]; then
    ok "Added $added_ignores entr$([[ $added_ignores -eq 1 ]] && echo y || echo ies) to .gitignore"
fi

# --- Legacy layout notice ---

legacy=()
for skill in "${SKILLS[@]}"; do
    [[ -f ".claude/commands/${skill}.md" ]] && legacy+=("$skill")
done
if [[ ${#legacy[@]} -gt 0 ]]; then
    echo ""
    warn "Old-style commands found in .claude/commands/: ${legacy[*]}"
    warn "They shadow the new skills of the same name. Delete them once you've moved"
    warn "any local edits across: rm .claude/commands/{$(IFS=,; echo "${legacy[*]}")}.md"
fi

# --- Done ---

echo ""
echo -e "${BOLD}Setup complete.${NC}"
echo ""
echo "Next steps:"
echo "  1. Fill in CLAUDE.md — Architecture, Project Structure, Build & Run"
echo "  2. Fill in REQUIREMENTS.md — vision and the milestone index table"
echo "  3. Create your first milestone: milestones/M-FIRST.md (see M-EXAMPLE.md)"
echo "  4. Start a session: claude          (docs work: /requirements, /design)"
echo "     Or isolated:     claude -w M-FIRST-1   (code work: /dev, /refactor)"
echo "  5. /status any time for milestone progress and in-flight worktrees"

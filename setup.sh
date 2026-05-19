#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/template"
PRESETS_DIR="$SCRIPT_DIR/presets"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}>${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
err()   { echo -e "${RED}✗${NC} $1" >&2; }

# --- Gather input ---

echo -e "${BOLD}Claude Workflow Template Setup${NC}"
echo ""

read -rp "Project name: " PROJECT_NAME
if [[ -z "$PROJECT_NAME" ]]; then
    err "Project name is required"
    exit 1
fi

read -rp "Brief description: " PROJECT_DESC

# List available presets
echo ""
info "Available presets:"
for preset_dir in "$PRESETS_DIR"/*/; do
    preset_name="$(basename "$preset_dir")"
    echo "  - $preset_name"
done
echo "  - custom (no preset, fill in manually)"
read -rp "Preset [custom]: " PRESET
PRESET="${PRESET:-custom}"

if [[ "$PRESET" != "custom" ]] && [[ ! -d "$PRESETS_DIR/$PRESET" ]]; then
    err "Preset '$PRESET' not found in $PRESETS_DIR/"
    exit 1
fi

# --- Helper: inject preset content into a file ---
# Replaces <!-- INJECT:NAME --> with contents of preset file
inject_preset() {
    local target_file="$1"
    local marker_name="$2"
    local preset_file="$3"

    if [[ -f "$preset_file" ]]; then
        # Use awk to replace the marker line with file contents
        local content
        content="$(cat "$preset_file")"
        # Escape for sed replacement
        local escaped_content
        escaped_content="$(echo "$content" | sed 's/[&/\]/\\&/g' | sed ':a;N;$!ba;s/\n/\\n/g')"
        sed -i "s|<!-- INJECT:${marker_name} -->|${escaped_content}|g" "$target_file"
    fi
}

# More robust injection using awk (handles multiline better)
inject_preset_awk() {
    local target_file="$1"
    local marker_name="$2"
    local preset_file="$3"

    if [[ -f "$preset_file" ]]; then
        awk -v marker="<!-- INJECT:${marker_name} -->" -v file="$preset_file" '
        {
            if (index($0, marker) > 0) {
                while ((getline line < file) > 0) print line
                close(file)
            } else {
                print
            }
        }' "$target_file" > "${target_file}.tmp" && mv "${target_file}.tmp" "$target_file"
    fi
}

# --- Create directory structure ---

echo ""

if [[ ! -d ".claude/commands" ]]; then
    mkdir -p .claude/commands
    ok "Created .claude/commands/"
else
    info ".claude/commands/ already exists"
fi

if [[ ! -d "milestones" ]]; then
    mkdir -p milestones
    ok "Created milestones/"
else
    info "milestones/ already exists"
fi

# --- Copy skill files ---

for skill in dev requirements design refactor refactor-investigation; do
    target=".claude/commands/${skill}.md"
    if [[ -f "$target" ]]; then
        info "Skipping $target (already exists)"
        continue
    fi
    cp "$TEMPLATE_DIR/.claude/commands/${skill}.md" "$target"

    # Inject preset content if not custom
    if [[ "$PRESET" != "custom" ]]; then
        PRESET_PATH="$PRESETS_DIR/$PRESET"

        case "$skill" in
            dev)
                inject_preset_awk "$target" "ROLE" "$PRESET_PATH/dev-role.md"
                inject_preset_awk "$target" "CODE_STYLE" "$PRESET_PATH/dev-codestyle.md"
                inject_preset_awk "$target" "IMPLEMENTATION_WIRING" "$PRESET_PATH/dev-wiring.md"
                inject_preset_awk "$target" "TEST_STYLE" "$PRESET_PATH/dev-teststyle.md"
                inject_preset_awk "$target" "BUILD_COMMANDS" "$PRESET_PATH/dev-buildcommands.md"
                ;;
            requirements)
                inject_preset_awk "$target" "ROLE" "$PRESET_PATH/requirements-role.md"
                inject_preset_awk "$target" "SOURCE_DIRS" "$PRESET_PATH/requirements-sourcedirs.md"
                ;;
            design)
                inject_preset_awk "$target" "DESIGN_ROLE" "$PRESET_PATH/design-role.md"
                inject_preset_awk "$target" "ANALYSIS_CATEGORIES" "$PRESET_PATH/design-categories.md"
                inject_preset_awk "$target" "DOMAIN_REFERENCES" "$PRESET_PATH/design-references.md"
                ;;
            refactor)
                inject_preset_awk "$target" "CODE_STYLE" "$PRESET_PATH/dev-codestyle.md"
                inject_preset_awk "$target" "BUILD_COMMANDS" "$PRESET_PATH/dev-buildcommands.md"
                ;;
            refactor-investigation)
                inject_preset_awk "$target" "SOURCE_DIRS" "$PRESET_PATH/requirements-sourcedirs.md"
                ;;
        esac
    fi

    ok "Created $target"
done

# --- Copy document templates ---

if [[ ! -f "REQUIREMENTS.md" ]]; then
    cp "$TEMPLATE_DIR/REQUIREMENTS.md.template" "REQUIREMENTS.md"
    # Replace placeholders
    sed -i "s/PROJECT_NAME/$PROJECT_NAME/g" "REQUIREMENTS.md"
    ok "Created REQUIREMENTS.md"
else
    info "Skipping REQUIREMENTS.md (already exists)"
fi

if [[ ! -f "CLAUDE.md" ]]; then
    cp "$TEMPLATE_DIR/CLAUDE.md.template" "CLAUDE.md"
    sed -i "s/PROJECT_NAME/$PROJECT_NAME/g" "CLAUDE.md"

    # Inject CLAUDE.md preset sections
    if [[ "$PRESET" != "custom" ]]; then
        PRESET_PATH="$PRESETS_DIR/$PRESET"
        SECTIONS_FILE="$PRESET_PATH/claude-sections.md"

        if [[ -f "$SECTIONS_FILE" ]]; then
            # Extract named sections from the preset file and inject them
            for section in CONVENTIONS CODE_STANDARDS ERROR_HANDLING TESTING DEPENDENCY_PHILOSOPHY LOGGING; do
                # Extract content between ## SECTION and next ## or EOF
                section_content="$(awk -v sec="## $section" '
                    $0 == sec { found=1; next }
                    found && /^## / { found=0 }
                    found { print }
                ' "$SECTIONS_FILE")"

                if [[ -n "$section_content" ]]; then
                    # Write to temp file for awk injection
                    echo "$section_content" > "/tmp/inject_${section}.tmp"
                    inject_preset_awk "CLAUDE.md" "$section" "/tmp/inject_${section}.tmp"
                    rm -f "/tmp/inject_${section}.tmp"
                fi
            done
        fi
    fi

    ok "Created CLAUDE.md (fill in TODO sections)"
else
    info "Skipping CLAUDE.md (already exists)"
fi

if [[ ! -f "milestones/M-EXAMPLE.md" ]]; then
    cp "$TEMPLATE_DIR/milestones/M-EXAMPLE.md" "milestones/M-EXAMPLE.md"
    ok "Created milestones/M-EXAMPLE.md (format reference)"
else
    info "Skipping milestones/M-EXAMPLE.md (already exists)"
fi

# --- Copy settings template ---

if [[ ! -f ".claude/settings.local.json" ]]; then
    if [[ "$PRESET" != "custom" ]] && [[ -f "$PRESETS_DIR/$PRESET/settings-permissions.json" ]]; then
        cp "$PRESETS_DIR/$PRESET/settings-permissions.json" ".claude/settings.local.json"
    else
        echo '{ "permissions": { "allow": ["Bash(git:*)"] } }' > ".claude/settings.local.json"
    fi
    ok "Created .claude/settings.local.json"
else
    info "Skipping .claude/settings.local.json (already exists)"
fi

# --- Done ---

echo ""
echo -e "${BOLD}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit REQUIREMENTS.md — add your vision and first milestones"
echo "  2. Edit CLAUDE.md — fill in Architecture, Project Structure, Build & Run"
echo "  3. Create your first milestone: milestones/M-FIRST.md (see M-EXAMPLE.md for format)"
echo "  4. Run /requirements to flesh out your first milestone"
echo "  5. Run /dev to implement the first subtask"

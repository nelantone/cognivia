#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
cd "$REPO_ROOT"

CANONICAL_SKILLS='task-brief architecture-audit safe-refactor docs-update commit-review session-handoff'
CXP_SKILL='cxp'
SUPPORTED_SKILLS="$CANONICAL_SKILLS $CXP_SKILL"
failure_count=0
check_count=0

record_failure() {
    check_count=$((check_count + 1))
    failure_count=$((failure_count + 1))
    printf '  FAIL: %s\n' "$1"
}

record_check() {
    check_count=$((check_count + 1))
}

category_result() {
    category_name=$1
    category_start=$2
    if [ "$failure_count" -eq "$category_start" ]; then
        printf 'PASS  %s\n' "$category_name"
    else
        printf 'FAIL  %s\n' "$category_name"
    fi
}

require_file() {
    path=$1
    record_check
    if [ ! -f "$path" ]; then
        record_failure "required file is missing: $path"
    fi
}

require_dir() {
    path=$1
    record_check
    if [ ! -d "$path" ]; then
        record_failure "required directory is missing: $path"
    fi
}

require_executable() {
    path=$1
    record_check
    if [ ! -x "$path" ]; then
        record_failure "script is not executable: $path"
    fi
}

require_contains() {
    path=$1
    pattern=$2
    description=$3
    record_check
    if ! grep -Eq -- "$pattern" "$path"; then
        record_failure "$description: $path"
    fi
}

require_absent() {
    path=$1
    pattern=$2
    description=$3
    record_check
    if grep -Eq -- "$pattern" "$path"; then
        record_failure "$description: $path"
    fi
}

frontmatter_value() {
    metadata_path=$1
    metadata_key=$2
    sed -n "2,/^---$/s/^${metadata_key}:[[:space:]]*[\"']\{0,1\}\([^\"']*\)[\"']\{0,1\}[[:space:]]*$/\\1/p" "$metadata_path" | head -n 1
}

validate_skill_frontmatter() {
    skill_path=$1
    record_check
    first_line=$(sed -n '1p' "$skill_path")
    if [ "$first_line" != '---' ]; then
        record_failure "skill frontmatter opening delimiter is missing: $skill_path"
        return 1
    fi

    closing_line=$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "$skill_path")
    if [ -z "$closing_line" ]; then
        record_failure "skill frontmatter closing delimiter is missing: $skill_path"
        return 1
    fi

    body_line=$(awk 'NR > 1 && /^#{1,6}[[:space:]]/ { print NR; exit }' "$skill_path")
    if [ -n "$body_line" ] && [ "$body_line" -lt "$closing_line" ]; then
        record_failure "Markdown body begins before skill frontmatter closes: $skill_path"
        return 1
    fi

    if [ "$closing_line" -eq 2 ]; then
        record_failure "skill frontmatter is empty: $skill_path"
        return 1
    fi

    frontmatter_content=$(sed -n "2,$((closing_line - 1))p" "$skill_path")
    if ! printf '%s\n' "$frontmatter_content" | grep -Eq '[^[:space:]]'; then
        record_failure "skill frontmatter is empty: $skill_path"
        return 1
    fi

    return 0
}

extract_body() {
    source_path=$1
    output_path=$2
    awk '
        NR == 1 && $0 == "---" { in_frontmatter = 1; next }
        in_frontmatter && $0 == "---" { in_frontmatter = 0; next }
        !in_frontmatter { print }
    ' "$source_path" > "$output_path"
}

extract_section() {
    source_path=$1
    section_name=$2
    output_path=$3
    awk -v heading="## $section_name" '
        $0 == heading { in_section = 1; next }
        in_section && /^## / { exit }
        in_section && NF { print }
    ' "$source_path" > "$output_path"
}

is_expected_name() {
    candidate=$1
    expected_names=$2
    for expected_name in $expected_names; do
        if [ "$candidate" = "$expected_name" ]; then
            return 0
        fi
    done
    return 1
}

printf '%s\n' 'Cognivia agent-tooling validator'
printf '%s\n' 'Local, deterministic, dependency-free, and network-free.'

category_start=$failure_count
for required_path in \
    .gitignore \
    AGENTS.md \
    CLAUDE.md \
    docs/agents/README.md \
    docs/agents/SKILL_MIGRATION.md \
    docs/agents/VALIDATION.md \
    docs/agent-prompts/sentinel-review.md \
    scripts/agent/sentinel.sh \
    scripts/agent/test-agent-tooling.sh \
    scripts/agent/validate-agent-tooling.sh \
    scripts/sentinel.sh; do
    require_file "$required_path"
done
for required_dir_path in .agents/skills .claude/skills scripts/agent docs/agents; do
    require_dir "$required_dir_path"
done
for skill_name in $SUPPORTED_SKILLS; do
    require_file ".agents/skills/$skill_name/SKILL.md"
    require_file ".agents/skills/$skill_name/agents/openai.yaml"
done
for skill_name in $CANONICAL_SKILLS; do
    record_check
    expected_target="../../.agents/skills/$skill_name"
    if [ ! -L ".claude/skills/$skill_name" ]; then
        record_failure "Claude canonical adapter is not a symlink: .claude/skills/$skill_name"
    elif [ "$(readlink ".claude/skills/$skill_name")" != "$expected_target" ]; then
        record_failure "Claude canonical adapter has the wrong target: .claude/skills/$skill_name"
    elif [ ! -f ".claude/skills/$skill_name/SKILL.md" ]; then
        record_failure "Claude canonical adapter target does not resolve: .claude/skills/$skill_name"
    fi
done
require_file ".claude/skills/$CXP_SKILL/SKILL.md"
category_result 'expected paths and adapters' "$category_start"

category_start=$failure_count
skill_names_file=$(mktemp "${TMPDIR:-/tmp}/cognivia-skill-names.XXXXXX") || exit 1
claude_skill_names_file=$(mktemp "${TMPDIR:-/tmp}/cognivia-claude-skill-names.XXXXXX") || exit 1
trap 'rm -f "$skill_names_file" "$claude_skill_names_file"; if [ -n "${validator_tmpdir:-}" ]; then rm -rf "$validator_tmpdir"; fi' EXIT HUP INT TERM
record_check
agent_skill_entry_count=$(find .agents/skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
if [ "$agent_skill_entry_count" -ne 7 ]; then
    record_failure "unexpected number of supported skill directories: $agent_skill_entry_count"
fi
for discovered_path in .agents/skills/*; do
    discovered_name=$(basename -- "$discovered_path")
    record_check
    if ! is_expected_name "$discovered_name" "$SUPPORTED_SKILLS"; then
        record_failure "unexpected skill directory: $discovered_path"
    fi
done
record_check
claude_skill_entry_count=$(find .claude/skills -mindepth 1 -maxdepth 1 -print | wc -l | tr -d ' ')
if [ "$claude_skill_entry_count" -ne 7 ]; then
    record_failure "unexpected number of Claude skill adapters: $claude_skill_entry_count"
fi
for discovered_path in .claude/skills/*; do
    discovered_name=$(basename -- "$discovered_path")
    record_check
    if ! is_expected_name "$discovered_name" "$SUPPORTED_SKILLS"; then
        record_failure "unexpected Claude skill adapter: $discovered_path"
    fi
done
for skill_name in $SUPPORTED_SKILLS; do
    skill_path=".agents/skills/$skill_name/SKILL.md"
    metadata_path=".agents/skills/$skill_name/agents/openai.yaml"
    if validate_skill_frontmatter "$skill_path"; then
        actual_name=$(frontmatter_value "$skill_path" name)
        description=$(frontmatter_value "$skill_path" description)
        record_check
        if [ "$actual_name" != "$skill_name" ]; then
            record_failure "skill name does not match its directory: $skill_path"
        fi
        record_check
        if [ -z "$description" ]; then
            record_failure "skill description is missing: $skill_path"
        fi
        printf '%s\n' "$actual_name" >> "$skill_names_file"
    fi
    claude_skill_path=".claude/skills/$skill_name/SKILL.md"
    if validate_skill_frontmatter "$claude_skill_path"; then
        claude_actual_name=$(frontmatter_value "$claude_skill_path" name)
        printf '%s\n' "$claude_actual_name" >> "$claude_skill_names_file"
        record_check
        if [ "$claude_actual_name" != "$skill_name" ]; then
            record_failure "Claude skill name does not match its adapter directory: .claude/skills/$skill_name"
        fi
    fi
    require_contains "$metadata_path" '^interface:[[:space:]]*$' 'Codex interface metadata is missing'
    require_contains "$metadata_path" '^  display_name:[[:space:]]+"[^"]+"[[:space:]]*$' 'Codex display_name metadata is invalid'
    require_contains "$metadata_path" '^  short_description:[[:space:]]+"[^"]+"[[:space:]]*$' 'Codex short_description metadata is invalid'
    require_contains "$metadata_path" '^  default_prompt:[[:space:]]+"[^"]+"[[:space:]]*$' 'Codex default_prompt metadata is invalid'
    if [ "$skill_name" = "$CXP_SKILL" ]; then
        require_contains "$metadata_path" '^policy:[[:space:]]*$' 'CXP Codex invocation policy is missing'
        require_contains "$metadata_path" '^  allow_implicit_invocation:[[:space:]]+false[[:space:]]*$' 'CXP must remain explicit-only in Codex'
    fi
done
require_contains ".claude/skills/$CXP_SKILL/SKILL.md" '^disable-model-invocation:[[:space:]]+true[[:space:]]*$' 'CXP must remain explicit-only in Claude'
require_contains ".claude/skills/$CXP_SKILL/SKILL.md" "^@\.\./\.\./\.\./\.agents/skills/$CXP_SKILL/SKILL\.md[[:space:]]*$" 'Claude CXP adapter does not import the project skill'
record_check
duplicate_names=$(sort "$skill_names_file" | uniq -d)
if [ -n "$duplicate_names" ]; then
    for duplicate_name in $duplicate_names; do
        record_failure "duplicate skill name: $duplicate_name"
    done
fi
record_check
duplicate_claude_names=$(sort "$claude_skill_names_file" | uniq -d)
if [ -n "$duplicate_claude_names" ]; then
    for duplicate_name in $duplicate_claude_names; do
        record_failure "duplicate Claude skill name: $duplicate_name"
    done
fi
category_result 'skill names and metadata' "$category_start"

category_start=$failure_count
for skill_name in $CANONICAL_SKILLS; do
    skill_path=".agents/skills/$skill_name/SKILL.md"
    for required_section in Purpose Trigger 'Do not trigger' Inputs Outputs Safety Validation References; do
        require_contains "$skill_path" "^## $required_section[[:space:]]*$" "canonical skill section '$required_section' is missing"
    done
    record_check
    ownership_rows=$(awk -v skill="$skill_name" '
        $0 == "## Canonical ownership" { in_ownership = 1; next }
        in_ownership && /^## / { in_ownership = 0 }
        in_ownership && index($0, "| `" skill "` |") == 1 { count++ }
        END { print count + 0 }
    ' docs/agents/SKILL_MIGRATION.md)
    if [ "$ownership_rows" -ne 1 ]; then
        record_failure "canonical ownership is not unique in SKILL_MIGRATION.md: $skill_name"
    fi
done
cxp_path=".agents/skills/$CXP_SKILL/SKILL.md"
for required_section in Purpose Trigger 'Do not trigger' Inputs 'Prompt contract' Routing Workflow Outputs Safety Validation References; do
    require_contains "$cxp_path" "^## $required_section[[:space:]]*$" "CXP section '$required_section' is missing"
done
require_contains "$cxp_path" '^ChatGPT/Codex:$' 'CXP prompt header is missing ChatGPT/Codex'
require_contains "$cxp_path" '^recommended:$' 'CXP prompt header is missing recommended'
require_contains "$cxp_path" '^minimum:$' 'CXP prompt header is missing minimum'
require_contains "$cxp_path" '^reasoning recommended:$' 'CXP prompt header is missing reasoning recommended'
require_contains "$cxp_path" '^reasoning minimum:$' 'CXP prompt header is missing reasoning minimum'
require_contains "$cxp_path" '\.cxp/CXP_HANDOFF\.md' 'CXP handoff path is missing'
require_contains .gitignore '^\.cxp/$' 'CXP handoff directory is not ignored'
record_check
cxp_ownership_rows=$(awk '
    $0 == "## Canonical ownership" { in_ownership = 1; next }
    in_ownership && /^## / { in_ownership = 0 }
    in_ownership && index($0, "| `cxp` |") == 1 { count++ }
    END { print count + 0 }
' docs/agents/SKILL_MIGRATION.md)
if [ "$cxp_ownership_rows" -ne 0 ]; then
    record_failure 'CXP must not own a canonical responsibility in SKILL_MIGRATION.md'
fi
category_result 'required sections and canonical ownership' "$category_start"

category_start=$failure_count
validator_tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/cognivia-agent-validator.XXXXXX") || exit 1
skill_index=0
for skill_name in $SUPPORTED_SKILLS; do
    skill_index=$((skill_index + 1))
    extract_body ".agents/skills/$skill_name/SKILL.md" "$validator_tmpdir/body-$skill_index"
done
left_index=1
for left_name in $SUPPORTED_SKILLS; do
    right_index=1
    for right_name in $SUPPORTED_SKILLS; do
        if [ "$right_index" -gt "$left_index" ]; then
            record_check
            if cmp -s "$validator_tmpdir/body-$left_index" "$validator_tmpdir/body-$right_index"; then
                record_failure "duplicated project skill body: $left_name and $right_name"
            fi
        fi
        right_index=$((right_index + 1))
    done
    left_index=$((left_index + 1))
done
section_manifest="$validator_tmpdir/sections"
: > "$section_manifest"
section_index=0
for skill_name in $SUPPORTED_SKILLS; do
    for section_name in Purpose Trigger 'Do not trigger' Inputs Workflow Routing Outputs Safety Validation; do
        section_index=$((section_index + 1))
        section_path="$validator_tmpdir/section-$section_index"
        extract_section ".agents/skills/$skill_name/SKILL.md" "$section_name" "$section_path"
        if [ -s "$section_path" ]; then
            section_sum=$(cksum "$section_path" | awk '{ print $1 ":" $2 }')
            printf '%s|%s|%s\n' "$section_sum" "$skill_name" "$section_name" >> "$section_manifest"
        fi
    done
done
record_check
duplicate_section_sums=$(cut -d '|' -f 1 "$section_manifest" | sort | uniq -d)
if [ -n "$duplicate_section_sums" ]; then
    for duplicate_sum in $duplicate_section_sums; do
        duplicate_labels=$(awk -F '|' -v sum="$duplicate_sum" '$1 == sum { printf "%s%s:%s", separator, $2, $3; separator = ", " }' "$section_manifest")
        record_failure "duplicated procedural section: $duplicate_labels"
    done
fi
category_result 'canonical body and procedural duplication' "$category_start"

category_start=$failure_count
require_contains AGENTS.md '^## Agent-tooling ownership[[:space:]]*$' 'AGENTS agent-tooling ownership section is missing'
require_contains AGENTS.md '^## Skill usage[[:space:]]*$' 'AGENTS skill usage section is missing'
require_contains AGENTS.md 'scripts/agent/sentinel\.sh' 'AGENTS does not reference the canonical Sentinel'
require_contains AGENTS.md 'scripts/agent/validate-agent-tooling\.sh' 'AGENTS does not reference the tooling validator'
require_absent AGENTS.md 'planned home for deterministic local gates|names are planned, not yet implemented|Until the skill-migration phase' 'AGENTS contains obsolete migration language'
require_contains CLAUDE.md '^@AGENTS\.md[[:space:]]*$' 'CLAUDE does not import AGENTS.md'
record_check
if [ "$(grep -c '^@AGENTS\.md[[:space:]]*$' CLAUDE.md)" -ne 1 ]; then
    record_failure 'CLAUDE must import AGENTS.md exactly once'
fi
require_contains CLAUDE.md '`\.claude/skills/`' 'CLAUDE does not describe its skill adapter path'
require_contains AGENTS.md '`cxp`.*explicit-only orchestration utility' 'AGENTS does not describe CXP as explicit-only orchestration'
require_contains CLAUDE.md 'explicit-only adapter' 'CLAUDE does not describe the explicit-only CXP adapter'
require_contains docs/agents/README.md '`\.agents/skills/cxp/`' 'README does not list the CXP skill path'
require_contains docs/agents/SKILL_MIGRATION.md 'restored after ownership was correctly reassessed' 'migration map does not record CXP recovery'
require_absent CLAUDE.md 'skill-migration phase|evaluated later|Do not duplicate canonical skill bodies under `\.claude/skills/` in the meantime' 'CLAUDE contains obsolete migration language'
for durable_heading in 'Project purpose' 'Repository boundaries' 'Security and provider safety' 'Git safety' 'Validation ladder'; do
    require_absent CLAUDE.md "^## $durable_heading[[:space:]]*$" "CLAUDE duplicates the AGENTS '$durable_heading' section"
done
require_contains docs/agents/README.md 'Phase 3' 'README does not record Phase 3'
require_contains docs/agents/README.md '`scripts/agent/sentinel\.sh`' 'README does not reference the canonical Sentinel'
require_contains docs/agents/README.md '`scripts/agent/validate-agent-tooling\.sh`' 'README does not reference the tooling validator'
require_absent docs/agents/README.md 'Planned home for deterministic local checks|Claude-specific skill-discovery adapters are not implemented|migration to `scripts/agent/sentinel\.sh`.*planned' 'README contains obsolete path status'
require_absent docs/agent-prompts/sentinel-review.md '\.codex-reports/' 'Sentinel interpretation guidance names an obsolete report location'
category_result 'current paths and AGENTS/CLAUDE consistency' "$category_start"

category_start=$failure_count
for shell_path in scripts/agent/*.sh scripts/sentinel.sh; do
    record_check
    if ! bash -n "$shell_path"; then
        record_failure "shell syntax is invalid: $shell_path"
    fi
    require_executable "$shell_path"
done
category_result 'shell syntax and executable permissions' "$category_start"

category_start=$failure_count
tooling_files=$(find .gitignore AGENTS.md CLAUDE.md .agents/skills .claude/skills scripts/agent scripts/sentinel.sh docs/agents docs/agent-prompts/sentinel-review.md -type f -print | sort)
for tooling_path in $tooling_files; do
    record_check
    if grep -Eq '[[:blank:]]$' "$tooling_path"; then
        record_failure "trailing whitespace: $tooling_path"
    fi
done
credential_pattern="(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_./+=-]{16,})"
for tooling_path in $tooling_files; do
    record_check
    if LC_ALL=C grep -Eiq -- "$credential_pattern" "$tooling_path"; then
        record_failure "likely credential pattern (value withheld): $tooling_path"
    fi
done
category_result 'whitespace and likely credentials' "$category_start"

category_start=$failure_count
markdown_files=$(find AGENTS.md CLAUDE.md .agents/skills .claude/skills docs/agents docs/agent-prompts/sentinel-review.md -type f -name '*.md' -print | sort)
for markdown_path in $markdown_files; do
    markdown_dir=$(dirname -- "$markdown_path")
    links=$(grep -Eo '\]\([^)]+\)' "$markdown_path" 2>/dev/null | sed -E 's/^\]\((.*)\)$/\1/' || true)
    if [ -z "$links" ]; then
        record_check
        continue
    fi
    while IFS= read -r link_target; do
        record_check
        link_target=${link_target%%#*}
        link_target=${link_target#<}
        link_target=${link_target%>}
        case "$link_target" in
            ''|http://*|https://*|mailto:*|/*)
                continue
                ;;
        esac
        if [ ! -e "$markdown_dir/$link_target" ]; then
            record_failure "broken Markdown link in $markdown_path: $link_target"
        fi
    done <<EOF
$links
EOF
done
category_result 'Markdown links and required references' "$category_start"

printf '\n'
if [ "$failure_count" -eq 0 ]; then
    printf 'Agent tooling validator: PASS (%s checks)\n' "$check_count"
    exit 0
fi

printf 'Agent tooling validator: FAIL (%s finding(s), %s checks)\n' "$failure_count" "$check_count"
exit 1

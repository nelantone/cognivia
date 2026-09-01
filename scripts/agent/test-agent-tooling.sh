#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
fixture_root=$(mktemp -d "${TMPDIR:-/tmp}/cognivia-agent-tooling-tests.XXXXXX") || exit 1
trap 'rm -rf "$fixture_root"' EXIT HUP INT TERM

pass_count=0
failure_count=0

pass() {
    pass_count=$((pass_count + 1))
    printf 'PASS  %s\n' "$1"
}

fail() {
    failure_count=$((failure_count + 1))
    printf 'FAIL  %s\n' "$1"
}

assert_exit() {
    description=$1
    expected=$2
    actual=$3
    if [ "$actual" -eq "$expected" ]; then
        pass "$description"
    else
        fail "$description (expected exit $expected, got $actual)"
    fi
}

assert_contains() {
    description=$1
    path=$2
    pattern=$3
    if grep -Eq -- "$pattern" "$path"; then
        pass "$description"
    else
        fail "$description"
    fi
}

assert_not_contains() {
    description=$1
    path=$2
    pattern=$3
    if grep -Eq -- "$pattern" "$path"; then
        fail "$description"
    else
        pass "$description"
    fi
}

assert_count() {
    description=$1
    path=$2
    pattern=$3
    expected=$4
    actual=$(grep -Ec -- "$pattern" "$path" || true)
    if [ "$actual" -eq "$expected" ]; then
        pass "$description"
    else
        fail "$description (expected $expected, got $actual)"
    fi
}

assert_file() {
    description=$1
    path=$2
    if [ -f "$path" ]; then
        pass "$description"
    else
        fail "$description"
    fi
}

assert_not_file() {
    description=$1
    path=$2
    if [ -e "$path" ] || [ -L "$path" ]; then
        fail "$description"
    else
        pass "$description"
    fi
}

assert_fixed_contains() {
    description=$1
    path=$2
    expected_text=$3
    if grep -Fq -- "$expected_text" "$path"; then
        pass "$description"
    else
        fail "$description"
    fi
}

extract_concise_report_path() {
    sed -n 's#^file://\(/tmp/cognivia-sentinel-[0-9][0-9]*-[0-9][0-9]*\.txt\)$#\1#p' "$1" | head -n 1
}

create_sentinel_fixture() {
    fixture_name=$1
    fixture_path="$fixture_root/$fixture_name"
    mkdir -p "$fixture_path/scripts/agent" "$fixture_path/scripts" "$fixture_path/allowed"
    cp "$REPO_ROOT/scripts/agent/sentinel.sh" "$fixture_path/scripts/agent/sentinel.sh"
    cp "$REPO_ROOT/scripts/sentinel.sh" "$fixture_path/scripts/sentinel.sh"
    (
        cd "$fixture_path"
        git init -q
        git config user.email fixture@example.invalid
        git config user.name 'Cognivia Fixture'
        printf '%s\n' keep > allowed/.keep
        git add -- scripts/agent/sentinel.sh scripts/sentinel.sh allowed/.keep
        git commit -q -m baseline
    )
    printf '%s\n' "$fixture_path"
}

run_sentinel() {
    fixture_path=$1
    output_path=$2
    shift 2
    (
        cd "$fixture_path"
        /bin/bash scripts/agent/sentinel.sh "$@"
    ) > "$output_path" 2>&1
    command_status=$?
    return "$command_status"
}

copy_tooling_fixture() {
    destination=$1
    mkdir -p "$destination/docs/agent-prompts" "$destination/scripts"
    cp "$REPO_ROOT/.gitignore" "$destination/.gitignore"
    cp "$REPO_ROOT/AGENTS.md" "$destination/AGENTS.md"
    cp "$REPO_ROOT/CLAUDE.md" "$destination/CLAUDE.md"
    cp -R "$REPO_ROOT/.agents" "$destination/.agents"
    cp -R "$REPO_ROOT/.claude" "$destination/.claude"
    cp -R "$REPO_ROOT/docs/agents" "$destination/docs/agents"
    cp "$REPO_ROOT/docs/AGENT_HANDOFF.md" "$destination/docs/AGENT_HANDOFF.md"
    cp "$REPO_ROOT/docs/agent-prompts/sentinel-review.md" "$destination/docs/agent-prompts/sentinel-review.md"
    cp -R "$REPO_ROOT/scripts/agent" "$destination/scripts/agent"
    cp "$REPO_ROOT/scripts/sentinel.sh" "$destination/scripts/sentinel.sh"
}

run_validator() {
    fixture_path=$1
    output_path=$2
    (
        cd "$fixture_path"
        /bin/bash scripts/agent/validate-agent-tooling.sh
    ) > "$output_path" 2>&1
    command_status=$?
    return "$command_status"
}

run_compatibility_sentinel() {
    fixture_path=$1
    output_path=$2
    shift 2
    (
        cd "$fixture_path"
        /bin/bash scripts/sentinel.sh "$@"
    ) > "$output_path" 2>&1
    command_status=$?
    return "$command_status"
}

printf '%s\n' 'Cognivia agent-tooling regression fixtures'

fixture_secret='sk-'
secret_index=0
while [ "$secret_index" -lt 24 ]; do
    fixture_secret="${fixture_secret}a"
    secret_index=$((secret_index + 1))
done

fixture_path=$(create_sentinel_fixture rename-within-scope)
printf '%s\n' content > "$fixture_path/allowed/source.txt"
git -C "$fixture_path" add -- allowed/source.txt
git -C "$fixture_path" commit -q -m add-source
git -C "$fixture_path" mv allowed/source.txt allowed/destination.txt
output_path="$fixture_root/rename-within-scope.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'staged rename entirely within scope passes' 0 "$command_status"
assert_count 'in-scope rename prints scope success once' "$output_path" 'PASS: all changed paths are within the declared scope' 1

fixture_path=$(create_sentinel_fixture rename-into-scope)
printf '%s\n' content > "$fixture_path/outside.txt"
git -C "$fixture_path" add -- outside.txt
git -C "$fixture_path" commit -q -m add-source
git -C "$fixture_path" mv outside.txt allowed/moved.txt
output_path="$fixture_root/rename-into-scope.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'staged rename from outside into scope blocks' 1 "$command_status"
assert_contains 'rename finding includes source path' "$output_path" 'path: outside\.txt'
assert_contains 'rename finding includes destination path' "$output_path" 'path: allowed/moved\.txt'
assert_not_contains 'blocked rename omits scope success' "$output_path" 'PASS: all changed paths are within the declared scope'

fixture_path=$(create_sentinel_fixture rename-out-of-scope)
printf '%s\n' content > "$fixture_path/allowed/source.txt"
git -C "$fixture_path" add -- allowed/source.txt
git -C "$fixture_path" commit -q -m add-source
git -C "$fixture_path" mv allowed/source.txt moved.txt
output_path="$fixture_root/rename-out-of-scope.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'staged rename from scope to outside blocks' 1 "$command_status"
assert_contains 'outgoing rename includes source path' "$output_path" 'path: allowed/source\.txt'
assert_contains 'outgoing rename includes destination path' "$output_path" 'path: moved\.txt'

fixture_path=$(create_sentinel_fixture unstaged-rename)
printf '%s\n' content > "$fixture_path/outside.txt"
git -C "$fixture_path" add -- outside.txt
git -C "$fixture_path" commit -q -m add-source
mv "$fixture_path/outside.txt" "$fixture_path/allowed/moved.txt"
output_path="$fixture_root/unstaged-rename.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'unstaged outside-to-inside move blocks' 1 "$command_status"
assert_contains 'unstaged move includes deleted source' "$output_path" 'path: outside\.txt'
assert_contains 'unstaged move includes untracked destination' "$output_path" 'path: allowed/moved\.txt'

fixture_path=$(create_sentinel_fixture in-scope-change)
printf '%s\n' content > "$fixture_path/allowed/file.txt"
git -C "$fixture_path" add -- allowed/file.txt
git -C "$fixture_path" commit -q -m add-file
printf '%s\n' changed >> "$fixture_path/allowed/file.txt"
output_path="$fixture_root/in-scope-change.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'ordinary in-scope change passes' 0 "$command_status"
assert_count 'ordinary in-scope change prints scope success once' "$output_path" 'PASS: all changed paths are within the declared scope' 1

fixture_path=$(create_sentinel_fixture out-of-scope-change)
printf '%s\n' content > "$fixture_path/outside.txt"
git -C "$fixture_path" add -- outside.txt
git -C "$fixture_path" commit -q -m add-file
printf '%s\n' changed >> "$fixture_path/outside.txt"
output_path="$fixture_root/out-of-scope-change.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'ordinary out-of-scope change blocks' 1 "$command_status"
assert_contains 'out-of-scope change reports blocking result' "$output_path" 'BLOCKED:'
assert_not_contains 'out-of-scope change omits scope success' "$output_path" 'PASS: all changed paths are within the declared scope'

fixture_path=$(create_sentinel_fixture newline-untracked)
newline_directory=$(printf 'allowed\nallowed')
newline_untracked_path="$newline_directory/fake"
mkdir -p "$fixture_path/$newline_directory"
printf '%s\n' "$fixture_secret" > "$fixture_path/$newline_untracked_path"
output_path="$fixture_root/newline-untracked.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'untracked newline path outside scope blocks' 1 "$command_status"
assert_count 'untracked newline path remains one changed-path record' "$output_path" '^  path:' 1
assert_fixed_contains 'untracked newline path is escaped for display' "$output_path" "path: \$'allowed\\nallowed/fake'"
assert_not_contains 'untracked newline path does not produce a false scope PASS' "$output_path" 'PASS: all changed paths are within the declared scope'
assert_contains 'credential scan reaches an untracked newline path' "$output_path" 'likely credential pattern found in an untracked file'
assert_not_contains 'newline-path report withholds the fixture credential' "$output_path" "$fixture_secret"

fixture_path=$(create_sentinel_fixture newline-staged)
newline_staged_path=$(printf 'allowed/file\npart')
printf '%s\n' staged > "$fixture_path/$newline_staged_path"
git -C "$fixture_path" add -- "$newline_staged_path"
output_path="$fixture_root/newline-staged.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'staged newline path inside scope passes' 0 "$command_status"
assert_contains 'staged newline path count remains one' "$output_path" 'changed paths: 1; staged: 1; untracked: 0'
assert_count 'staged newline path is displayed once' "$output_path" '^  path:' 1
assert_fixed_contains 'staged newline path is escaped for display' "$output_path" "path: \$'allowed/file\\npart'"
assert_contains 'staged newline path preserves scope success' "$output_path" 'PASS: all changed paths are within the declared scope'

fixture_path=$(create_sentinel_fixture newline-rename)
newline_source_path=$(printf 'allowed/source\npart')
newline_destination_path=$(printf 'allowed/destination\npart')
printf '%s\n' tracked > "$fixture_path/$newline_source_path"
git -C "$fixture_path" add -- "$newline_source_path"
git -C "$fixture_path" commit -q -m add-newline-source
git -C "$fixture_path" mv "$newline_source_path" "$newline_destination_path"
output_path="$fixture_root/newline-rename.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'staged newline rename within scope passes' 0 "$command_status"
assert_contains 'newline rename retains both endpoint records' "$output_path" 'changed paths: 2; staged: 2; untracked: 0'
assert_count 'newline rename displays exactly two endpoints' "$output_path" '^  path:' 2
assert_fixed_contains 'newline rename displays its source endpoint safely' "$output_path" "path: \$'allowed/source\\npart'"
assert_fixed_contains 'newline rename displays its destination endpoint safely' "$output_path" "path: \$'allowed/destination\\npart'"
assert_contains 'newline rename preserves scope success' "$output_path" 'PASS: all changed paths are within the declared scope'

tooling_template="$fixture_root/tooling-template"
copy_tooling_fixture "$tooling_template"
output_path="$fixture_root/valid-tooling.out"
run_validator "$tooling_template" "$output_path"
command_status=$?
assert_exit 'valid canonical SKILL.md passes' 0 "$command_status"
assert_contains 'valid canonical metadata passes' "$output_path" 'PASS  skill names and metadata'
assert_contains 'valid CXP orchestration contract passes' "$output_path" 'PASS  required sections and canonical ownership'

fixture_path="$fixture_root/implicit-cxp"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '/allow_implicit_invocation:/d' "$fixture_path/.agents/skills/cxp/agents/openai.yaml"
output_path="$fixture_root/implicit-cxp.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'CXP without explicit-only Codex policy fails' 1 "$command_status"
assert_contains 'CXP Codex policy failure names the metadata path' "$output_path" 'CXP must remain explicit-only in Codex: \.agents/skills/cxp/agents/openai\.yaml'

fixture_path="$fixture_root/implicit-claude-cxp"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '/disable-model-invocation:/d' "$fixture_path/.claude/skills/cxp/SKILL.md"
output_path="$fixture_root/implicit-claude-cxp.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'CXP without explicit-only Claude policy fails' 1 "$command_status"
assert_contains 'CXP Claude policy failure names the adapter path' "$output_path" 'CXP must remain explicit-only in Claude: \.claude/skills/cxp/SKILL\.md'

fixture_path="$fixture_root/missing-opening"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '1d' "$fixture_path/.agents/skills/task-brief/SKILL.md"
output_path="$fixture_root/missing-opening.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'missing opening delimiter fails' 1 "$command_status"
assert_contains 'missing opening output names the path' "$output_path" 'opening delimiter is missing: \.agents/skills/task-brief/SKILL\.md'

fixture_path="$fixture_root/missing-closing"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '4d' "$fixture_path/.agents/skills/task-brief/SKILL.md"
output_path="$fixture_root/missing-closing.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'missing closing delimiter fails' 1 "$command_status"
assert_contains 'missing closing output names the path' "$output_path" 'closing delimiter is missing: \.agents/skills/task-brief/SKILL\.md'

fixture_path="$fixture_root/empty-frontmatter"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '2,3d' "$fixture_path/.agents/skills/task-brief/SKILL.md"
output_path="$fixture_root/empty-frontmatter.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'empty bounded frontmatter fails' 1 "$command_status"
assert_contains 'empty frontmatter output names the path' "$output_path" 'frontmatter is empty: \.agents/skills/task-brief/SKILL\.md'

fixture_path="$fixture_root/unclosed-metadata"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '4d' "$fixture_path/.agents/skills/task-brief/SKILL.md"
output_path="$fixture_root/unclosed-metadata.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'metadata in an unclosed block does not pass' 1 "$command_status"
assert_not_contains 'frontmatter failure does not expose skill content' "$output_path" 'Turn an implementation, debugging, audit, or migration request'

fixture_path="$fixture_root/body-before-closing"
cp -R "$tooling_template" "$fixture_path"
sed -i '' '4d' "$fixture_path/.agents/skills/task-brief/SKILL.md"
printf '%s\n' '---' >> "$fixture_path/.agents/skills/task-brief/SKILL.md"
output_path="$fixture_root/body-before-closing.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'closing delimiter after Markdown body fails' 1 "$command_status"
assert_contains 'body-before-closing output names the path' "$output_path" 'Markdown body begins before skill frontmatter closes: \.agents/skills/task-brief/SKILL\.md'

fixture_path="$fixture_root/invalid-claude-adapter"
cp -R "$tooling_template" "$fixture_path"
rm "$fixture_path/.claude/skills/task-brief"
ln -s ../../.agents/skills/missing "$fixture_path/.claude/skills/task-brief"
output_path="$fixture_root/invalid-claude-adapter.out"
run_validator "$fixture_path" "$output_path"
command_status=$?
assert_exit 'invalid Claude canonical adapter fails' 1 "$command_status"
assert_contains 'Claude adapter failure names the path' "$output_path" 'wrong target: \.claude/skills/task-brief'

fixture_path=$(create_sentinel_fixture report-pass)
printf '%s\n' changed >> "$fixture_path/allowed/.keep"
git -C "$fixture_path" add -- allowed/.keep
output_path="$fixture_root/report-pass.out"
run_sentinel "$fixture_path" "$output_path" --scope allowed
command_status=$?
assert_exit 'PASS retains a zero exit' 0 "$command_status"
assert_contains 'concise PASS result is reported' "$output_path" '^Result: PASS$'
assert_contains 'concise output contains blocking count' "$output_path" '^Blocking findings: 0$'
assert_contains 'concise output contains advisory count' "$output_path" '^Advisory notes: 0$'
assert_contains 'concise output contains latest file URL' "$output_path" '^file:///tmp/cognivia-sentinel-latest\.txt$'
assert_contains 'concise output contains copy command' "$output_path" '^pbcopy < /tmp/cognivia-sentinel-latest\.txt$'
assert_contains 'concise output contains Finder command' "$output_path" '^open -R /tmp/cognivia-sentinel-latest\.txt$'
assert_not_contains 'concise output omits detailed checks' "$output_path" '^Scope verification$'
report_path=$(extract_concise_report_path "$output_path")
assert_file 'default execution creates a timestamped report' "$report_path"
assert_file 'default execution updates the latest report' '/tmp/cognivia-sentinel-latest.txt'
assert_contains 'complete report includes the format version' "$report_path" '^Sentinel/report format version: 1$'
assert_contains 'complete report includes the final result' "$report_path" '^Final result: PASS$'

fixture_path=$(create_sentinel_fixture report-pass-with-notes)
output_path="$fixture_root/report-pass-with-notes.out"
run_sentinel "$fixture_path" "$output_path"
command_status=$?
assert_exit 'PASS WITH NOTES retains a zero exit' 0 "$command_status"
assert_contains 'concise PASS WITH NOTES result is reported' "$output_path" '^Result: PASS WITH NOTES$'

fixture_path=$(create_sentinel_fixture report-blocked)
printf '%s\n' outside > "$fixture_path/outside.txt"
output_path="$fixture_root/report-blocked.out"
run_sentinel "$fixture_path" "$output_path" --scope allowed
command_status=$?
assert_exit 'BLOCKED retains a non-zero exit' 1 "$command_status"
assert_contains 'concise BLOCKED result is reported' "$output_path" '^Result: BLOCKED$'

fixture_path=$(create_sentinel_fixture report-verbose)
custom_verbose_report="$fixture_root/verbose-output/report.txt"
output_path="$fixture_root/report-verbose.out"
run_sentinel "$fixture_path" "$output_path" --verbose --report "$custom_verbose_report"
command_status=$?
assert_exit '--verbose with --report preserves validation exit' 0 "$command_status"
assert_file '--verbose persists the requested complete report' "$custom_verbose_report"
assert_contains '--verbose prints the complete report' "$output_path" '^Cognivia Sentinel report$'
assert_contains '--verbose includes detailed checks' "$output_path" '^Scope verification$'
assert_not_contains '--verbose does not print the concise Report label' "$output_path" '^Report:$'

latest_checksum_before=$(cksum /tmp/cognivia-sentinel-latest.txt)
timestamp_count_before=$(ls /tmp/cognivia-sentinel-[0-9]*.txt 2>/dev/null | wc -l | tr -d ' ')
fixture_path=$(create_sentinel_fixture report-stdout)
output_path="$fixture_root/report-stdout.out"
run_sentinel "$fixture_path" "$output_path" --stdout
command_status=$?
latest_checksum_after=$(cksum /tmp/cognivia-sentinel-latest.txt)
timestamp_count_after=$(ls /tmp/cognivia-sentinel-[0-9]*.txt 2>/dev/null | wc -l | tr -d ' ')
assert_exit '--stdout preserves validation exit' 0 "$command_status"
assert_contains '--stdout prints the complete report' "$output_path" '^Cognivia Sentinel report$'
if [ "$latest_checksum_before" = "$latest_checksum_after" ]; then
    pass '--stdout does not update the latest report'
else
    fail '--stdout does not update the latest report'
fi
if [ "$timestamp_count_before" -eq "$timestamp_count_after" ]; then
    pass '--stdout does not create a timestamped report'
else
    fail '--stdout does not create a timestamped report'
fi

fixture_path=$(create_sentinel_fixture report-custom)
custom_report="$fixture_root/custom-output/report.txt"
output_path="$fixture_root/report-custom.out"
run_sentinel "$fixture_path" "$output_path" --report "$custom_report"
command_status=$?
assert_exit '--report writes successfully outside the fixture repository' 0 "$command_status"
assert_file '--report creates parent directories and the requested file' "$custom_report"
assert_contains '--report concise output links to the requested file' "$output_path" '^file://.*/custom-output/report\.txt$'

fixture_path=$(create_sentinel_fixture report-symlink-repository)
physical_fixture_path=$(CDPATH= cd -- "$fixture_path" && pwd -P)
repository_link="$fixture_root/report-repository-link"
ln -s "$fixture_path" "$repository_link"
inside_report="$fixture_path/inside-report.txt"
output_path="$fixture_root/report-symlink-repository.out"
run_sentinel "$repository_link" "$output_path" --report "$inside_report"
command_status=$?
assert_exit 'physical report path inside symlinked repository blocks' 1 "$command_status"
assert_not_file 'physical report path inside repository is not created' "$inside_report"
assert_fixed_contains 'symlinked invocation reports the physical repository root' "$output_path" "Repository root: $physical_fixture_path"
assert_contains 'symlinked repository containment failure is explicit' "$output_path" '^Final result: BLOCKED$'

through_link_report="$repository_link/through-link-report.txt"
output_path="$fixture_root/report-through-link.out"
run_sentinel "$fixture_path" "$output_path" --report "$through_link_report"
command_status=$?
assert_exit 'report destination through repository symlink blocks' 1 "$command_status"
assert_not_file 'report destination through repository symlink is not created' "$fixture_path/through-link-report.txt"

case_alias=$(printf '%s' "$fixture_path" | tr '[:lower:]' '[:upper:]')
if [ "$case_alias" != "$fixture_path" ] && [ -d "$case_alias" ]; then
    case_alias_report="$case_alias/case-alias-report.txt"
    output_path="$fixture_root/report-case-alias.out"
    run_sentinel "$fixture_path" "$output_path" --report "$case_alias_report"
    command_status=$?
    assert_exit 'filesystem case-alias report destination blocks' 1 "$command_status"
    assert_not_file 'filesystem case-alias report is not created' "$fixture_path/case-alias-report.txt"
else
    pass 'filesystem case alias is unavailable on this volume'
fi

fixture_path=$(create_sentinel_fixture report-worktree-administration)
worktree_path="$fixture_root/report-linked-worktree"
git -C "$fixture_path" worktree add -q -b sentinel-report-fixture "$worktree_path"
worktree_git_dir=$(git -C "$worktree_path" rev-parse --git-dir)
case "$worktree_git_dir" in
    /*)
        ;;
    *)
        worktree_git_dir="$worktree_path/$worktree_git_dir"
        ;;
esac
administrative_report="$worktree_git_dir/sentinel-report.txt"
output_path="$fixture_root/report-worktree-administration.out"
run_sentinel "$worktree_path" "$output_path" --report "$administrative_report"
command_status=$?
assert_exit 'worktree administrative report destination blocks' 1 "$command_status"
assert_not_file 'worktree administrative report is not created' "$administrative_report"

output_path="$fixture_root/report-missing-value.out"
run_sentinel "$fixture_path" "$output_path" --report
command_status=$?
assert_exit 'missing --report value is rejected' 2 "$command_status"
assert_contains 'missing --report value has a concise usage error' "$output_path" '^Sentinel usage error: --report requires a path\.$'

output_path="$fixture_root/report-conflict.out"
run_sentinel "$fixture_path" "$output_path" --stdout --report "$custom_report"
command_status=$?
assert_exit '--stdout and --report conflict is rejected' 2 "$command_status"
assert_contains 'option conflict has a concise usage error' "$output_path" '^Sentinel usage error: --stdout and --report cannot be combined\.$'

output_path="$fixture_root/report-directory.out"
run_sentinel "$fixture_path" "$output_path" --report "$fixture_root"
command_status=$?
assert_exit 'directory report destination blocks deterministically' 1 "$command_status"
assert_contains 'directory report failure names only the safe category' "$output_path" '^Final result: BLOCKED$'

fixture_path=$(create_sentinel_fixture report-secret)
printf '%s\n' "$fixture_secret" > "$fixture_path/allowed/secret.txt"
output_path="$fixture_root/report-secret.out"
run_sentinel "$fixture_path" "$output_path" --scope allowed
command_status=$?
assert_exit 'likely credential fixture blocks' 1 "$command_status"
secret_report_path=$(extract_concise_report_path "$output_path")
assert_file 'blocked secret fixture still persists its report' "$secret_report_path"
assert_not_contains 'concise output does not expose the fixture credential' "$output_path" "$fixture_secret"
assert_not_contains 'complete report does not expose the fixture credential' "$secret_report_path" "$fixture_secret"
assert_contains 'complete report preserves the redacted secret finding' "$secret_report_path" 'matching value withheld'

fixture_path=$(create_sentinel_fixture leading-dash-credentials)
printf '%s\n' safe > "$fixture_path/-secret"
printf '%s\n' safe > "$fixture_path/--config"
printf '%s\n' "$fixture_secret" > "$fixture_path/---token"
output_path="$fixture_root/leading-dash-credentials.out"
run_sentinel "$fixture_path" "$output_path" --stdout
command_status=$?
assert_exit 'leading-dash credential filename is scanned and blocks' 1 "$command_status"
assert_contains 'leading-dash scan identifies the credential-bearing path' "$output_path" 'matching value withheld: ---token'
assert_not_contains 'leading-dash scan emits no grep option error' "$output_path" 'grep:'
assert_not_contains 'leading-dash scan withholds credential PASS' "$output_path" 'PASS: no likely credential values detected'
assert_not_contains 'leading-dash scan withholds the fixture credential' "$output_path" "$fixture_secret"

fixture_path=$(create_sentinel_fixture incomplete-credential-scan)
ln -s missing-target "$fixture_path/allowed/unreadable-link"
output_path="$fixture_root/incomplete-credential-scan.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'incomplete non-regular credential scan remains advisory' 0 "$command_status"
assert_contains 'incomplete credential scan names the escaped path' "$output_path" 'credential scan incomplete for non-regular untracked path: allowed/unreadable-link'
assert_not_contains 'incomplete credential scan withholds credential PASS' "$output_path" 'PASS: no likely credential values detected'

fixture_path=$(create_sentinel_fixture large-text-scan)
dd if=/dev/zero bs=1048576 count=5 2>/dev/null | tr '\000' x > "$fixture_path/allowed/large.txt"
output_path="$fixture_root/large-text-scan.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'bounded large text scan remains advisory without a finding' 0 "$command_status"
assert_contains 'large text scan documents its 4 MiB bound' "$output_path" 'credential scan limited to the first 4 MiB of large untracked file: allowed/large.txt'
assert_not_contains 'bounded large text scan withholds credential PASS' "$output_path" 'PASS: no likely credential values detected'

fixture_path=$(create_sentinel_fixture large-binary-scan)
dd if=/dev/zero of="$fixture_path/allowed/large.bin" bs=1048576 count=5 2>/dev/null
output_path="$fixture_root/large-binary-scan.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'bounded large binary scan remains advisory without a finding' 0 "$command_status"
assert_contains 'large binary scan documents its 4 MiB bound' "$output_path" 'credential scan limited to the first 4 MiB of large untracked file: allowed/large.bin'
assert_not_contains 'bounded large binary scan withholds credential PASS' "$output_path" 'PASS: no likely credential values detected'

fixture_path=$(create_sentinel_fixture large-secret-scan)
{ printf '%s\n' "$fixture_secret"; dd if=/dev/zero bs=1048576 count=5 2>/dev/null | tr '\000' x; } > "$fixture_path/allowed/large-secret.txt"
output_path="$fixture_root/large-secret-scan.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'bounded large scan detects a credential in its scanned prefix' 1 "$command_status"
assert_contains 'large credential finding names the path without its value' "$output_path" 'matching value withheld: allowed/large-secret.txt'
assert_not_contains 'large credential scan withholds the fixture credential' "$output_path" "$fixture_secret"

fixture_path=$(create_sentinel_fixture large-unscanned-tail)
dd if=/dev/zero bs=1048576 count=5 2>/dev/null | tr '\000' x > "$fixture_path/allowed/large-tail.txt"
printf '%s\n' "$fixture_secret" >> "$fixture_path/allowed/large-tail.txt"
output_path="$fixture_root/large-unscanned-tail.out"
run_sentinel "$fixture_path" "$output_path" --stdout --scope allowed
command_status=$?
assert_exit 'credential beyond the bounded prefix remains advisory' 0 "$command_status"
assert_contains 'unscanned large tail is named as incomplete' "$output_path" 'credential scan limited to the first 4 MiB of large untracked file: allowed/large-tail.txt'
assert_not_contains 'unscanned large tail withholds credential PASS' "$output_path" 'PASS: no likely credential values detected'
assert_not_contains 'unscanned large tail withholds the fixture credential' "$output_path" "$fixture_secret"

fixture_path=$(create_sentinel_fixture report-compatibility)
output_path="$fixture_root/report-compatibility.out"
run_compatibility_sentinel "$fixture_path" "$output_path"
command_status=$?
assert_exit 'legacy Sentinel forwarding path preserves exit behavior' 0 "$command_status"
assert_contains 'legacy Sentinel forwarding path preserves concise output' "$output_path" '^Cognivia Sentinel$'

printf '\nAgent-tooling fixtures: %s passed, %s failed\n' "$pass_count" "$failure_count"
if [ "$failure_count" -gt 0 ]; then
    exit 1
fi

#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd -P)
cd "$REPO_ROOT"

expected_branch=''
scope_paths=()
scope_path_count=0
failure_count=0
note_count=0
verbose=0
stdout_only=0
requested_report=''
report_format_version='1'
report_stage=''
latest_stage=''
credential_scan_limit_bytes=4194304

usage() {
    printf '%s\n' \
        'Usage: scripts/agent/sentinel.sh [OPTIONS]' \
        '' \
        'Options:' \
        '  --expected-branch NAME  Require the current branch name.' \
        '  --scope PATH            Declare an allowed changed-path scope; repeatable.' \
        '  --verbose               Persist and print the complete report.' \
        '  --report PATH           Persist the complete report at an absolute path outside the repository.' \
        '  --stdout                Print the complete report without persisting it.' \
        '  --help                  Show this help.'
}

fail() {
    failure_count=$((failure_count + 1))
    printf '  FAIL: %s\n' "$1"
}

note() {
    note_count=$((note_count + 1))
    printf '  NOTE: %s\n' "$1"
}

path_is_in_scope() {
    candidate=$1
    for scope_path in "${scope_paths[@]}"; do
        case "$candidate" in
            "$scope_path"|"$scope_path"/*)
                return 0
                ;;
        esac
    done
    return 1
}

path_is_sensitive() {
    candidate=$1
    case "$candidate" in
        .env|.env.*|*/.env|*/.env.*|*.pem|*.p12|*.pfx|*.key|*credentials*.json|*service-account*.json)
            return 0
            ;;
    esac
    return 1
}

path_is_generated() {
    candidate=$1
    case "$candidate" in
        .codex-reports/*|*/.codex-reports/*|*/__pycache__/*|*.pyc|*.pyo|.pytest_cache/*|*/.pytest_cache/*|.mypy_cache/*|*/.mypy_cache/*|htmlcov/*|*/htmlcov/*|.coverage|*/.coverage|*.log|*.tmp|*~|*.swp|.DS_Store|*/.DS_Store)
            return 0
            ;;
    esac
    return 1
}

collect_name_status_paths() {
    name_status_path=$1
    output_path=$2
    : > "$output_path"
    while IFS= read -r -d '' change_status; do
        case "$change_status" in
            R*|C*)
                IFS= read -r -d '' source_path || return 1
                IFS= read -r -d '' destination_path || return 1
                printf '%s\0%s\0' "$source_path" "$destination_path" >> "$output_path"
                ;;
            *)
                IFS= read -r -d '' changed_path || return 1
                printf '%s\0' "$changed_path" >> "$output_path"
                ;;
        esac
    done < "$name_status_path"
}

merge_unique_nul_paths() {
    merged_path=$1
    shift
    : > "$merged_path"
    for source_path_file in "$@"; do
        while IFS= read -r -d '' candidate_path; do
            duplicate_path=0
            while IFS= read -r -d '' existing_path; do
                if [ "$candidate_path" = "$existing_path" ]; then
                    duplicate_path=1
                    break
                fi
            done < "$merged_path"
            if [ "$duplicate_path" -eq 0 ]; then
                printf '%s\0' "$candidate_path" >> "$merged_path"
            fi
        done < "$source_path_file"
    done
}

count_nul_paths() {
    count_path=$1
    nul_path_count=0
    while IFS= read -r -d '' counted_path; do
        nul_path_count=$((nul_path_count + 1))
    done < "$count_path"
    printf '%s' "$nul_path_count"
}

count_nul_overlap() {
    first_path_file=$1
    second_path_file=$2
    overlap_path_count=0
    while IFS= read -r -d '' first_path; do
        while IFS= read -r -d '' second_path; do
            if [ "$first_path" = "$second_path" ]; then
                overlap_path_count=$((overlap_path_count + 1))
                break
            fi
        done < "$second_path_file"
    done < "$first_path_file"
    printf '%s' "$overlap_path_count"
}

quote_path() {
    printf '%q' "$1"
}

canonicalize_existing_path() {
    candidate=$1
    case "$candidate" in
        /*)
            absolute_candidate=$candidate
            ;;
        *)
            absolute_candidate="$REPO_ROOT/$candidate"
            ;;
    esac
    if [ -d "$absolute_candidate" ]; then
        CDPATH= cd -- "$absolute_candidate" 2>/dev/null && pwd -P
        return $?
    fi
    existing_parent=${absolute_candidate%/*}
    existing_name=${absolute_candidate##*/}
    physical_parent=$(CDPATH= cd -- "$existing_parent" 2>/dev/null && pwd -P) || return 1
    printf '%s/%s' "$physical_parent" "$existing_name"
}

path_is_within_root() {
    candidate=$1
    protected_root=$2
    case "$candidate" in
        "$protected_root"|"$protected_root"/*)
            return 0
            ;;
    esac
    return 1
}

path_has_dot_component() {
    candidate=$1
    case "$candidate" in
        */./*|*/../*|*/.|*/..)
            return 0
            ;;
    esac
    return 1
}

resolve_report_path() {
    candidate=$1
    case "$candidate" in
        *'
'*)
            return 1
            ;;
    esac
    case "$candidate" in
        /*)
            ;;
        *)
            return 1
            ;;
    esac
    if path_has_dot_component "$candidate"; then
        return 1
    fi

    candidate_parent=${candidate%/*}
    candidate_name=${candidate##*/}
    if [ -z "$candidate_parent" ] || [ -z "$candidate_name" ]; then
        return 1
    fi

    probe_path=$candidate_parent
    missing_suffix=''
    while [ ! -d "$probe_path" ]; do
        probe_name=${probe_path##*/}
        if [ -z "$probe_name" ]; then
            return 1
        fi
        if [ -z "$missing_suffix" ]; then
            missing_suffix=$probe_name
        else
            missing_suffix="$probe_name/$missing_suffix"
        fi
        next_probe=${probe_path%/*}
        if [ -z "$next_probe" ]; then
            next_probe='/'
        fi
        if [ "$next_probe" = "$probe_path" ]; then
            return 1
        fi
        probe_path=$next_probe
    done

    canonical_parent=$(CDPATH= cd -- "$probe_path" 2>/dev/null && pwd -P) || return 1
    if [ -n "$missing_suffix" ]; then
        if [ "$canonical_parent" = '/' ]; then
            canonical_parent="/$missing_suffix"
        else
            canonical_parent="$canonical_parent/$missing_suffix"
        fi
    fi
    for protected_root in "$REPO_ROOT" "$GIT_DIR" "$GIT_COMMON_DIR"; do
        if path_is_within_root "$canonical_parent" "$protected_root"; then
            return 1
        fi
    done
    if ! mkdir -p "$canonical_parent" 2>/dev/null; then
        return 1
    fi
    resolved_report_path="$canonical_parent/$candidate_name"
    if [ -d "$resolved_report_path" ]; then
        return 1
    fi
    return 0
}

file_url() {
    printf '%s' "$1" | sed \
        -e 's/%/%25/g' \
        -e 's/ /%20/g' \
        -e 's/#/%23/g' \
        -e 's/?/%3F/g' \
        -e 's/\[/%5B/g' \
        -e 's/\]/%5D/g'
}

set_final_result() {
    if [ "$failure_count" -gt 0 ]; then
        final_result='BLOCKED'
        sentinel_exit=1
    elif [ "$note_count" -gt 0 ]; then
        final_result='PASS WITH NOTES'
        sentinel_exit=0
    else
        final_result='PASS'
        sentinel_exit=0
    fi
}

append_detailed_summary() {
    printf '\nSentinel summary\n' >> "$body_file"
    case "$final_result" in
        BLOCKED)
            printf '  BLOCKED: %s deterministic finding(s), %s advisory note(s)\n' "$failure_count" "$note_count" >> "$body_file"
            ;;
        'PASS WITH NOTES')
            printf '  PASS WITH NOTES: %s advisory note(s)\n' "$note_count" >> "$body_file"
            ;;
        PASS)
            printf '%s\n' '  PASS' >> "$body_file"
            ;;
    esac
    printf '%s\n' 'Optional human/LLM interpretation: docs/agent-prompts/sentinel-review.md' >> "$body_file"
}

build_complete_report() {
    {
        printf '%s\n' 'Cognivia Sentinel report'
        printf 'Timestamp: %s\n' "$report_timestamp"
        printf 'Repository root: %s\n' "$REPO_ROOT"
        printf 'Current branch: %s\n' "$current_branch"
        printf 'Current commit: %s\n' "$current_commit"
        if [ -n "$expected_branch" ]; then
            printf 'Expected branch: %s\n' "$expected_branch"
        fi
        if [ "$scope_path_count" -gt 0 ]; then
            printf '%s\n' 'Declared scopes:'
            for scope_path in "${scope_paths[@]}"; do
                printf '  - %s\n' "$(quote_path "$scope_path")"
            done
        fi
        printf 'Sentinel/report format version: %s\n' "$report_format_version"
        printf 'Final result: %s\n' "$final_result"
        printf '%s\n' '--------------------------------------------------'
        cat "$body_file"
    } > "$complete_report_file"
}

print_concise_summary() {
    report_url=$(file_url "$resolved_report_path")
    latest_url=$(file_url '/tmp/cognivia-sentinel-latest.txt')
    printf '%s\n' \
        '--------------------------------------------------' \
        'Cognivia Sentinel' \
        '--------------------------------------------------' \
        ''
    printf 'Result: %s\n' "$final_result"
    printf 'Blocking findings: %s\n' "$failure_count"
    printf 'Advisory notes: %s\n\n' "$note_count"
    printf 'Report:\nfile://%s\n\n' "$report_url"
    printf 'Latest:\nfile://%s\n\n' "$latest_url"
    printf '%s\n' \
        'Copy:' \
        'pbcopy < /tmp/cognivia-sentinel-latest.txt' \
        '' \
        'Reveal:' \
        'open -R /tmp/cognivia-sentinel-latest.txt' \
        '--------------------------------------------------'
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --expected-branch)
            if [ "$#" -lt 2 ]; then
                usage
                exit 2
            fi
            expected_branch=$2
            shift 2
            ;;
        --scope)
            if [ "$#" -lt 2 ]; then
                usage
                exit 2
            fi
            scope_paths[$scope_path_count]=$2
            scope_path_count=$((scope_path_count + 1))
            shift 2
            ;;
        --verbose)
            verbose=1
            shift
            ;;
        --report)
            if [ "$#" -lt 2 ] || [ -z "$2" ]; then
                printf '%s\n' 'Sentinel usage error: --report requires a path.' >&2
                usage >&2
                exit 2
            fi
            case "$2" in
                --*)
                    printf '%s\n' 'Sentinel usage error: --report requires a path.' >&2
                    usage >&2
                    exit 2
                    ;;
            esac
            requested_report=$2
            shift 2
            ;;
        --stdout)
            stdout_only=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown argument: %s\n' "$1"
            usage
            exit 2
            ;;
    esac
done

if [ "$stdout_only" -eq 1 ] && [ -n "$requested_report" ]; then
    printf '%s\n' 'Sentinel usage error: --stdout and --report cannot be combined.' >&2
    usage >&2
    exit 2
fi

git_dir_raw=$(git rev-parse --git-dir 2>/dev/null) || exit 1
git_common_dir_raw=$(git rev-parse --git-common-dir 2>/dev/null) || exit 1
GIT_DIR=$(canonicalize_existing_path "$git_dir_raw") || exit 1
GIT_COMMON_DIR=$(canonicalize_existing_path "$git_common_dir_raw") || exit 1

sentinel_tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/cognivia-sentinel.XXXXXX") || exit 1
trap 'rm -rf "$sentinel_tmpdir"; [ -z "$report_stage" ] || rm -f "$report_stage"; [ -z "$latest_stage" ] || rm -f "$latest_stage"' EXIT HUP INT TERM
umask 077
changed_paths_file="$sentinel_tmpdir/changed-paths"
unstaged_paths_file="$sentinel_tmpdir/unstaged-paths"
staged_paths_file="$sentinel_tmpdir/staged-paths"
untracked_paths_file="$sentinel_tmpdir/untracked-paths"
unstaged_status_file="$sentinel_tmpdir/unstaged-status"
staged_status_file="$sentinel_tmpdir/staged-status"
untracked_raw_file="$sentinel_tmpdir/untracked-raw"
diff_file="$sentinel_tmpdir/added-lines.diff"
tracked_added_file="$sentinel_tmpdir/tracked-added-lines"
credential_sample_file="$sentinel_tmpdir/credential-sample"
body_file="$sentinel_tmpdir/report-body"
checks_body_file="$sentinel_tmpdir/checks-body"
complete_report_file="$sentinel_tmpdir/complete-report"

exec 3>&1 4>&2
exec > "$body_file" 2>&1

git diff --name-status -z -M --no-ext-diff > "$unstaged_status_file"
git diff --cached --name-status -z -M --no-ext-diff > "$staged_status_file"
if ! collect_name_status_paths "$unstaged_status_file" "$unstaged_paths_file"; then
    fail 'could not parse unstaged Git name-status data'
fi
if ! collect_name_status_paths "$staged_status_file" "$staged_paths_file"; then
    fail 'could not parse staged Git name-status data'
fi
git ls-files --others --exclude-standard -z > "$untracked_raw_file"
cp "$untracked_raw_file" "$untracked_paths_file"
merge_unique_nul_paths "$changed_paths_file" "$unstaged_paths_file" "$staged_paths_file" "$untracked_paths_file"
{
    git diff --no-ext-diff --unified=0
    git diff --cached --no-ext-diff --unified=0
} > "$diff_file"

current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || printf '%s' 'DETACHED')
current_commit=$(git rev-parse --verify HEAD 2>/dev/null || printf '%s' 'UNBORN')
changed_count=$(count_nul_paths "$changed_paths_file")
staged_count=$(count_nul_paths "$staged_paths_file")
untracked_count=$(count_nul_paths "$untracked_paths_file")

printf '%s\n' 'Cognivia Sentinel: deterministic local advisory gate'
printf '%s\n' 'No network, provider, credential, install, or Git mutation is performed.'
printf '\nBranch and working tree\n'
printf '  branch: %s\n' "$current_branch"
printf '  changed paths: %s; staged: %s; untracked: %s\n' "$changed_count" "$staged_count" "$untracked_count"
if [ -n "$expected_branch" ] && [ "$current_branch" != "$expected_branch" ]; then
    fail "expected branch '$expected_branch'; found '$current_branch'"
fi

printf '\nScope verification\n'
scope_violation=0
if [ "$changed_count" -eq 0 ]; then
    printf '%s\n' '  PASS: working tree is clean'
else
    while IFS= read -r -d '' changed_path; do
        quoted_path=$(quote_path "$changed_path")
        printf '  path: %s\n' "$quoted_path"
        if [ "$scope_path_count" -gt 0 ] && ! path_is_in_scope "$changed_path"; then
            scope_violation=1
            fail "changed path is outside the declared scope: $quoted_path"
        fi
    done < "$changed_paths_file"
    if [ "$scope_path_count" -eq 0 ]; then
        note 'no --scope paths supplied; changed paths require human scope confirmation'
    elif [ "$scope_violation" -eq 0 ]; then
        printf '%s\n' '  PASS: all changed paths are within the declared scope'
    fi
fi

printf '\nUnexpected and generated files\n'
unexpected_count=0
while IFS= read -r -d '' changed_path; do
    quoted_path=$(quote_path "$changed_path")
    if path_is_sensitive "$changed_path"; then
        unexpected_count=$((unexpected_count + 1))
        fail "sensitive filename requires manual review; content was not read: $quoted_path"
    fi
    if path_is_generated "$changed_path"; then
        unexpected_count=$((unexpected_count + 1))
        fail "generated or temporary artifact is part of the change: $quoted_path"
    fi
done < "$changed_paths_file"
while IFS= read -r -d '' untracked_path; do
    if ! path_is_sensitive "$untracked_path" && ! path_is_generated "$untracked_path"; then
        unexpected_count=$((unexpected_count + 1))
        note "untracked file requires an ownership decision: $(quote_path "$untracked_path")"
    fi
done < "$untracked_paths_file"
if [ "$unexpected_count" -eq 0 ]; then
    printf '%s\n' '  PASS: no unexpected, sensitive, generated, or temporary paths detected'
fi

printf '\nLikely secret patterns\n'
credential_pattern="(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_./+=-]{16,})"
secret_finding=0
credential_scan_complete=1
if sed -n '/^+++/d; /^+/p' "$diff_file" > "$tracked_added_file"; then
    LC_ALL=C grep -Eiq -- "$credential_pattern" "$tracked_added_file"
    tracked_scan_status=$?
    case "$tracked_scan_status" in
        0)
            secret_finding=1
            fail 'likely credential pattern found in a tracked diff; matching value withheld'
            ;;
        1)
            ;;
        *)
            credential_scan_complete=0
            note 'tracked-diff credential scan could not be completed'
            ;;
    esac
else
    credential_scan_complete=0
    note 'tracked-diff credential scan could not be prepared'
fi
while IFS= read -r -d '' untracked_path; do
    quoted_path=$(quote_path "$untracked_path")
    if path_is_sensitive "$untracked_path"; then
        credential_scan_complete=0
        note "credential content scan omitted for sensitive path: $quoted_path"
        continue
    fi
    if [ -L "$untracked_path" ] || [ ! -f "$untracked_path" ]; then
        credential_scan_complete=0
        note "credential scan incomplete for non-regular untracked path: $quoted_path"
        continue
    fi
    file_size_output=$(wc -c < "$untracked_path" 2>/dev/null)
    file_size_status=$?
    file_size=$(printf '%s' "$file_size_output" | tr -d ' ')
    case "$file_size" in
        ''|*[!0-9]*)
            file_size_status=1
            ;;
    esac
    if [ "$file_size_status" -ne 0 ]; then
        credential_scan_complete=0
        note "credential scan could not read untracked file metadata: $quoted_path"
        continue
    fi

    credential_scan_path=$untracked_path
    if [ "$file_size" -gt "$credential_scan_limit_bytes" ]; then
        if dd if="$untracked_path" of="$credential_sample_file" bs=1048576 count=4 2>/dev/null; then
            credential_scan_path=$credential_sample_file
            credential_scan_complete=0
            note "credential scan limited to the first 4 MiB of large untracked file: $quoted_path"
        else
            credential_scan_complete=0
            note "credential scan could not read large untracked file: $quoted_path"
            continue
        fi
    fi

    LC_ALL=C grep -Eiq -- "$credential_pattern" "$credential_scan_path"
    untracked_scan_status=$?
    case "$untracked_scan_status" in
        0)
            secret_finding=1
            fail "likely credential pattern found in an untracked file; matching value withheld: $quoted_path"
            ;;
        1)
            ;;
        *)
            credential_scan_complete=0
            note "credential scan could not be completed for untracked file: $quoted_path"
            ;;
    esac
done < "$untracked_paths_file"
if [ "$secret_finding" -eq 0 ] && [ "$credential_scan_complete" -eq 1 ]; then
    printf '%s\n' '  PASS: no likely credential values detected in changed text'
fi

printf '\nStaged scope sanity\n'
if [ "$staged_count" -eq 0 ]; then
    note 'nothing is staged'
else
    if git diff --cached --check; then
        printf '%s\n' '  PASS: staged diff whitespace check'
    else
        fail 'staged diff whitespace check failed'
    fi
    overlap_count=$(count_nul_overlap "$staged_paths_file" "$unstaged_paths_file")
    if [ "$overlap_count" -gt 0 ]; then
        note "$overlap_count path(s) contain both staged and unstaged changes"
    fi
fi

printf '\nLightweight validation\n'
if git diff --check; then
    printf '%s\n' '  PASS: unstaged diff whitespace check'
else
    fail 'unstaged diff whitespace check failed'
fi
shell_failure=0
while IFS= read -r -d '' changed_path; do
    case "$changed_path" in
        *.sh)
            if [ -f "$changed_path" ] && ! bash -n "$changed_path"; then
                shell_failure=1
                fail "shell syntax check failed: $(quote_path "$changed_path")"
            fi
            ;;
    esac
done < "$changed_paths_file"
if [ "$shell_failure" -eq 0 ]; then
    printf '%s\n' '  PASS: changed shell syntax'
fi

agent_tooling_changed=0
while IFS= read -r -d '' changed_path; do
    case "$changed_path" in
        AGENTS.md|CLAUDE.md|.agents/*|.claude/skills/*|docs/agents/*|docs/agent-prompts/sentinel-review.md|scripts/agent/*|scripts/sentinel.sh)
            agent_tooling_changed=1
            ;;
    esac
done < "$changed_paths_file"
if [ "$agent_tooling_changed" -eq 1 ]; then
    if bash scripts/agent/validate-agent-tooling.sh; then
        printf '%s\n' '  PASS: agent-tooling validator'
    else
        fail 'agent-tooling validator failed'
    fi
else
    printf '%s\n' '  PASS: no agent-tooling structural validation required'
fi

exec 1>&3 2>&4
exec 3>&- 4>&-
cp "$body_file" "$checks_body_file"

report_timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z')
filename_timestamp=$(date '+%Y%m%d-%H%M%S')
persistence_error=''

if [ "$stdout_only" -eq 0 ]; then
    if [ -n "$requested_report" ]; then
        if ! resolve_report_path "$requested_report"; then
            persistence_error='requested report path must be a usable absolute file path outside the repository'
        fi
    else
        resolved_report_path="/tmp/cognivia-sentinel-$filename_timestamp.txt"
    fi

    if [ -z "$persistence_error" ]; then
        report_parent=${resolved_report_path%/*}
        report_stage=$(mktemp "$report_parent/.cognivia-sentinel-report.XXXXXX" 2>/dev/null) || persistence_error='could not prepare the requested report destination'
    fi
    if [ -z "$persistence_error" ]; then
        latest_stage=$(mktemp '/tmp/.cognivia-sentinel-latest.XXXXXX' 2>/dev/null) || persistence_error='could not prepare the stable latest-report destination'
    fi
fi

if [ -n "$persistence_error" ]; then
    failure_count=$((failure_count + 1))
    {
        printf '\nReport persistence\n'
        printf '  FAIL: %s; complete findings follow on stdout\n' "$persistence_error"
    } >> "$body_file"
fi

set_final_result
append_detailed_summary
build_complete_report

if [ "$stdout_only" -eq 1 ]; then
    cat "$complete_report_file"
    exit "$sentinel_exit"
fi

if [ -n "$persistence_error" ]; then
    printf 'Cognivia Sentinel: %s.\n' "$persistence_error" >&2
    cat "$complete_report_file"
    exit 1
fi

if ! cp "$complete_report_file" "$report_stage" 2>/dev/null || ! mv -f "$report_stage" "$resolved_report_path" 2>/dev/null; then
    cp "$checks_body_file" "$body_file"
    failure_count=$((failure_count + 1))
    printf '\nReport persistence\n  FAIL: report persistence failed; complete findings follow on stdout\n' >> "$body_file"
    set_final_result
    append_detailed_summary
    build_complete_report
    printf '%s\n' 'Cognivia Sentinel: report persistence failed; complete findings follow on stdout.' >&2
    cat "$complete_report_file"
    exit 1
fi
report_stage=''

if ! cp "$complete_report_file" "$latest_stage" 2>/dev/null || ! mv -f "$latest_stage" /tmp/cognivia-sentinel-latest.txt 2>/dev/null; then
    cp "$checks_body_file" "$body_file"
    failure_count=$((failure_count + 1))
    printf '\nReport persistence\n  FAIL: latest-report update failed; complete findings follow on stdout\n' >> "$body_file"
    set_final_result
    append_detailed_summary
    build_complete_report
    printf '%s\n' 'Cognivia Sentinel: latest-report update failed; complete findings follow on stdout.' >&2
    cat "$complete_report_file"
    exit 1
fi
latest_stage=''

if [ "$verbose" -eq 1 ]; then
    cat "$complete_report_file"
else
    print_concise_summary
fi

exit "$sentinel_exit"

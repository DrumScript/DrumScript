#!/usr/bin/env bash
# scripts/run_tests.sh
#
# Run the DrumScript test suite with per-file logging.
#
# Usage:
#   ./scripts/run_tests.sh                  # All unit tests, one file at a time
#   ./scripts/run_tests.sh --all-at-once    # All unit tests in a single pytest call
#   ./scripts/run_tests.sh --integration    # Also run integration tests (slow!)
#   ./scripts/run_tests.sh --everything     # Unit + integration
#   ./scripts/run_tests.sh --help           # Show this help
#
# Logs are written to logs/tests/<timestamp>/.

# Why no `set -e`:
#   We want to keep going even if a test file fails, so we can see ALL
#   failures in one run rather than stopping at the first.
# Why `set -u`:
#   Catches typos in variable names — referencing $UNDEFINED becomes an
#   immediate error rather than silently using empty string.
# Why `set -o pipefail`:
#   Without this, `pytest | tee` would always report success because tee
#   succeeds even when pytest fails. With pipefail, the pipeline's exit
#   code reflects the failed component.
set -u
set -o pipefail


# ----------------------------------------------------------------------
# Colours for human-readable output
# ----------------------------------------------------------------------
# tput is the portable way to get terminal escape codes. It returns empty
# strings on dumb terminals (like CI logs), so colours degrade gracefully.
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    GREEN=$(tput setaf 2)
    RED=$(tput setaf 1)
    YELLOW=$(tput setaf 3)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    GREEN="" RED="" YELLOW="" BOLD="" RESET=""
fi


# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
MODE="per-file"  # per-file | all-at-once
RUN_INTEGRATION=false

show_help() {
    # Pull the comment block at the top of this file as the help text.
    # The `^# ` prefix is stripped so the help reads naturally.
    sed -n '2,/^$/p' "$0" | sed 's/^# \?//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all-at-once)
            MODE="all-at-once"
            ;;
        --integration)
            RUN_INTEGRATION=true
            ;;
        --everything)
            RUN_INTEGRATION=true
            MODE="all-at-once"
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Run with --help to see usage." >&2
            exit 2
            ;;
    esac
    shift
done


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
# %Y-%m-%d_%H-%M-%S — sortable, no spaces or shell-special chars
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="scripts/logs/tests/${TIMESTAMP}"
mkdir -p "${LOG_DIR}"

SUMMARY_LOG="${LOG_DIR}/_summary.txt"

# Track results across files so we can print a summary at the end.
# Bash arrays are the cleanest way to do this without a temp file.
declare -a PASSED_FILES=()
declare -a FAILED_FILES=()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
log_to_summary() {
    # Write to both the summary log and stdout. Doubles as a "section
    # header" function so the summary file is readable on its own later.
    echo "$@" | tee -a "${SUMMARY_LOG}"
}

run_one_file() {
    # Run pytest on a single file and log to its own file in LOG_DIR.
    # Returns pytest's exit code.
    local test_file="$1"
    # basename strips the directory; %.* strips the .py extension.
    local basename
    basename=$(basename "${test_file}" .py)
    local log_file="${LOG_DIR}/${basename}.txt"

    echo
    echo "${BOLD}━━━ Running: ${test_file} ━━━${RESET}"

    # Why -v: verbose, shows each test name as it runs (useful in logs)
    # Why --tb=short: compact tracebacks, easier to skim
    # Why 2>&1: merge stderr so warnings/errors land in the log too
    pytest "${test_file}" -v --tb=short 2>&1 | tee "${log_file}"
    local exit_code=${PIPESTATUS[0]}  # exit code of pytest, NOT tee

    if [[ ${exit_code} -eq 0 ]]; then
        log_to_summary "  ${GREEN}✓ PASS${RESET}  ${test_file}"
        PASSED_FILES+=("${test_file}")
    else
        log_to_summary "  ${RED}✗ FAIL${RESET}  ${test_file}  (exit ${exit_code}, see ${log_file})"
        FAILED_FILES+=("${test_file}")
    fi

    return "${exit_code}"
}

# Resolve the script's location and cd to the project root so all paths
# below are reliable regardless of where the user invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.." || exit 1

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
log_to_summary "${BOLD}DrumScript test run${RESET}"
log_to_summary "Started: $(date)"
log_to_summary "Mode:    ${MODE}"
log_to_summary "Logs:    ${LOG_DIR}"
log_to_summary ""


# Discover unit-test files. Globbing in zsh + bash is portable here
# because we're sticking to simple wildcards (no extglob).
UNIT_FILES=(tests/unit/test_*.py)
INTEGRATION_FILES=(tests/integration/test_*.py)


if [[ "${MODE}" == "all-at-once" ]]; then
    # Single pytest invocation across the entire suite (or just unit).
    log_to_summary "${BOLD}Running all unit tests in one pytest call...${RESET}"
    log_file="${LOG_DIR}/unit_all.txt"

    if [[ "${RUN_INTEGRATION}" == "true" ]]; then
        # `pytest` with no markers runs everything including slow tests.
        pytest -v --tb=short 2>&1 | tee "${log_file}"
    else
        pytest -m "not slow" -v --tb=short 2>&1 | tee "${log_file}"
    fi
    overall_exit=${PIPESTATUS[0]}

    log_to_summary ""
    if [[ ${overall_exit} -eq 0 ]]; then
        log_to_summary "${GREEN}${BOLD}All tests passed.${RESET}"
    else
        log_to_summary "${RED}${BOLD}Some tests failed (exit ${overall_exit}).${RESET}"
        log_to_summary "Full log: ${log_file}"
    fi
    exit "${overall_exit}"
fi


# ----------------------------------------------------------------------
# per-file mode (default)
# ----------------------------------------------------------------------
log_to_summary "${BOLD}Unit tests${RESET}"
for test_file in "${UNIT_FILES[@]}"; do
    run_one_file "${test_file}" || true
    # || true so that `set -u` and pipefail don't kill the script
    # on the first failing file — we want to keep going.
done


if [[ "${RUN_INTEGRATION}" == "true" ]]; then
    log_to_summary ""
    log_to_summary "${BOLD}Integration tests${RESET}"
    log_to_summary "${YELLOW}Note: these are slow and may download Demucs models on first run.${RESET}"
    for test_file in "${INTEGRATION_FILES[@]}"; do
        run_one_file "${test_file}" || true
    done
fi


# ----------------------------------------------------------------------
# Final summary
# ----------------------------------------------------------------------
log_to_summary ""
log_to_summary "${BOLD}━━━ Summary ━━━${RESET}"
log_to_summary "Passed: ${#PASSED_FILES[@]}"
log_to_summary "Failed: ${#FAILED_FILES[@]}"

if [[ ${#FAILED_FILES[@]} -gt 0 ]]; then
    log_to_summary ""
    log_to_summary "${RED}Failed files:${RESET}"
    for f in "${FAILED_FILES[@]}"; do
        log_to_summary "  - ${f}"
    done
    log_to_summary ""
    log_to_summary "Per-file logs are in: ${LOG_DIR}/"
    exit 1
else
    log_to_summary ""
    log_to_summary "${GREEN}${BOLD}All test files passed.${RESET}"
    exit 0
fi

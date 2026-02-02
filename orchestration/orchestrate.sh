#!/bin/bash
# =============================================================================
# ORCHESTRATE.SH
# =============================================================================
# Runs inject-substrate.sh (which also runs tests) for all execution substrates
# and then grades the results.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SUBSTRATES_DIR="$PROJECT_ROOT/execution-substratrates"

# =============================================================================
# COLORS
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Substrate colors (cycle through for visual distinction)
SUBSTRATE_COLORS=(
    '\033[38;5;214m'  # Orange
    '\033[38;5;118m'  # Bright green
    '\033[38;5;147m'  # Light purple
    '\033[38;5;81m'   # Sky blue
    '\033[38;5;219m'  # Pink
    '\033[38;5;228m'  # Light yellow
    '\033[38;5;123m'  # Aqua
    '\033[38;5;183m'  # Lavender
    '\033[38;5;203m'  # Coral
    '\033[38;5;157m'  # Mint
    '\033[38;5;208m'  # Dark orange
    '\033[38;5;120m'  # Light green
)

echo ""
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║${NC}          ${BOLD}${WHITE}EXECUTION SUBSTRATE ORCHESTRATOR${NC}                  ${BOLD}${CYAN}║${NC}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# MENU: Select run mode
# =============================================================================

# Get list of substrates for the menu
SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
SUBSTRATES_ARRAY=($SUBSTRATES)
TOTAL_SUBSTRATES=${#SUBSTRATES_ARRAY[@]}

echo -e "${BOLD}${WHITE}Select an option:${NC}"
echo ""
echo -e "  ${RED}[C]${NC} ${BOLD}CLEAN${NC} all generated files from substrates"
echo -e "  ${GREEN}[A]${NC} Run ${BOLD}ALL${NC} substrates ($TOTAL_SUBSTRATES total)"
echo ""
echo -e "  ${YELLOW}Or select a specific substrate:${NC}"
echo ""

# Display substrates with numbers
INDEX=1
for substrate in $SUBSTRATES; do
    substrate_dir="$SUBSTRATES_DIR/$substrate"
    inject_script="$substrate_dir/inject-substrate.sh"
    if [ -f "$inject_script" ]; then
        echo -e "  ${CYAN}[$INDEX]${NC} $substrate"
    # else
    #   echo -e "  ${DIM}[$INDEX] $substrate (no inject-substrate.sh)${NC}"
    fi
    INDEX=$((INDEX + 1))
done
echo ""

# Read user input
read -p "Enter choice [C, A, or 1-$TOTAL_SUBSTRATES] (default: A): " USER_CHOICE

# Default to 'A' if user just presses Enter
if [ -z "$USER_CHOICE" ]; then
    USER_CHOICE="A"
fi

# Handle CLEAN option
if [[ "$USER_CHOICE" =~ ^[Cc]$ ]]; then
    echo ""
    echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${RED}║${NC}              ${BOLD}${WHITE}CLEANING ALL SUBSTRATES${NC}                       ${BOLD}${RED}║${NC}"
    echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    for substrate in $SUBSTRATES; do
        substrate_dir="$SUBSTRATES_DIR/$substrate"
        echo -e "${YELLOW}Cleaning ${substrate}...${NC}"

        # Try different clean methods in order of preference
        if [ -f "$substrate_dir/inject-into-${substrate}.py" ]; then
            # Most substrates have inject-into-*.py with --clean
            (cd "$substrate_dir" && python3 "inject-into-${substrate}.py" --clean 2>/dev/null) || true
        elif [ -f "$substrate_dir/clean.py" ]; then
            # YAML has a separate clean.py
            (cd "$substrate_dir" && python3 clean.py --clean 2>/dev/null) || true
        else
            echo -e "  ${DIM}No clean script found${NC}"
        fi
    done

    echo ""
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}CLEAN COMPLETE${NC}                                ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 0
fi

# Determine which substrates to run
RUN_SINGLE=""
if [[ "$USER_CHOICE" =~ ^[Aa]$ ]]; then
    echo ""
    echo -e "${GREEN}Running ALL substrates...${NC}"
    echo ""
elif [[ "$USER_CHOICE" =~ ^[0-9]+$ ]] && [ "$USER_CHOICE" -ge 1 ] && [ "$USER_CHOICE" -le "$TOTAL_SUBSTRATES" ]; then
    RUN_SINGLE="${SUBSTRATES_ARRAY[$((USER_CHOICE - 1))]}"
    echo ""
    echo -e "${GREEN}Running single substrate: ${BOLD}$RUN_SINGLE${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 1: Generate answer key and blank test from database
# -----------------------------------------------------------------------------
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 1:${NC} ${YELLOW}Generating answer key and blank test...${NC}              ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# Load test-orchestrator module
spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Run steps 1 and 2
answer_key = test_orch.generate_answer_key()
test_orch.generate_blank_test(answer_key)
"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Run inject-substrate.sh for each substrate
# -----------------------------------------------------------------------------
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 2:${NC} ${YELLOW}Running inject + test for each substrate...${NC}         ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Determine which substrates to process
if [ -n "$RUN_SINGLE" ]; then
    SUBSTRATES_TO_RUN="$RUN_SINGLE"
    TOTAL_TO_RUN=1
else
    SUBSTRATES_TO_RUN=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    TOTAL_TO_RUN=$(echo "$SUBSTRATES_TO_RUN" | wc -w | tr -d ' ')
fi

INJECT_RESULTS=""
COLOR_INDEX=0
CURRENT=0

# Array to store failed substrates (outputs stored in temp files)
FAILED_SUBSTRATES=""
FAILED_OUTPUTS_DIR=$(mktemp -d)
trap "rm -rf $FAILED_OUTPUTS_DIR" EXIT

for substrate in $SUBSTRATES_TO_RUN; do
    substrate_dir="$SUBSTRATES_DIR/$substrate"
    inject_script="$substrate_dir/inject-substrate.sh"
    CURRENT=$((CURRENT + 1))

    # Get color for this substrate
    COLOR="${SUBSTRATE_COLORS[$COLOR_INDEX]}"
    COLOR_INDEX=$(( (COLOR_INDEX + 1) % ${#SUBSTRATE_COLORS[@]} ))

    if [ -f "$inject_script" ]; then
        substrate_upper=$(echo "$substrate" | tr '[:lower:]' '[:upper:]')
        echo -e "${COLOR}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${COLOR}║${NC} ${BOLD}[$CURRENT/$TOTAL_TO_RUN]${NC} ${COLOR}▶ ${BOLD}${substrate_upper}${NC}"
        echo -e "${COLOR}╚══════════════════════════════════════════════════════════════╝${NC}"

        # Run script with real-time output AND capture for error reporting
        # Use tee to show output live while also saving to temp file
        INJECT_TEMP_FILE=$(mktemp)
        START_TIME=$(python3 -c "import time; print(time.time())")
        bash "$inject_script" 2>&1 | tee "$INJECT_TEMP_FILE" && INJECT_EXIT_CODE=0 || INJECT_EXIT_CODE=${PIPESTATUS[0]}
        END_TIME=$(python3 -c "import time; print(time.time())")
        ELAPSED_TIME=$(python3 -c "print($END_TIME - $START_TIME)")
        INJECT_OUTPUT=$(cat "$INJECT_TEMP_FILE")
        rm -f "$INJECT_TEMP_FILE"
        
        if [ $INJECT_EXIT_CODE -eq 0 ]; then
            INJECT_RESULTS="$INJECT_RESULTS$substrate:OK\n"
            echo -e "  ${GREEN}✓${NC} ${substrate}: ${GREEN}${BOLD}OK${NC}"
        else
            INJECT_RESULTS="$INJECT_RESULTS$substrate:FAILED\n"
            echo -e "  ${RED}✗${NC} ${substrate}: ${RED}${BOLD}FAILED TO EXECUTE${NC}"
            # Store failure information
            FAILED_SUBSTRATES="$FAILED_SUBSTRATES $substrate"
            echo "$INJECT_OUTPUT" > "$FAILED_OUTPUTS_DIR/$substrate.txt"
        fi

        # Grade this substrate immediately
        python3 -c "
import sys
import json
import os
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

with open(test_orch.ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

substrate = '$substrate'
inject_exit_code = $INJECT_EXIT_CODE
elapsed_seconds = $ELAPSED_TIME

# If inject failed, mark as error regardless of stale test-answers.json
if inject_exit_code != 0:
    grades = test_orch.grade_substrate(substrate, answer_key, None)
    grades['error'] = 'FAILED TO EXECUTE (inject-substrate.sh returned non-zero)'
    grades['execution_failed'] = True
else:
    answers_path = os.path.join(test_orch.SUBSTRATES_DIR, substrate, 'test-answers.json')
    if os.path.exists(answers_path):
        grades = test_orch.grade_substrate(substrate, answer_key, answers_path)
    else:
        grades = test_orch.grade_substrate(substrate, answer_key, None)
        grades['error'] = 'No test-answers.json'

# Add timing information
grades['elapsed_seconds'] = elapsed_seconds

test_orch.generate_substrate_report(substrate, grades)
test_orch.print_substrate_test_summary(substrate, grades)

# Save grades to temp file for final summary
import pickle
grades_file = os.path.join(test_orch.SUBSTRATES_DIR, substrate, '.grades.pkl')
with open(grades_file, 'wb') as f:
    pickle.dump(grades, f)
"
        # Add vertical spacing after each substrate for visual isolation
        printf '\n%.0s' {1..10}
    else
        echo -e "  ${YELLOW}○${NC} ${substrate}: ${DIM}SKIPPED (no inject-substrate.sh)${NC}"
        INJECT_RESULTS="$INJECT_RESULTS$substrate:SKIPPED\n"
    fi
done

# -----------------------------------------------------------------------------
# Step 3: Generate summary report
# -----------------------------------------------------------------------------
# Breathing room before summary
printf '\n%.0s' {1..5}
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 3:${NC} ${YELLOW}Generating summary report...${NC}                         ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
python3 -c "
import sys
import json
import os
import pickle
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Collect grades from temp files
run_single = '$RUN_SINGLE'
if run_single:
    substrates = [run_single]
else:
    substrates = test_orch.get_substrates()

all_grades = {}
for substrate in substrates:
    grades_file = os.path.join(test_orch.SUBSTRATES_DIR, substrate, '.grades.pkl')
    if os.path.exists(grades_file):
        with open(grades_file, 'rb') as f:
            all_grades[substrate] = pickle.load(f)
        os.remove(grades_file)  # Clean up

# Generate summary report and print final table
if run_single:
    # For single substrate, just print the summary table (no full report)
    test_orch.print_final_summary_table(all_grades)
else:
    test_orch.generate_summary_report(all_grades)
    test_orch.print_final_summary_table(all_grades)
"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Show Failed Substrates Summary (if any)
# -----------------------------------------------------------------------------
# Trim leading space from FAILED_SUBSTRATES
FAILED_SUBSTRATES=$(echo "$FAILED_SUBSTRATES" | xargs)
FAILED_COUNT=$(echo "$FAILED_SUBSTRATES" | wc -w | tr -d ' ')

if [ -n "$FAILED_SUBSTRATES" ]; then
    printf '\n%.0s' {1..3}
    echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${RED}║${NC}           ${BOLD}${WHITE}⚠️  FAILED TO EXECUTE ($FAILED_COUNT substrates)${NC}              ${BOLD}${RED}║${NC}"
    echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    for failed_substrate in $FAILED_SUBSTRATES; do
        failed_upper=$(echo "$failed_substrate" | tr '[:lower:]' '[:upper:]')
        echo -e "${RED}┌──────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${RED}│${NC} ${BOLD}${RED}✗ ${failed_upper}${NC} ${DIM}(FAILED TO EXECUTE)${NC}"
        echo -e "${RED}├──────────────────────────────────────────────────────────────┤${NC}"
        
        # Show the captured output (last 20 lines to keep it manageable)
        echo -e "${DIM}Output (last 20 lines):${NC}"
        if [ -f "$FAILED_OUTPUTS_DIR/$failed_substrate.txt" ]; then
            tail -20 "$FAILED_OUTPUTS_DIR/$failed_substrate.txt" | while IFS= read -r line; do
                echo -e "  ${DIM}│${NC} $line"
            done
        fi
        
        echo -e "${RED}└──────────────────────────────────────────────────────────────┘${NC}"
        echo ""
    done
    
    # List all failed substrates on one line for easy copy/paste
    echo -e "${RED}${BOLD}Failed substrates:${NC} $FAILED_SUBSTRATES"
    echo ""
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
if [ -n "$FAILED_SUBSTRATES" ]; then
    echo -e "${BOLD}${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${YELLOW}║${NC}         ${BOLD}${WHITE}ORCHESTRATION COMPLETE (WITH FAILURES)${NC}            ${BOLD}${YELLOW}║${NC}"
    echo -e "${BOLD}${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}ORCHESTRATION COMPLETE${NC}                       ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
fi
echo ""
if [ -n "$RUN_SINGLE" ]; then
    echo -e "${CYAN}Results written to:${NC}"
    echo -e "  ${DIM}•${NC} Per-substrate: ${WHITE}execution-substratrates/$RUN_SINGLE/test-results.md${NC}"
else
    echo -e "${CYAN}Results written to:${NC}"
    echo -e "  ${DIM}•${NC} Per-substrate: ${WHITE}execution-substratrates/*/test-results.md${NC}"
    echo -e "  ${DIM}•${NC} Summary:       ${WHITE}orchestration/all-tests-results.md${NC}"
fi
echo ""

# Exit with error code if any substrates failed
if [ -n "$FAILED_SUBSTRATES" ]; then
    echo -e "${RED}${BOLD}⚠️  $FAILED_COUNT substrate(s) failed to execute: $FAILED_SUBSTRATES${NC}"
    exit 1
fi

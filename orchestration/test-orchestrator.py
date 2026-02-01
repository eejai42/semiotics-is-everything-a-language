#!/usr/bin/env python3
# =============================================================================
# TEST ORCHESTRATOR
# =============================================================================
# Generic test framework for evaluating execution substrates.
# Compares field-by-field - no domain-specific logic in the evaluation.
# =============================================================================

import json
import os
import subprocess
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database connection
DB_CONNECTION = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/wikidata-language-candidates"
)

# View to query for answer key
VIEW_NAME = "vw_language_candidates"

# Primary key field (used for matching records between answer key and test answers)
PRIMARY_KEY = "language_candidate_id"

# Computed columns to strip for blank test
# (These are the fields that substrates must compute)
# Note: has_grammar was removed - it's now a raw field in the rulebook
COMPUTED_COLUMNS = [
    "family_feud_mismatch",
    "family_fued_question",
    "top_family_feud_answer",
    "relationship_to_concept",
    "is_open_closed_world_conflicted",
]

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TESTING_DIR = os.path.join(PROJECT_ROOT, "testing")
SUBSTRATES_DIR = os.path.join(PROJECT_ROOT, "execution-substratrates")

ANSWER_KEY_PATH = os.path.join(TESTING_DIR, "answer-key.json")
BLANK_TEST_PATH = os.path.join(TESTING_DIR, "blank-test.json")
SUMMARY_PATH = os.path.join(SCRIPT_DIR, "all-tests-results.md")

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Extended 256-color palette for gradients and backgrounds
SKY_BLUE_BG = "\033[48;5;117m"  # Sky blue background
DARK_TEXT = "\033[38;5;232m"    # Near-black text for contrast
GREEN_BG = "\033[48;5;22m"      # Dark green background for pass rows
RED_BG = "\033[48;5;52m"        # Dark red background for fail rows
WHITE_TEXT = "\033[97m"         # White text
STRIKETHROUGH = "\033[9m"       # Strikethrough text
DIM = "\033[2m"                 # Dim text


def get_score_color(score: float) -> str:
    """
    Returns ANSI color code for a score using a red->yellow->green gradient.
    0% = pure red, 50% = yellow, 100% = pure green
    Uses 256-color palette for smooth gradient.
    """
    if score >= 100:
        return "\033[38;5;46m"   # Bright green
    elif score >= 90:
        return "\033[38;5;82m"   # Light green
    elif score >= 80:
        return "\033[38;5;118m"  # Yellow-green
    elif score >= 70:
        return "\033[38;5;154m"  # More yellow-green
    elif score >= 60:
        return "\033[38;5;190m"  # Yellow-ish green
    elif score >= 50:
        return "\033[38;5;226m"  # Yellow
    elif score >= 40:
        return "\033[38;5;220m"  # Orange-yellow
    elif score >= 30:
        return "\033[38;5;214m"  # Orange
    elif score >= 20:
        return "\033[38;5;208m"  # Dark orange
    elif score >= 10:
        return "\033[38;5;202m"  # Red-orange
    else:
        return "\033[38;5;196m"  # Pure red


# =============================================================================
# STEP 1: Generate Answer Key from Postgres
# =============================================================================

def generate_answer_key():
    """Query the view and export all data (including computed columns) to answer-key.json"""
    print(f"Step 1: Generating answer key from {VIEW_NAME}...", flush=True)

    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(f"SELECT * FROM {VIEW_NAME} ORDER BY {PRIMARY_KEY}")
        rows = cur.fetchall()

        # Convert to list of dicts (RealDictCursor returns dict-like rows)
        answer_key = [dict(row) for row in rows]

        # Write to file
        with open(ANSWER_KEY_PATH, 'w') as f:
            json.dump(answer_key, f, indent=2, default=str)

        print(f"  -> Exported {len(answer_key)} records to {ANSWER_KEY_PATH}", flush=True)

        cur.close()
        conn.close()

        return answer_key

    except Exception as e:
        print(f"  ERROR: Failed to connect to database: {e}", flush=True)
        sys.exit(1)


# =============================================================================
# STEP 2: Generate Blank Test (null placeholders for computed columns)
# =============================================================================

def generate_blank_test(answer_key):
    """Set computed columns to null in blank test (keeps structure, clears values)"""
    print(f"Step 2: Generating blank test (nulling {len(COMPUTED_COLUMNS)} computed columns)...", flush=True)

    blank_test = []
    for record in answer_key:
        blank_record = dict(record)
        # Set computed columns to null (placeholder for substrate to fill in)
        for col in COMPUTED_COLUMNS:
            blank_record[col] = None
        blank_test.append(blank_record)

    with open(BLANK_TEST_PATH, 'w') as f:
        json.dump(blank_test, f, indent=2, default=str)

    print(f"  -> Exported {len(blank_test)} records to {BLANK_TEST_PATH}", flush=True)
    print(f"  -> Nulled columns: {', '.join(COMPUTED_COLUMNS)}", flush=True)

    return blank_test


# =============================================================================
# STEP 3: Run Each Substrate's Test
# =============================================================================

def get_substrates():
    """Get list of substrate directories"""
    substrates = []
    if os.path.isdir(SUBSTRATES_DIR):
        for name in sorted(os.listdir(SUBSTRATES_DIR)):
            path = os.path.join(SUBSTRATES_DIR, name)
            if os.path.isdir(path) and not name.startswith('.'):
                substrates.append(name)
    return substrates


def run_substrate_test(substrate_name):
    """Run a substrate's take-test.sh and return path to test-answers.json"""
    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    script_path = os.path.join(substrate_dir, "take-test.sh")
    answers_path = os.path.join(substrate_dir, "test-answers.json")

    if not os.path.exists(script_path):
        return None, f"No take-test.sh found"

    try:
        result = subprocess.run(
            ["bash", script_path],
            cwd=substrate_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return None, f"Script failed: {result.stderr}"

        if not os.path.exists(answers_path):
            return None, f"No test-answers.json generated"

        return answers_path, None

    except subprocess.TimeoutExpired:
        return None, "Script timed out"
    except Exception as e:
        return None, str(e)


def run_and_grade_all_substrates(answer_key):
    """Run and grade each substrate, showing results immediately after each test"""
    print(f"Step 3: Running and grading tests for each substrate...", flush=True)
    print(flush=True)

    substrates = get_substrates()
    print(f"  Found {len(substrates)} substrates: {', '.join(substrates)}", flush=True)
    print(flush=True)

    all_grades = {}

    for i, substrate in enumerate(substrates, 1):
        # Print substrate header (flush immediately so it appears before the test runs)
        print(f"  [{i}/{len(substrates)}] Testing {substrate}...", flush=True)

        # Run the test
        answers_path, error = run_substrate_test(substrate)

        # Grade the results
        grades = grade_substrate(substrate, answer_key, answers_path)
        if error:
            grades["error"] = error

        all_grades[substrate] = grades

        # Generate the report file
        generate_substrate_report(substrate, grades)

        # Print the summary box immediately
        print_substrate_test_summary(substrate, grades)
        
        # Add vertical spacing after each substrate for visual isolation
        print("\n" * 10, flush=True)

    return all_grades


def grade_all_substrates(answer_key, substrate_results):
    """
    Grade all substrates and generate reports.
    Used by orchestrate.sh which handles running tests separately.
    """
    all_grades = {}

    for substrate_name, run_result in substrate_results.items():
        answers_path = run_result.get("answers_path")

        grades = grade_substrate(substrate_name, answer_key, answers_path)

        if run_result.get("error"):
            grades["error"] = run_result["error"]

        all_grades[substrate_name] = grades

        generate_substrate_report(substrate_name, grades)

        # Print detailed test summary for this substrate
        print_substrate_test_summary(substrate_name, grades)

    return all_grades


# =============================================================================
# STEP 4: Grade Each Substrate (Generic Field-by-Field Comparison)
# =============================================================================

def load_json(path):
    """Load JSON file, return empty list if error"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return []


def compare_values(expected, actual):
    """Compare two values, handling type differences"""
    # Convert both to strings for comparison (handles int vs str, etc.)
    return str(expected) == str(actual)


def grade_substrate(substrate_name, answer_key, answers_path):
    """
    Compare substrate's answers against answer key.
    Returns dict with detailed results.

    THIS IS GENERIC - no domain-specific logic.
    Just compares field-by-field whatever is in the JSON.
    """
    results = {
        "substrate": substrate_name,
        "total_records": len(answer_key),
        "total_fields_tested": 0,
        "fields_passed": 0,
        "fields_failed": 0,
        "failures": [],
        "error": None
    }

    if not answers_path:
        results["error"] = "No answers file"
        return results

    test_answers = load_json(answers_path)

    if not test_answers:
        results["error"] = "Could not load answers or empty file"
        return results

    # Index test answers by primary key for lookup
    answers_by_pk = {}
    for record in test_answers:
        pk = record.get(PRIMARY_KEY)
        if pk is not None:
            answers_by_pk[str(pk)] = record

    # Compare each record, field by field
    for expected_record in answer_key:
        pk = str(expected_record.get(PRIMARY_KEY))
        actual_record = answers_by_pk.get(pk, {})

        # Only check computed columns (those are what substrates must produce)
        for field in COMPUTED_COLUMNS:
            results["total_fields_tested"] += 1

            expected_val = expected_record.get(field)
            actual_val = actual_record.get(field)

            if compare_values(expected_val, actual_val):
                results["fields_passed"] += 1
            else:
                results["fields_failed"] += 1
                results["failures"].append({
                    PRIMARY_KEY: pk,
                    "field": field,
                    "expected": expected_val,
                    "actual": actual_val
                })

    return results


def generate_substrate_report(substrate_name, results):
    """Generate test-results.md for a substrate"""
    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    report_path = os.path.join(substrate_dir, "test-results.md")

    total = results["total_fields_tested"]
    passed = results["fields_passed"]
    failed = results["fields_failed"]
    score = (passed / total * 100) if total > 0 else 0

    lines = [
        f"# Test Results: {substrate_name}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Fields Tested | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Score | {score:.1f}% |",
        "",
    ]

    if results.get("error"):
        lines.extend([
            "## Error",
            "",
            f"```",
            results["error"],
            f"```",
            "",
        ])

    if results["failures"]:
        lines.extend([
            "## Failures",
            "",
            f"| {PRIMARY_KEY} | Field | Expected | Actual |",
            f"|---------------|-------|----------|--------|",
        ])

        # Show first 50 failures to keep report manageable
        for failure in results["failures"][:50]:
            pk = failure[PRIMARY_KEY]
            field = failure["field"]
            expected = str(failure["expected"])[:40]
            actual = str(failure["actual"])[:40]
            lines.append(f"| {pk} | {field} | {expected} | {actual} |")

        if len(results["failures"]) > 50:
            lines.append(f"| ... | ... | ({len(results['failures']) - 50} more failures) | ... |")

        lines.append("")

    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))

    return report_path


def print_substrate_test_summary(substrate_name, grades):
    """Print a per-test breakdown for a substrate to console"""
    total = grades["total_fields_tested"]
    passed = grades["fields_passed"]
    failed = grades["fields_failed"]
    execution_failed = grades.get("execution_failed", False) or (grades.get("error") and total == 0)
    score = (passed / total * 100) if total > 0 else 0

    # Determine status with color
    if execution_failed:
        status_plain = "FAILED TO COMPUTE"
    elif grades.get("error"):
        status_plain = "ERROR"
    elif failed == 0:
        status_plain = "PASS"
    else:
        status_plain = "FAIL"

    # Get gradient color for score
    score_color = get_score_color(score)

    # Print header with sky-blue background (or red for execution failures)
    box_width = 52
    if execution_failed:
        header_bg = RED_BG
        header_text = WHITE_TEXT
    else:
        header_bg = SKY_BLUE_BG
        header_text = DARK_TEXT

    print(f"  {header_bg}{header_text}┌{'─' * box_width}┐{RESET}", flush=True)
    print(f"  {header_bg}{header_text}│{BOLD} {substrate_name.upper():^{box_width - 2}} {RESET}{header_bg}{header_text}│{RESET}", flush=True)
    
    # Score line
    if execution_failed:
        score_text = f"Score: --/-- (--%) - {status_plain}"
        print(f"  {header_bg}{header_text}│ {RED}{BOLD}{score_text:^{box_width - 2}}{RESET}{header_bg}{header_text} │{RESET}", flush=True)
    else:
        score_text = f"Score: {passed}/{total} ({score:.1f}%) - {status_plain}"
        print(f"  {header_bg}{header_text}│ {score_color}{BOLD}{score_text:^{box_width - 2}}{RESET}{header_bg}{header_text} │{RESET}", flush=True)
    print(f"  {header_bg}{header_text}├{'─' * box_width}┤{RESET}", flush=True)

    # Group failures by field
    failures_by_field = {}
    for failure in grades.get("failures", []):
        field = failure.get("field")
        if field not in failures_by_field:
            failures_by_field[field] = 0
        failures_by_field[field] += 1

    # Print per-test results with colored row backgrounds
    for col in COMPUTED_COLUMNS:
        col_failures = failures_by_field.get(col, 0)
        col_total = grades["total_records"]

        if execution_failed:
            # Execution failed - show -- for all
            row_bg = RED_BG
            icon = "✗"
            result_padded = "-- (NO DATA)"
            text_color = RED
        elif col_failures == 0 and not grades.get("error"):
            # Passing test - green background
            row_bg = GREEN_BG
            icon = "✓"
            result_padded = "PASS"
            text_color = GREEN
        else:
            # Failing test - red background
            row_bg = RED_BG
            icon = "✗"
            result_padded = f"FAIL ({col_failures}/{col_total})"
            text_color = RED

        # Truncate column name if too long
        col_display = col[:30] if len(col) > 30 else col
        # Render the entire row with colored background
        row_content = f"  {icon} {col_display:<32} {result_padded:>12} "
        print(f"  {row_bg}{WHITE_TEXT}│{row_content}│{RESET}", flush=True)

    print(f"  {header_bg}{header_text}└{'─' * box_width}┘{RESET}", flush=True)
    print(flush=True)


# =============================================================================
# STEP 4: Generate Summary Report
# =============================================================================

def generate_summary_report(all_grades):
    """Generate all-tests-results.md with summary of all substrates"""
    print(f"Step 4: Generating summary report...", flush=True)

    lines = [
        "# Test Orchestrator Results",
        "",
        "## Configuration",
        "",
        f"- **View:** `{VIEW_NAME}`",
        f"- **Primary Key:** `{PRIMARY_KEY}`",
        f"- **Computed Columns:** {len(COMPUTED_COLUMNS)}",
        "",
        "## Summary by Substrate",
        "",
        "| Substrate | Passed | Failed | Total | Score | Status |",
        "|-----------|--------|--------|-------|-------|--------|",
    ]

    total_passed = 0
    total_failed = 0
    total_tests = 0

    for substrate_name in sorted(all_grades.keys()):
        grades = all_grades[substrate_name]

        passed = grades["fields_passed"]
        failed = grades["fields_failed"]
        total = grades["total_fields_tested"]
        score = (passed / total * 100) if total > 0 else 0

        total_passed += passed
        total_failed += failed
        total_tests += total

        if grades.get("error"):
            status = f"ERROR: {grades['error'][:30]}"
        elif failed == 0:
            status = "PASS"
        else:
            status = "FAIL"

        lines.append(f"| {substrate_name} | {passed} | {failed} | {total} | {score:.1f}% | {status} |")

    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0

    lines.extend([
        "",
        "## Overall Statistics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Substrates | {len(all_grades)} |",
        f"| Total Fields Tested | {total_tests} |",
        f"| Total Passed | {total_passed} |",
        f"| Total Failed | {total_failed} |",
        f"| Overall Score | {overall_score:.1f}% |",
        "",
    ])

    # Summary by Test (computed column)
    lines.extend([
        "## Summary by Test",
        "",
        "| Test (Computed Column) | Substrates Passing | Substrates Failing | Pass Rate |",
        "|------------------------|--------------------|--------------------|-----------|",
    ])

    # Calculate per-test statistics
    for col in COMPUTED_COLUMNS:
        passing_substrates = []
        failing_substrates = []

        for substrate_name in sorted(all_grades.keys()):
            grades = all_grades[substrate_name]
            # Count failures for this specific column
            col_failures = [f for f in grades.get("failures", []) if f.get("field") == col]

            if len(col_failures) == 0 and not grades.get("error"):
                passing_substrates.append(substrate_name)
            else:
                failing_substrates.append(substrate_name)

        total_substrates = len(all_grades)
        pass_rate = (len(passing_substrates) / total_substrates * 100) if total_substrates > 0 else 0

        lines.append(f"| `{col}` | {len(passing_substrates)} | {len(failing_substrates)} | {pass_rate:.1f}% |")

    lines.extend([
        "",
        "### Test Details",
        "",
    ])

    # Detailed breakdown for each test
    for col in COMPUTED_COLUMNS:
        passing_substrates = []
        failing_substrates = []

        for substrate_name in sorted(all_grades.keys()):
            grades = all_grades[substrate_name]
            col_failures = [f for f in grades.get("failures", []) if f.get("field") == col]

            if len(col_failures) == 0 and not grades.get("error"):
                passing_substrates.append(substrate_name)
            else:
                failing_substrates.append(substrate_name)

        lines.append(f"**`{col}`**")
        if passing_substrates:
            lines.append(f"- Passing: {', '.join(passing_substrates)}")
        if failing_substrates:
            lines.append(f"- Failing: {', '.join(failing_substrates)}")
        lines.append("")

    lines.extend([
        "## Computed Columns Being Tested",
        "",
    ])

    for col in COMPUTED_COLUMNS:
        lines.append(f"- `{col}`")

    lines.extend([
        "",
        "---",
        "",
        "*Generated by test-orchestrator.py*",
    ])

    with open(SUMMARY_PATH, 'w') as f:
        f.write('\n'.join(lines))

    print(f"  -> Summary written to {SUMMARY_PATH}", flush=True)
    print(f"  -> Overall: {total_passed}/{total_tests} ({overall_score:.1f}%)", flush=True)

    return total_passed, total_failed, total_tests, overall_score


def split_column_name(name, max_lines=3):
    """Split a column name by underscores into multiple lines, centered.

    Ensures at least max_lines lines are returned (padded with empty strings).
    """
    parts = name.replace('_', '\n').split('\n')
    # Pad to ensure we have at least max_lines
    while len(parts) < max_lines:
        parts.insert(0, '')  # Add empty lines at the beginning
    return parts[-max_lines:]  # Return only the last max_lines


def print_final_summary_table(all_grades):
    """Print a final summary table to console showing all substrates"""
    print(flush=True)
    print("=" * 70, flush=True)
    print(f"{BOLD}FINAL RESULTS SUMMARY{RESET}", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)

    # Calculate column widths
    substrate_width = 15
    test_width = 12  # Wider to accommodate longer column name parts
    status_width = 18  # Wide enough for "FAILED TO COMPUTE"

    # Build multi-line header (3 lines for column names)
    header_lines = [[], [], []]
    col_name_parts = []

    for col in COMPUTED_COLUMNS:
        parts = split_column_name(col, max_lines=3)
        col_name_parts.append(parts)

    # Print 3-line header
    for line_idx in range(3):
        if line_idx == 1:
            # Middle line includes "Substrate" label
            line = f"{'Substrate':<{substrate_width}}"
        else:
            line = f"{'':<{substrate_width}}"

        for parts in col_name_parts:
            line += f" │ {parts[line_idx]:^{test_width}}"

        # Add Total/Score/Status on middle line only
        if line_idx == 1:
            line += f" │ {'Total':^8} │ {'Score':^7} │ {'Status':^{status_width}}"
        else:
            line += f" │ {'':^8} │ {'':^7} │ {'':^{status_width}}"

        print(line, flush=True)

    # Calculate header width for separator
    header_width = substrate_width + (len(COMPUTED_COLUMNS) * (test_width + 3)) + 8 + 3 + 7 + 3 + status_width + 3
    print("─" * header_width, flush=True)

    # Data rows
    total_passed = 0
    total_failed = 0
    failed_substrates = []

    # Sort substrates by score (highest to lowest)
    def get_substrate_score(name):
        grades = all_grades[name]
        passed = grades["fields_passed"]
        total = grades["total_fields_tested"]
        return (passed / total * 100) if total > 0 else 0

    for substrate_name in sorted(all_grades.keys(), key=get_substrate_score, reverse=True):
        grades = all_grades[substrate_name]
        has_error = grades.get("error") is not None
        execution_failed = grades.get("execution_failed", False) or (has_error and grades.get("total_fields_tested", 0) == 0)

        # Track failed substrates (execution failures only)
        if execution_failed:
            failed_substrates.append(substrate_name)

        # Group failures by field
        failures_by_field = {}
        for failure in grades.get("failures", []):
            field = failure.get("field")
            if field not in failures_by_field:
                failures_by_field[field] = 0
            failures_by_field[field] += 1

        # Print substrate name (with strikethrough if execution failed)
        if execution_failed:
            print(f"{RED}{STRIKETHROUGH}{substrate_name:<{substrate_width}}{RESET}", end="", flush=True)
        else:
            print(f"{substrate_name:<{substrate_width}}", end="", flush=True)

        substrate_passed = 0
        substrate_total = 0

        for col in COMPUTED_COLUMNS:
            col_failures = failures_by_field.get(col, 0)
            col_total = grades["total_records"]

            substrate_passed += (col_total - col_failures)
            substrate_total += col_total

            if execution_failed:
                # Show -- for execution failures (we have no data)
                cell_str = "--"
                padding = (test_width - len(cell_str)) // 2
                print(f" │ {' ' * padding}{RED}{DIM}{cell_str}{RESET}{' ' * (test_width - padding - len(cell_str))}", end="", flush=True)
            elif col_failures == 0:
                # Center the checkmark with padding
                padding = (test_width - 1) // 2
                print(f" │ {' ' * padding}{GREEN}✓{RESET}{' ' * (test_width - padding - 1)}", end="", flush=True)
            else:
                # Center the failure count with padding
                cell_str = str(col_failures)
                padding = (test_width - len(cell_str)) // 2
                print(f" │ {' ' * padding}{RED}{cell_str}{RESET}{' ' * (test_width - padding - len(cell_str))}", end="", flush=True)

        # For execution failures, don't count towards totals
        if not execution_failed:
            total_passed += substrate_passed
            total_failed += (substrate_total - substrate_passed)

        passed = grades["fields_passed"]
        total = grades["total_fields_tested"]
        score = (passed / total * 100) if total > 0 else 0

        # Use gradient color for score
        score_color = get_score_color(score)

        # Status column
        if execution_failed:
            status_text = "FAILED TO COMPUTE"
            # Show --/-- for total since we have no data
            print(f" │ {'--':>3}/{'--':<3} │ {RED}{DIM}{'--':>5}%{RESET} │ {RED}{BOLD}{status_text:^{status_width}}{RESET}", flush=True)
        elif grades["fields_failed"] == 0:
            status_text = "PASS"
            print(f" │ {passed:>3}/{total:<3} │ {score_color}{score:>5.1f}%{RESET} │ {GREEN}{status_text:^{status_width}}{RESET}", flush=True)
        else:
            status_text = "PARTIAL"
            print(f" │ {passed:>3}/{total:<3} │ {score_color}{score:>5.1f}%{RESET} │ {YELLOW}{status_text:^{status_width}}{RESET}", flush=True)

    print("─" * header_width, flush=True)

    # Overall totals
    overall_total = total_passed + total_failed
    overall_score = (total_passed / overall_total * 100) if overall_total > 0 else 0
    print(f"{BOLD}{'OVERALL':<{substrate_width}}{RESET}", end="", flush=True)
    for _ in COMPUTED_COLUMNS:
        print(f" │ {'':^{test_width}}", end="", flush=True)
    print(f" │ {total_passed:>3}/{overall_total:<3} │ {BOLD}{overall_score:>5.1f}%{RESET} │ {' ':^{status_width}}", flush=True)
    print(flush=True)

    # Print failed substrates summary if any
    if failed_substrates:
        print(f"{RED}{'─' * 70}{RESET}", flush=True)
        print(f"{RED}{BOLD}⚠️  FAILED TO EXECUTE ({len(failed_substrates)} substrates):{RESET}", flush=True)
        print(flush=True)
        for substrate_name in failed_substrates:
            error_msg = all_grades[substrate_name].get("error", "Unknown error")
            print(f"  {RED}✗{RESET} {BOLD}{substrate_name}{RESET}: {DIM}{error_msg}{RESET}", flush=True)
        print(flush=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60, flush=True)
    print("TEST ORCHESTRATOR", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Step 1: Generate answer key from Postgres
    answer_key = generate_answer_key()
    print(flush=True)

    # Step 2: Generate blank test
    generate_blank_test(answer_key)
    print(flush=True)

    # Step 3: Run and grade each substrate (shows summary after each test)
    all_grades = run_and_grade_all_substrates(answer_key)
    print(flush=True)

    # Step 4: Generate summary report
    # Breathing room before summary
    print("\n" * 5, flush=True)
    generate_summary_report(all_grades)
    print(flush=True)

    # Step 5: Print final summary table to console
    print_final_summary_table(all_grades)

    print("=" * 60, flush=True)
    print("DONE", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()

import re
from typing import List, Optional
from models.document_models import TestCase
from ingestion.document import DocumentContent


def clean_text(text) -> str:
    """
    Clean unnecessary whitespace from text.
    """
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_test_case_id(text: str) -> Optional[str]:
    """
    Detect common test case ID formats.
    """
    patterns = [
        r"\bTC[-_ ]?\d+\b",
        r"\bTEST[-_ ]?\d+\b",
        r"\bTESTCASE[-_ ]?\d+\b",
        r"\bTest Case\s+\d+\b",
        r"\bT[-_ ]?\d+\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group().strip()

    return None


def parse_table_lines(lines: List[str]):
    """
    Split sequential table lines into steps and expected results.
    """
    step_numbers = []
    text_lines = []

    for line in lines:
        cleaned = clean_text(line)
        if not cleaned:
            continue

        # Check if it is a pure step number (e.g., "1.", "2.")
        if re.match(r"^\d+\.$", cleaned):
            step_numbers.append(cleaned)
        else:
            text_lines.append(cleaned)

    steps = []
    expected = []

    n = len(step_numbers)
    if n > 0 and len(text_lines) == 2 * n:
        steps = text_lines[:n]
        expected = text_lines[n:]
    else:
        for line in text_lines:
            match = re.match(r"^(\d+\.)\s+(.*)$", line)
            if match:
                content = match.group(2).strip()
                parts = re.split(r"\s{2,}", content)
                if len(parts) >= 2:
                    steps.append(parts[0])
                    expected.append(parts[1])
                else:
                    steps.append(content)
            else:
                parts = re.split(r"\s{2,}", line)
                if len(parts) >= 2:
                    steps.append(parts[0])
                    expected.append(parts[1])
                else:
                    steps.append(line)

    return steps, expected


def parse_test_case_segment(
    segment_text: str,
    tc_id: str,
    pre_title: str,
    file_name: str,
    base_location: str
) -> TestCase:
    """
    Parse a partitioned text segment for a test case.
    """
    lines = [
        clean_text(line)
        for line in segment_text.splitlines()
        if clean_text(line)
    ]

    title = pre_title
    description = ""
    steps = []
    expected = []
    status = None

    # Fallback title if not found from pre-lines
    if not title and lines:
        first_line = lines[0]
        temp = re.sub(
            r"\b" + re.escape(tc_id) + r"\b",
            "",
            first_line,
            flags=re.IGNORECASE
        )
        temp = temp.strip("-:.\s ")
        if temp and len(temp) > 3:
            title = temp

    in_table = False
    table_lines = []

    for line in lines:
        lower_line = line.lower()

        # 1. Detect step table start trigger
        if (
            "step no." in lower_line
            or "execution description" in lower_line
            or "procedure result" in lower_line
        ):
            in_table = True
            continue

        # 2. Detect step table end triggers
        elif in_table and any(
            k in lower_line
            for k in ["comments", "passed", "failed", "not executed"]
        ):
            t_steps, t_exp = parse_table_lines(table_lines)
            steps.extend(t_steps)
            expected.extend(t_exp)
            table_lines = []
            in_table = False

        # 3. Prerequisites
        elif "pre-requisite" in lower_line or "precondition" in lower_line:
            prereq = re.sub(
                r"^(?:pre-requisite|precondition)[:\s]*",
                "",
                line,
                flags=re.IGNORECASE
            ).strip()
            if prereq:
                description += " Prereq: " + prereq

        # 4. Description / Objective
        elif "objective" in lower_line or "description" in lower_line:
            desc_text = re.sub(
                r"^(?:objective|description)[:\s]*",
                "",
                line,
                flags=re.IGNORECASE
            ).strip()
            if desc_text:
                description += " " + desc_text

        # Status Check (always evaluated)
        if "passed" in lower_line or "failed" in lower_line:
            if "passed" in lower_line:
                status = "Passed"
            elif "failed" in lower_line:
                status = "Failed"

        # Accumulate table rows if inside a table block (always evaluated)
        if in_table:
            # Skip page markers inside table rows
            if "page" in lower_line or "test document" in lower_line:
                continue
            table_lines.append(line)

    # Process remaining table lines if segment ended inside table
    if in_table and table_lines:
        t_steps, t_exp = parse_table_lines(table_lines)
        steps.extend(t_steps)
        expected.extend(t_exp)

    steps_str = "\n".join(steps).strip()
    expected_str = "\n".join(expected).strip()
    description = description.strip()

    if not title:
        title = f"Test Case {tc_id}"

    return TestCase(
        id=tc_id,
        title=title,
        description=description,
        steps=steps_str,
        expected_result=expected_str,
        actual_result=None,
        status=status,
        source_file=file_name,
        source_location=base_location
    )


def extract_test_cases_from_text_block(
    text: str, file_name: str
) -> List[TestCase]:
    """
    Extract test cases from plain text using logical segment block partitioning.
    """
    if not text:
        return []

    patterns = [
        r"\bTC[-_ ]?\d+\b",
        r"\bTEST[-_ ]?\d+\b",
        r"\bTESTCASE[-_ ]?\d+\b",
        r"\bTest Case\s+\d+\b",
        r"\bT[-_ ]?\d+\b"
    ]

    matches = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matches.append((m.start(), m.end(), m.group()))

    matches.sort(key=lambda x: x[0])

    filtered_matches = []
    last_end = -1
    for start, end, val in matches:
        if start >= last_end:
            filtered_matches.append((start, end, val))
            last_end = end

    test_cases = []
    if not filtered_matches:
        return []

    for idx, (start, end, val) in enumerate(filtered_matches):
        seg_start = start
        seg_end = (
            filtered_matches[idx + 1][0]
            if idx + 1 < len(filtered_matches)
            else len(text)
        )

        segment = text[seg_start:seg_end]

        # Detect PDF page number dynamically from headers
        page_num = 1
        page_match = list(re.finditer(r"--- PAGE (\d+) ---", text[:start]))
        if page_match:
            page_num = int(page_match[-1].group(1))

        location = f"Page {page_num}"

        # Look backwards to find the title of the test case
        pre_start = max(0, start - 200)
        pre_text = text[pre_start:start]
        pre_lines = [
            clean_text(l)
            for l in pre_text.splitlines()
            if clean_text(l)
        ]

        title = ""
        if pre_lines:
            for line in reversed(pre_lines):
                # Search for section numbers or short lines, excluding metadata
                if re.search(r"^\d+(?:\.\d+)*\s+\w+", line) or (
                    5 < len(line) < 50
                    and not any(
                        k in line.lower()
                        for k in [
                            "use case",
                            "actor",
                            "description",
                            "trigger",
                            "precondition",
                            "page",
                            "test case id",
                            "test case",
                            "test date",
                            "reviewed",
                            "version",
                            "revision"
                        ]
                    )
                ):
                    title = line
                    title = re.sub(r"^\d+(?:\.\d+)*\s*", "", title)
                    title = title.strip("-:.\s ")
                    break

        tc = parse_test_case_segment(segment, val, title, file_name, location)
        if tc:
            test_cases.append(tc)

    return test_cases


def extract_test_cases_from_tables(
    document: DocumentContent
) -> List[TestCase]:
    """
    Extract test cases from tabular structures.
    """
    test_cases = []

    for table_idx, table in enumerate(document.tables, start=1):
        rows = table.get("rows", [])
        columns = table.get("columns", [])
        table_name = table.get("name", f"Table {table_idx}")

        if not rows:
            continue

        headers = [clean_text(h).lower() for h in columns]

        id_col_idx = -1
        title_col_idx = -1
        desc_col_idx = -1
        steps_col_idx = -1
        expected_col_idx = -1
        actual_col_idx = -1
        status_col_idx = -1

        # Semantic column header mapping
        for col_idx, header in enumerate(headers):
            if "id" in header and (
                "test" in header or "tc" in header or "case" in header
            ):
                id_col_idx = col_idx
            elif "id" in header and id_col_idx == -1:
                id_col_idx = col_idx
            elif (
                "title" in header
                or "name" in header
                or "case name" in header
            ):
                title_col_idx = col_idx
            elif (
                "description" in header
                or "objective" in header
                or "scenario" in header
                or "summary" in header
            ):
                desc_col_idx = col_idx
            elif (
                "step" in header
                or "procedure" in header
                or "action" in header
            ):
                steps_col_idx = col_idx
            elif (
                "expected" in header
                or "expected result" in header
                or "expected output" in header
            ):
                expected_col_idx = col_idx
            elif (
                "actual" in header
                or "actual result" in header
                or "actual output" in header
            ):
                actual_col_idx = col_idx
            elif (
                "status" in header
                or "result" in header
                or "pass/fail" in header
            ):
                status_col_idx = col_idx

        for row_idx, row in enumerate(rows, start=1):
            cells = [clean_text(cell) for cell in row]
            if not any(cells):
                continue

            tc_id = None
            if id_col_idx != -1 and id_col_idx < len(cells):
                tc_id = find_test_case_id(cells[id_col_idx])

            if not tc_id:
                for cell in cells:
                    tc_id = find_test_case_id(cell)
                    if tc_id:
                        break

            has_content = False
            title = ""
            description = ""
            steps = ""
            expected_result = ""
            actual_result = None
            status = None

            if title_col_idx != -1 and title_col_idx < len(cells):
                title = cells[title_col_idx]
                if title:
                    has_content = True

            if desc_col_idx != -1 and desc_col_idx < len(cells):
                description = cells[desc_col_idx]
                if description:
                    has_content = True

            if steps_col_idx != -1 and steps_col_idx < len(cells):
                steps = cells[steps_col_idx]
                if steps:
                    has_content = True

            if expected_col_idx != -1 and expected_col_idx < len(cells):
                expected_result = cells[expected_col_idx]
                if expected_result:
                    has_content = True

            if actual_col_idx != -1 and actual_col_idx < len(cells):
                actual_result = cells[actual_col_idx]
                if actual_result:
                    has_content = True

            if status_col_idx != -1 and status_col_idx < len(cells):
                status = cells[status_col_idx]
                if status:
                    has_content = True

            if not has_content:
                continue

            if not tc_id:
                tc_id = "TC-AUTO-GEN"

            if not title:
                title = (
                    description[:50]
                    if description
                    else f"Test case {tc_id}"
                )

            location = f"{table_name}, Row {row_idx}"

            test_cases.append(
                TestCase(
                    id=tc_id,
                    title=title,
                    description=description,
                    steps=steps,
                    expected_result=expected_result,
                    actual_result=actual_result if actual_result else None,
                    status=status if status else None,
                    source_file=document.file_name,
                    source_location=location
                )
            )

    auto_count = 1
    for tc in test_cases:
        if tc.id == "TC-AUTO-GEN":
            tc.id = f"TC-AUTO-{auto_count:03d}"
            auto_count += 1

    return test_cases


def remove_duplicate_test_cases(
    test_cases: List[TestCase]
) -> List[TestCase]:
    """
    Remove duplicate test cases based on ID and title.
    """
    unique = []
    seen = set()

    for tc in test_cases:
        key = (tc.id, tc.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(tc)

    return unique


def extract_test_cases(document: DocumentContent) -> List[TestCase]:
    """
    Main extraction interface routing to text and table test case extractors.
    """
    # 1. Table-based extraction (Excel, CSV)
    table_cases = extract_test_cases_from_tables(document)

    # 2. Text-based extraction (PDF, DOCX)
    text_cases = extract_test_cases_from_text_block(
        document.text, document.file_name
    )

    # Combine (prioritizing table cases to retain rich columns during deduplication)
    all_cases = table_cases + text_cases

    return remove_duplicate_test_cases(all_cases)
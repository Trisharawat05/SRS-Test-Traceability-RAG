import re
from typing import List, Optional
from models.document_models import Requirement
from ingestion.document import DocumentContent


def clean_text(text: str) -> str:
    """
    Clean unnecessary whitespace while preserving the actual text.
    """
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_requirement_id(text: str) -> Optional[str]:
    """
    Detect common requirement ID formats in order of priority.
    """
    # 1. Specific standard patterns (case-insensitive)
    ci_patterns = [
        r"\b(?:REQ|FR|NFR|SR)[-_ ]?\d+\b",
        r"\bRequirement\s+\d+\b"
    ]
    for pattern in ci_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group().strip()
            if not re.match(r"^PAGE[-_ ]?\d+$", val, re.IGNORECASE):
                return val

    # 2. General code patterns and sections (case-sensitive)
    cs_patterns = [
        r"\b[A-Z]{2,4}[-_ ]\d+\b",
        r"\b\d+\.\d+\.\d+(?:\.\d+)*\b"
    ]
    for pattern in cs_patterns:
        match = re.search(pattern, text)
        if match:
            val = match.group().strip()
            if not re.match(r"^PAGE[-_ ]?\d+$", val, re.IGNORECASE):
                return val

    return None


def has_definitive_requirement_language(text: str) -> bool:
    """
    Check for definitive requirement keywords (excluding 'should').
    """
    text_lower = text.lower()
    phrases = [
        "shall",
        "must",
        "is required to",
        "required to",
        "will provide",
        "will support",
        "will allow",
        "is responsible for",
        "the system shall",
        "the system must"
    ]
    return any(phrase in text_lower for phrase in phrases)


def has_requirement_language(text: str) -> bool:
    """
    Check for any requirement keywords (including 'should' as supporting signal).
    """
    if has_definitive_requirement_language(text):
        return True
    return "should" in text.lower()


def parse_segment(
    segment_text: str, req_id: str, file_name: str, base_location: str
) -> Optional[Requirement]:
    """
    Parse a partitioned text segment for a requirement.
    """
    lines = [
        clean_text(line)
        for line in segment_text.splitlines()
        if clean_text(line)
    ]
    if not lines:
        return None

    title = None
    text_val = None

    # Check for explicit labeled formats (e.g., Explore Hotels format)
    for line in lines:
        lower_line = line.lower()
        if lower_line.startswith("title"):
            title = re.sub(
                r"^title[:\s]*", "", line, flags=re.IGNORECASE
            ).strip()
        elif lower_line.startswith("requirement"):
            text_val = re.sub(
                r"^requirement[:\s]*", "", line, flags=re.IGNORECASE
            ).strip()

    # Search for requirement language lines if not labeled
    if not text_val:
        for line in lines:
            if line == req_id or len(line) < 10:
                continue
            if has_requirement_language(line):
                text_val = line
                break

    # Fallback to the longest line that isn't the ID
    if not text_val:
        non_id_lines = [l for l in lines if l != req_id and len(l) > 5]
        if non_id_lines:
            text_val = max(non_id_lines, key=len)

    if not text_val:
        text_val = " ".join(lines)

    # Sanity checks to filter out heading-only segment debris
    if text_val == req_id or not text_val or len(text_val) < 10:
        return None

    # If the ID is a section-style dotted number (e.g. 5.1.1), require actual requirement language
    if re.match(r"^\d+\.\d+\.\d+(?:\.\d+)*$", req_id):
        if not has_requirement_language(text_val):
            return None

    # Determine title from first line or other short lines
    if not title:
        first_line = lines[0]
        if req_id in first_line:
            temp = first_line
            temp = re.sub(r"^\d+(?:\.\d+)*\s*", "", temp)
            temp = re.sub(
                r"\b" + re.escape(req_id) + r"\b\s*",
                "",
                temp,
                flags=re.IGNORECASE
            )
            temp = temp.strip("-:.\s ")
            if temp and len(temp) > 3:
                title = temp

    if not title:
        # Find any other short line in the block that is not the ID or requirement text
        for line in lines:
            if line != req_id and line != text_val and len(line) < 50:
                title = line
                break

    return Requirement(
        id=req_id,
        text=text_val,
        title=title if title else None,
        source_file=file_name,
        source_location=base_location
    )


def extract_from_text_block(
    text: str, file_name: str, base_location: str
) -> List[Requirement]:
    """
    Extract requirements from plain text using logical segment block partitioning.
    """
    if not text:
        return []

    requirements = []

    # Find matches of requirement IDs and their spans
    ci_patterns = [
        r"\b(?:REQ|FR|NFR|SR)[-_ ]?\d+\b",
        r"\bRequirement\s+\d+\b"
    ]
    cs_patterns = [
        r"\b[A-Z]{2,4}[-_ ]\d+\b",
        r"\b\d+\.\d+\.\d+(?:\.\d+)*\b"
    ]

    matches = []
    for pattern in ci_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matches.append((m.start(), m.end(), m.group()))
    for pattern in cs_patterns:
        for m in re.finditer(pattern, text):
            matches.append((m.start(), m.end(), m.group()))

    matches.sort(key=lambda x: x[0])

    # Deduplicate overlapping matches and ignore page headings/footers
    filtered_matches = []
    last_end = -1
    for start, end, val in matches:
        if re.match(r"^PAGE[-_ ]?\d+$", val, re.IGNORECASE):
            continue
        if start >= last_end:
            filtered_matches.append((start, end, val))
            last_end = end

    used_text_spans = []
    if filtered_matches:
        for idx, (start, end, val) in enumerate(filtered_matches):
            seg_start = start
            seg_end = (
                filtered_matches[idx + 1][0]
                if idx + 1 < len(filtered_matches)
                else len(text)
            )

            segment = text[seg_start:seg_end]
            used_text_spans.append((seg_start, seg_end))

            # Detect page number dynamically using backward search for page headers
            page_num = 1
            page_match = list(re.finditer(r"--- PAGE (\d+) ---", text[:start]))
            if page_match:
                page_num = int(page_match[-1].group(1))

            loc = f"Page {page_num}" if "Page" in base_location else base_location

            req = parse_segment(segment, val, file_name, loc)
            if req:
                requirements.append(req)

    # Search for auto-generated requirements (definitive language only) outside ID blocks
    lines = text.splitlines()
    char_offset = 0
    for line_num, line in enumerate(lines, start=1):
        line_len = len(line) + 1
        start_pos = char_offset
        end_pos = char_offset + len(line)
        char_offset += line_len

        in_segment = False
        for s_start, s_end in used_text_spans:
            if start_pos >= s_start and end_pos <= s_end:
                in_segment = True
                break

        if in_segment:
            continue

        cleaned = clean_text(line)
        if not cleaned:
            continue

        # Treat 'should' as a supporting signal ONLY (exclude here)
        if has_definitive_requirement_language(cleaned):
            req_id = find_requirement_id(cleaned) or "REQ-AUTO-GEN"
            
            page_num = 1
            page_match = list(re.finditer(r"--- PAGE (\d+) ---", text[:start_pos]))
            if page_match:
                page_num = int(page_match[-1].group(1))
            loc = f"Page {page_num}" if "Page" in base_location else base_location
            
            requirements.append(
                Requirement(
                    id=req_id,
                    text=cleaned,
                    title=None,
                    source_file=file_name,
                    source_location=f"{loc}, Line {line_num}" if "Page" not in loc else f"{loc}"
                )
            )

    # Assign final unique auto IDs
    auto_count = 1
    for req in requirements:
        if req.id == "REQ-AUTO-GEN":
            req.id = f"REQ-AUTO-{auto_count:03d}"
            auto_count += 1

    return requirements


def extract_from_tables(document: DocumentContent) -> List[Requirement]:
    """
    Extract requirements from tabular structures.
    """
    requirements = []

    for table_idx, table in enumerate(document.tables, start=1):
        rows = table.get("rows", [])
        columns = table.get("columns", [])
        table_name = table.get("name", f"Table {table_idx}")

        if not rows:
            continue

        id_col_idx = -1
        title_col_idx = -1
        text_col_idx = -1

        # Semantic column header mapping
        headers = [clean_text(h).lower() for h in columns]
        for col_idx, header in enumerate(headers):
            if "id" in header and (
                "req" in header or "requirement" in header
            ):
                id_col_idx = col_idx
            elif "id" in header and id_col_idx == -1:
                id_col_idx = col_idx
            elif (
                "title" in header
                or "name" in header
                or "subsystem" in header
            ):
                title_col_idx = col_idx
            elif (
                "req" in header
                or "text" in header
                or "description" in header
                or "statement" in header
            ):
                text_col_idx = col_idx

        for row_idx, row in enumerate(rows, start=1):
            cells = [clean_text(cell) for cell in row]
            if not any(cells):
                continue

            req_id = None
            if id_col_idx != -1 and id_col_idx < len(cells):
                req_id = find_requirement_id(cells[id_col_idx])

            if not req_id:
                for cell in cells:
                    req_id = find_requirement_id(cell)
                    if req_id:
                        break

            text_val = None
            if text_col_idx != -1 and text_col_idx < len(cells):
                text_val = cells[text_col_idx]

            if not text_val:
                for cell in cells:
                    if cell != req_id and has_requirement_language(cell):
                        text_val = cell
                        break

            if not text_val:
                non_id_cells = [c for c in cells if c != req_id and len(c) > 0]
                if non_id_cells:
                    text_val = max(non_id_cells, key=len)

            if not text_val:
                continue

            # Must have either an explicit ID or definitive requirement language
            if not req_id and not has_definitive_requirement_language(text_val):
                continue

            if not req_id:
                req_id = "REQ-AUTO-GEN"

            title = None
            if title_col_idx != -1 and title_col_idx < len(cells):
                title = cells[title_col_idx]

            if not title:
                for cell in cells:
                    if (
                        cell != req_id
                        and cell != text_val
                        and 0 < len(cell) < 50
                    ):
                        title = cell
                        break

            requirements.append(
                Requirement(
                    id=req_id,
                    text=text_val,
                    title=title if title else None,
                    source_file=document.file_name,
                    source_location=f"{table_name}, Row {row_idx}"
                )
            )

    auto_count = 1
    for req in requirements:
        if req.id == "REQ-AUTO-GEN":
            req.id = f"REQ-AUTO-{auto_count:03d}"
            auto_count += 1

    return requirements


def remove_duplicates(requirements: List[Requirement]) -> List[Requirement]:
    """
    Remove duplicate requirements based on ID and text.
    """
    unique = []
    seen = set()

    for requirement in requirements:
        key = (requirement.id, requirement.text)
        if key in seen:
            continue
        seen.add(key)
        unique.append(requirement)

    return unique


def extract_requirements(document: DocumentContent) -> List[Requirement]:
    """
    Main extraction interface routing to text and table extractors.
    """
    requirements = []

    # 1. Extract from tables (DOCX, Excel, CSV)
    table_requirements = extract_from_tables(document)
    requirements.extend(table_requirements)

    # 2. Extract from page structures or raw text (PDF, DOCX paragraphs, Text)
    if document.pages:
        # Join pages into full text, but with page marker headers inserted
        # (This allows find_page_number_in_text to locate the page dynamically)
        text_parts = []
        for p in document.pages:
            p_num = p.get("page_number", 1)
            p_text = p.get("text", "")
            text_parts.append(f"\n--- PAGE {p_num} ---\n{p_text}")
        full_text = "\n".join(text_parts)
        
        reqs = extract_from_text_block(
            full_text, document.file_name, "Page 1"
        )
        requirements.extend(reqs)
    else:
        reqs = extract_from_text_block(
            document.text, document.file_name, "Document Text"
        )
        requirements.extend(reqs)

    return remove_duplicates(requirements)

import json
import re
from pathlib import Path

from models.document_models import Requirement, TestCase


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value) -> str:
    """
    Normalize whitespace while preserving the original meaning.
    """

    if value is None:
        return ""

    text = str(value)

    # Normalize newline characters
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Replace multiple whitespace characters with one space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# ID NORMALIZATION
# ============================================================

def normalize_id(value) -> str:
    """
    Normalize an identifier without changing its meaning.
    """

    if value is None:
        return ""

    value = normalize_text(value)

    return value.upper()


# ============================================================
# REQUIREMENT NORMALIZATION
# ============================================================

def normalize_requirement(
    requirement: Requirement
) -> dict:
    """
    Convert a Requirement object into a clean JSON-compatible
    dictionary.
    """

    return {
        "id": normalize_id(
            requirement.id
        ),

        "text": normalize_text(
            requirement.text
        ),

        "title": (
            normalize_text(
                requirement.title
            )
            if requirement.title
            else None
        ),

        "source_file": normalize_text(
            requirement.source_file
        ),

        "source_location": normalize_text(
            requirement.source_location
        ),
    }


# ============================================================
# TEST CASE NORMALIZATION
# ============================================================

def normalize_test_case(
    test_case: TestCase
) -> dict:
    """
    Convert a TestCase object into a clean JSON-compatible
    dictionary.
    """

    return {
        "id": normalize_id(
            test_case.id
        ),

        "title": normalize_text(
            test_case.title
        ),

        "description": normalize_text(
            test_case.description
        ),

        "steps": normalize_text(
            test_case.steps
        ),

        "expected_result": normalize_text(
            test_case.expected_result
        ),

        "actual_result": normalize_text(
            test_case.actual_result
        ),

        "status": normalize_text(
            test_case.status
        ),

        "source_file": normalize_text(
            test_case.source_file
        ),

        "source_location": normalize_text(
            test_case.source_location
        ),
    }


# ============================================================
# HEADING DETECTION
# ============================================================

def is_heading_like_requirement(
    requirement: dict
) -> bool:
    """
    Determine whether a requirement record looks like a
    heading rather than the actual requirement statement.

    Examples from the current SRS:

        FR-01 Log-in and Checking page availability

        FR-02 Register

        [SRS Doc of Explore Hotels]

        FR-04 Select Hotel

    These are headings/titles and should not become separate
    requirement records.
    """

    requirement_id = requirement.get(
        "id",
        ""
    ).strip()

    text = requirement.get(
        "text",
        ""
    ).strip()

    if not text:
        return True

    # Example:
    # FR-01 Log-in and Checking page availability
    if requirement_id:

        pattern = (
            r"^"
            + re.escape(requirement_id)
            + r"\b"
        )

        if re.match(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return True

    # Very short records are often headings.
    words = text.split()

    if len(words) <= 4:
        return True

    # Known heading-style bracketed text.
    if (
        text.startswith("[")
        and text.endswith("]")
    ):
        return True

    return False


# ============================================================
# REQUIREMENT MERGING / DEDUPLICATION
# ============================================================

def deduplicate_requirements(
    requirements: list[dict]
) -> list[dict]:
    """
    Clean duplicate requirement records.

    The current SRS sometimes produces two records for one
    requirement:

        FR-01
        FR-01 Log-in and Checking page availability

        FR-01
        The user should know how to log-in...

    The heading-like record is merged with the following
    requirement statement.

    Important:
    Two different requirements with the same ID are NOT
    automatically merged.
    """

    cleaned = []

    i = 0

    while i < len(requirements):

        current = requirements[i]

        # ----------------------------------------------------
        # Check the next record
        # ----------------------------------------------------

        if i + 1 < len(requirements):

            next_record = requirements[i + 1]

            current_id = normalize_id(
                current.get("id")
            )

            next_id = normalize_id(
                next_record.get("id")
            )

            same_id = (
                current_id != ""
                and current_id == next_id
            )

            # ------------------------------------------------
            # If both records have the same ID and the first
            # one looks like a heading, merge them.
            # ------------------------------------------------

            if same_id and is_heading_like_requirement(
                current
            ):

                merged = {
                    "id": current_id,

                    "text": normalize_text(
                        next_record.get("text")
                    ),

                    "title": (
                        current.get("title")
                        or next_record.get("title")
                    ),

                    "source_file": (
                        current.get("source_file")
                        or next_record.get(
                            "source_file"
                        )
                    ),

                    "source_location": (
                        next_record.get(
                            "source_location"
                        )
                        or current.get(
                            "source_location"
                        )
                    )
                }

                cleaned.append(
                    merged
                )

                # Skip both records because they have
                # now become one requirement.
                i += 2

                continue

        # ----------------------------------------------------
        # Normal requirement
        # ----------------------------------------------------

        cleaned.append(
            current
        )

        i += 1

    # --------------------------------------------------------
    # Remove exact duplicates only
    # --------------------------------------------------------

    unique = []

    seen = set()

    for requirement in cleaned:

        key = (
            requirement.get("id", ""),
            requirement.get("text", "")
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            requirement
        )

    return unique


# ============================================================
# DUPLICATE ID DIAGNOSTIC
# ============================================================

def find_duplicate_requirement_ids(
    requirements: list[dict]
) -> dict:
    """
    Find requirement IDs that still occur more than once
    after heading merging.

    This is diagnostic only.

    We deliberately do NOT merge these records because
    they may represent genuinely different requirements
    sharing the same source ID.
    """

    counts = {}

    for requirement in requirements:

        requirement_id = (
            requirement.get("id", "")
        )

        if not requirement_id:
            continue

        counts[requirement_id] = (
            counts.get(
                requirement_id,
                0
            ) + 1
        )

    duplicates = {
        requirement_id: count
        for requirement_id, count
        in counts.items()
        if count > 1
    }

    return duplicates


# ============================================================
# TEST CASE DEDUPLICATION
# ============================================================

def deduplicate_test_cases(
    test_cases: list[dict]
) -> list[dict]:
    """
    Remove exact duplicate test cases.

    Two test cases with the same ID but different content
    are preserved.
    """

    unique = []

    seen = set()

    for test_case in test_cases:

        key = (
            test_case.get(
                "id",
                ""
            ),

            test_case.get(
                "title",
                ""
            ),

            test_case.get(
                "description",
                ""
            ),

            test_case.get(
                "steps",
                ""
            ),

            test_case.get(
                "expected_result",
                ""
            )
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            test_case
        )

    return unique


# ============================================================
# JSON WRITING
# ============================================================

def save_json(
    data: list[dict],
    output_path: str
):
    """
    Save normalized records as readable JSON.
    """

    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# COMPLETE REQUIREMENT NORMALIZATION PIPELINE
# ============================================================

def normalize_requirements(
    requirements
) -> list[dict]:
    """
    Complete requirement normalization pipeline.
    """

    # --------------------------------------------------------
    # Step 1: Normalize individual records
    # --------------------------------------------------------

    normalized = [
        normalize_requirement(
            requirement
        )
        for requirement in requirements
    ]

    # --------------------------------------------------------
    # Step 2: Merge heading + requirement statement
    # --------------------------------------------------------

    normalized = deduplicate_requirements(
        normalized
    )

    # --------------------------------------------------------
    # Step 3: Check for remaining duplicate IDs
    # --------------------------------------------------------

    duplicates = find_duplicate_requirement_ids(
        normalized
    )

    if duplicates:

        print(
            "\nWARNING: Duplicate requirement IDs "
            "still detected:"
        )

        for requirement_id, count in (
            duplicates.items()
        ):

            print(
                f"  {requirement_id}: "
                f"{count} occurrences"
            )

        print(
            "\nThese were NOT automatically merged "
            "because they may represent different "
            "requirements."
        )

    return normalized


# ============================================================
# COMPLETE TEST CASE NORMALIZATION PIPELINE
# ============================================================

def normalize_test_cases(
    test_cases
) -> list[dict]:
    """
    Complete test-case normalization pipeline.
    """

    # --------------------------------------------------------
    # Step 1: Normalize individual records
    # --------------------------------------------------------

    normalized = [
        normalize_test_case(
            test_case
        )
        for test_case in test_cases
    ]

    # --------------------------------------------------------
    # Step 2: Remove exact duplicates
    # --------------------------------------------------------

    normalized = deduplicate_test_cases(
        normalized
    )

    return normalized


# ============================================================
# OPTIONAL COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Normalizer module loaded successfully."
    )
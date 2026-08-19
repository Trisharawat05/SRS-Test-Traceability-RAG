import os

from ingestion.universal_loader import load_document
from analysis.requirement_extractor import extract_requirements
from analysis.testcase_extractor import extract_test_cases
from analysis.normalizer import (
    normalize_requirements,
    normalize_test_cases,
    save_json
)


# ============================================================
# INPUT FILES
# ============================================================

SRS_FILE = "data/SRS document.pdf"
TEST_FILE = "data/Test Document.pdf"


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    "output",
    exist_ok=True
)


# ============================================================
# SAFE PRINT
# ============================================================

def safe_print(label, val):

    try:

        print(
            f"{label} {val}"
        )

    except UnicodeEncodeError:

        safe_val = (
            str(val)
            .encode(
                "ascii",
                errors="replace"
            )
            .decode("ascii")
        )

        print(
            f"{label} {safe_val}"
        )


# ============================================================
# SRS EXTRACTION
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "SRS EXTRACTION"
)

print(
    "=" * 80
)

print(
    f"Loading SRS file: {SRS_FILE} ..."
)

srs_document = load_document(
    SRS_FILE
)

print(
    "Extracting requirements..."
)

requirements = extract_requirements(
    srs_document
)


# ============================================================
# NORMALIZE REQUIREMENTS
# ============================================================

normalized_requirements = (
    normalize_requirements(
        requirements
    )
)


print(
    f"\nRaw requirements found: "
    f"{len(requirements)}"
)

print(
    f"Normalized requirements: "
    f"{len(normalized_requirements)}"
)


# ============================================================
# SAVE ONLY NORMALIZED REQUIREMENTS
# ============================================================

requirements_json_path = (
    "output/requirements.json"
)

save_json(
    normalized_requirements,
    requirements_json_path
)

print(
    f"\nSaved normalized requirements to: "
    f"{requirements_json_path}"
)


# ============================================================
# DISPLAY REQUIREMENTS
# ============================================================

print(
    "\nFirst 10 normalized requirements:"
)

for requirement in normalized_requirements[:10]:

    print(
        "\n------------------------------"
    )

    safe_print(
        "ID:",
        requirement["id"]
    )

    safe_print(
        "TEXT:",
        requirement["text"]
    )

    safe_print(
        "TITLE:",
        requirement.get("title")
    )

    safe_print(
        "SOURCE LOCATION:",
        requirement["source_location"]
    )


# ============================================================
# TEST CASE EXTRACTION
# ============================================================

print(
    "\n\n" + "=" * 80
)

print(
    "TEST CASE EXTRACTION"
)

print(
    "=" * 80
)

print(
    f"Loading Test file: {TEST_FILE} ..."
)

test_document = load_document(
    TEST_FILE
)

print(
    "Extracting test cases..."
)

test_cases = extract_test_cases(
    test_document
)


# ============================================================
# NORMALIZE TEST CASES
# ============================================================

normalized_test_cases = (
    normalize_test_cases(
        test_cases
    )
)


print(
    f"\nRaw test cases found: "
    f"{len(test_cases)}"
)

print(
    f"Normalized test cases: "
    f"{len(normalized_test_cases)}"
)


# ============================================================
# SAVE ONLY NORMALIZED TEST CASES
# ============================================================

test_cases_json_path = (
    "output/test_cases.json"
)

save_json(
    normalized_test_cases,
    test_cases_json_path
)

print(
    f"\nSaved normalized test cases to: "
    f"{test_cases_json_path}"
)


# ============================================================
# DISPLAY TEST CASES
# ============================================================

print(
    "\nFirst 10 normalized test cases:"
)

for test_case in normalized_test_cases[:10]:

    print(
        "\n------------------------------"
    )

    safe_print(
        "ID:",
        test_case["id"]
    )

    safe_print(
        "TITLE:",
        test_case["title"]
    )

    safe_print(
        "DESCRIPTION:",
        test_case["description"]
    )

    safe_print(
        "STEPS:",
        test_case["steps"]
    )

    safe_print(
        "EXPECTED:",
        test_case["expected_result"]
    )

    safe_print(
        "SOURCE LOCATION:",
        test_case["source_location"]
    )


# ============================================================
# COMPLETE
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "EXTRACTION AND NORMALIZATION COMPLETE"
)

print(
    "=" * 80
)
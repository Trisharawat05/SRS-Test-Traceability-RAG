import json
from pathlib import Path


def build_requirement_text(requirement: dict) -> str:
    """
    Build the text representation of a requirement
    that will later be passed to the embedding model.
    """

    parts = [
        f"Requirement ID: {requirement.get('id', '')}",
        f"Requirement: {requirement.get('text', '')}",
    ]

    title = requirement.get("title")

    if title:
        parts.append(
            f"Title: {title}"
        )

    return "\n".join(parts)


def build_test_case_text(test_case: dict) -> str:
    """
    Build the text representation of a test case
    that will later be passed to the embedding model.
    """

    parts = [
        f"Test Case ID: {test_case.get('id', '')}",
    ]

    if test_case.get("title"):
        parts.append(
            f"Title: {test_case['title']}"
        )

    if test_case.get("description"):
        parts.append(
            f"Description: {test_case['description']}"
        )

    if test_case.get("steps"):
        parts.append(
            f"Steps: {test_case['steps']}"
        )

    if test_case.get("expected_result"):
        parts.append(
            f"Expected Result: {test_case['expected_result']}"
        )

    return "\n".join(parts)


def load_json(path: str):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def prepare_embedding_data():

    requirements = load_json(
        "output/requirements.json"
    )

    test_cases = load_json(
        "output/test_cases.json"
    )

    requirement_documents = []

    for requirement in requirements:

        requirement_documents.append({
            "id": requirement["id"],

            "text": build_requirement_text(
                requirement
            ),

            "metadata": {
                "type": "requirement",
                "source_file": requirement.get(
                    "source_file"
                ),
                "source_location": requirement.get(
                    "source_location"
                )
            }
        })

    test_case_documents = []

    for test_case in test_cases:

        test_case_documents.append({
            "id": test_case["id"],

            "text": build_test_case_text(
                test_case
            ),

            "metadata": {
                "type": "test_case",
                "source_file": test_case.get(
                    "source_file"
                ),
                "source_location": test_case.get(
                    "source_location"
                )
            }
        })

    output_dir = Path("output")

    output_dir.mkdir(
        exist_ok=True
    )

    with open(
        output_dir / "requirement_documents.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            requirement_documents,
            file,
            indent=4,
            ensure_ascii=False
        )

    with open(
        output_dir / "test_case_documents.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            test_case_documents,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Prepared {len(requirement_documents)} "
        "requirement documents."
    )

    print(
        f"Prepared {len(test_case_documents)} "
        "test case documents."
    )


if __name__ == "__main__":
    prepare_embedding_data()
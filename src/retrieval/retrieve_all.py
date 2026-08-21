import json
from pathlib import Path

from retriever import (
    get_test_case_collection,
    retrieve_test_cases
)


# ============================================================
# CONFIGURATION
# ============================================================

REQUIREMENT_EMBEDDINGS = (
    "output/requirement_embeddings.json"
)

OUTPUT_PATH = (
    "output/retrieval_results.json"
)

TOP_K = 5


# ============================================================
# LOAD REQUIREMENTS
# ============================================================

def load_requirements(path: str) -> list[dict]:
    """
    Load requirement embeddings from JSON.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# RETRIEVE FOR ALL REQUIREMENTS
# ============================================================

def retrieve_all_requirements(
    requirements: list[dict],
    collection,
    top_k: int
) -> list[dict]:
    """
    Retrieve the top-K candidate test cases
    for every requirement.
    """

    all_results = []

    for index, requirement in enumerate(
        requirements,
        start=1
    ):

        print(
            f"Processing {index}/{len(requirements)}: "
            f"{requirement['id']}"
        )

        candidates = retrieve_test_cases(
            requirement_embedding=(
                requirement["embedding"]
            ),
            collection=collection,
            top_k=top_k
        )

        all_results.append(
            {
                "requirement_id": requirement["id"],

                "requirement_text": (
                    requirement["text"]
                ),

                "candidates": candidates
            }
        )

    return all_results


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results: list[dict],
    path: str
):
    """
    Save retrieval results as JSON.
    """

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("RETRIEVING TEST CASES FOR ALL REQUIREMENTS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load requirements
    # --------------------------------------------------------

    requirements = load_requirements(
        REQUIREMENT_EMBEDDINGS
    )

    print(
        f"\nRequirements loaded: "
        f"{len(requirements)}"
    )

    if not requirements:

        print(
            "No requirement embeddings found."
        )

        return

    # --------------------------------------------------------
    # Connect to ChromaDB
    # --------------------------------------------------------

    print(
        "\nConnecting to ChromaDB..."
    )

    test_case_collection = (
        get_test_case_collection()
    )

    print(
        f"Test cases available: "
        f"{test_case_collection.count()}"
    )

    # --------------------------------------------------------
    # Retrieve candidates
    # --------------------------------------------------------

    print(
        f"\nRetrieving top {TOP_K} "
        "test cases for each requirement...\n"
    )

    results = retrieve_all_requirements(
        requirements=requirements,
        collection=test_case_collection,
        top_k=TOP_K
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    save_results(
        results,
        OUTPUT_PATH
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "RETRIEVAL COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"\nProcessed requirements: "
        f"{len(results)}"
    )

    print(
        f"Results saved to: "
        f"{OUTPUT_PATH}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
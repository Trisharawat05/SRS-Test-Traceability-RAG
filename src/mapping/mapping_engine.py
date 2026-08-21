import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = (
    "output/reranked_results.json"
)

OUTPUT_PATH = (
    "output/candidate_mappings.json"
)

TOP_K = 5


# ============================================================
# LOAD RESULTS
# ============================================================

def load_results(path: str) -> list[dict]:
    """
    Load reranked retrieval results.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# CREATE CANDIDATE MAPPINGS
# ============================================================

def create_candidate_mappings(
    results: list[dict]
) -> list[dict]:
    """
    Convert reranked results into a clean
    requirement-to-test-case candidate mapping.
    """

    mappings = []

    for requirement in results:

        requirement_id = (
            requirement["requirement_id"]
        )

        requirement_text = (
            requirement["requirement_text"]
        )

        candidates = requirement.get(
            "reranked_candidates",
            []
        )

        for rank, candidate in enumerate(
            candidates,
            start=1
        ):

            mappings.append(
                {
                    "requirement_id":
                        requirement_id,

                    "requirement_text":
                        requirement_text,

                    "test_case_id":
                        candidate[
                            "test_case_id"
                        ],

                    "test_case_text":
                        candidate[
                            "document"
                        ],

                    "retrieval_similarity":
                        candidate.get(
                            "similarity"
                        ),

                    "reranker_score":
                        candidate.get(
                            "reranker_score"
                        ),

                    "rank":
                        rank
                }
            )

    return mappings


# ============================================================
# SAVE MAPPINGS
# ============================================================

def save_mappings(
    mappings: list[dict],
    path: str
):
    """
    Save candidate mappings to JSON.
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
            mappings,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# DISPLAY SAMPLE
# ============================================================

def display_sample(
    mappings: list[dict]
):
    """
    Display a few candidate mappings.
    """

    print(
        "\n" + "=" * 80
    )

    print(
        "SAMPLE CANDIDATE MAPPINGS"
    )

    print(
        "=" * 80
    )

    for mapping in mappings[:10]:

        print(
            f"\nRequirement: "
            f"{mapping['requirement_id']}"
        )

        print(
            f"Test Case: "
            f"{mapping['test_case_id']}"
        )

        print(
            f"Rank: "
            f"{mapping['rank']}"
        )

        print(
            f"Retrieval similarity: "
            f"{mapping['retrieval_similarity']}"
        )

        print(
            f"Reranker score: "
            f"{mapping['reranker_score']}"
        )

        print(
            "\nRequirement:"
        )

        print(
            mapping["requirement_text"]
        )

        print(
            "\nTest Case:"
        )

        print(
            mapping["test_case_text"]
        )

        print(
            "-" * 80
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)

    print(
        "REQUIREMENT-TEST CASE MAPPING"
    )

    print("=" * 80)

    # --------------------------------------------------------
    # Load reranked results
    # --------------------------------------------------------

    print(
        "\nLoading reranked results..."
    )

    results = load_results(
        INPUT_PATH
    )

    print(
        f"Loaded results for "
        f"{len(results)} requirements."
    )

    if not results:

        print(
            "No reranked results found."
        )

        return

    # --------------------------------------------------------
    # Create mappings
    # --------------------------------------------------------

    print(
        "\nCreating candidate mappings..."
    )

    mappings = create_candidate_mappings(
        results
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_mappings(
        mappings,
        OUTPUT_PATH
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    display_sample(
        mappings
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 80
    )

    print(
        "MAPPING COMPLETE"
    )

    print(
        "=" * 80
    )

    print(
        f"\nTotal candidate mappings: "
        f"{len(mappings)}"
    )

    print(
        f"Saved to: "
        f"{OUTPUT_PATH}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
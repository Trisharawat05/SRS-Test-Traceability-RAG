import json

import chromadb


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = "chroma_db"

REQUIREMENT_EMBEDDINGS = (
    "output/requirement_embeddings.json"
)

TOP_K = 5


# ============================================================
# LOAD REQUIREMENT EMBEDDINGS
# ============================================================

def load_embeddings(path: str) -> list[dict]:
    """
    Load requirement embedding records from JSON.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

def get_test_case_collection():
    """
    Connect to the persistent ChromaDB database
    and return the test_cases collection.
    """

    client = chromadb.PersistentClient(
        path=DB_PATH
    )

    return client.get_collection(
        name="test_cases"
    )


# ============================================================
# CONVERT DISTANCE TO SIMILARITY
# ============================================================

def distance_to_similarity(distance: float) -> float:
    """
    Convert ChromaDB cosine distance into a simple
    similarity score.

    For normalized embeddings:

        similarity ≈ 1 - distance
    """

    similarity = 1 - distance

    return round(similarity, 4)


# ============================================================
# RETRIEVE TEST CASES
# ============================================================

def retrieve_test_cases(
    requirement_embedding: list[float],
    collection,
    top_k: int = TOP_K
) -> list[dict]:
    """
    Retrieve the top-K most similar test cases
    for a requirement.
    """

    results = collection.query(

        query_embeddings=[
            requirement_embedding
        ],

        n_results=top_k,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved_results = []

    ids = results["ids"][0]

    documents = results["documents"][0]

    metadatas = results["metadatas"][0]

    distances = results["distances"][0]

    for chroma_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances
    ):

        retrieved_results.append(
            {
                "chroma_id": chroma_id,

                "test_case_id": metadata.get(
                    "record_id",
                    chroma_id
                ),

                "document": document,

                "source_file": metadata.get(
                    "source_file",
                    ""
                ),

                "source_location": metadata.get(
                    "source_location",
                    ""
                ),

                "distance": round(
                    distance,
                    4
                ),

                "similarity": distance_to_similarity(
                    distance
                )
            }
        )

    return retrieved_results


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    requirement: dict,
    results: list[dict]
):
    """
    Display the retrieval results in a readable format.
    """

    print("\n" + "=" * 80)

    print(
        f"REQUIREMENT: {requirement['id']}"
    )

    print("-" * 80)

    print(
        requirement["text"]
    )

    print("\nTOP MATCHING TEST CASES")

    print("=" * 80)

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n{rank}. Test Case: "
            f"{result['test_case_id']}"
        )

        print(
            f"Similarity: "
            f"{result['similarity']}"
        )

        print(
            f"Distance: "
            f"{result['distance']}"
        )

        print(
            f"Source: "
            f"{result['source_file']}"
        )

        print(
            f"Location: "
            f"{result['source_location']}"
        )

        print("\nTest Case Content:")

        print(
            result["document"]
        )

        print("-" * 80)


# ============================================================
# TEST RETRIEVAL
# ============================================================

def main():

    print("=" * 80)
    print("SEMANTIC RETRIEVAL TEST")
    print("=" * 80)

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
    # Load requirement embeddings
    # --------------------------------------------------------

    print(
        "\nLoading requirement embeddings..."
    )

    requirements = load_embeddings(
        REQUIREMENT_EMBEDDINGS
    )

    print(
        f"Requirements available: "
        f"{len(requirements)}"
    )

    if not requirements:

        print(
            "No requirement embeddings found."
        )

        return

    # --------------------------------------------------------
    # Test first requirement
    # --------------------------------------------------------

    requirement = requirements[0]

    print(
        f"\nTesting retrieval for: "
        f"{requirement['id']}"
    )

    results = retrieve_test_cases(

        requirement_embedding=(
            requirement["embedding"]
        ),

        collection=test_case_collection,

        top_k=TOP_K
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    display_results(
        requirement,
        results
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
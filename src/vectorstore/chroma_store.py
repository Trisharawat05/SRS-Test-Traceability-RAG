import json

import chromadb


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = "chroma_db"

REQUIREMENT_EMBEDDINGS = (
    "output/requirement_embeddings.json"
)

TEST_CASE_EMBEDDINGS = (
    "output/test_case_embeddings.json"
)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

def load_embeddings(path: str) -> list[dict]:
    """
    Load embedding records from a JSON file.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# CREATE CHROMADB CLIENT
# ============================================================

def create_client():
    """
    Create a persistent ChromaDB client.
    """

    return chromadb.PersistentClient(
        path=DB_PATH
    )


# ============================================================
# CREATE COLLECTIONS
# ============================================================

def create_collections(client):
    """
    Create or retrieve the requirement and test case collections.
    """

    requirement_collection = (
        client.get_or_create_collection(
            name="requirements"
        )
    )

    testcase_collection = (
        client.get_or_create_collection(
            name="test_cases"
        )
    )

    return (
        requirement_collection,
        testcase_collection
    )


# ============================================================
# ADD / UPDATE REQUIREMENTS
# ============================================================

def add_requirements(
    collection,
    requirements: list[dict]
):
    """
    Store requirement embeddings in ChromaDB.

    A unique internal ChromaDB ID is created for every record,
    while the original requirement ID is preserved as metadata.
    """

    if not requirements:

        print(
            "No requirements to add."
        )

        return

    # --------------------------------------------------------
    # Create unique ChromaDB IDs
    # --------------------------------------------------------

    ids = [
        f"REQ_{item['id']}_{index}"
        for index, item in enumerate(requirements)
    ]

    # --------------------------------------------------------
    # Add or update records
    # --------------------------------------------------------

    collection.upsert(

        ids=ids,

        embeddings=[
            item["embedding"]
            for item in requirements
        ],

        documents=[
            item["text"]
            for item in requirements
        ],

        metadatas=[
            {
                **item.get(
                    "metadata",
                    {}
                ),

                # Original requirement ID
                "record_id": item["id"],

                # Internal unique ChromaDB ID
                "chroma_id": ids[index]
            }

            for index, item
            in enumerate(requirements)
        ]
    )

    print(
        f"Added/updated {len(requirements)} "
        "requirements in ChromaDB."
    )


# ============================================================
# ADD / UPDATE TEST CASES
# ============================================================

def add_test_cases(
    collection,
    test_cases: list[dict]
):
    """
    Store test case embeddings in ChromaDB.

    A unique internal ChromaDB ID is created for every record,
    while the original test case ID is preserved as metadata.
    """

    if not test_cases:

        print(
            "No test cases to add."
        )

        return

    # --------------------------------------------------------
    # Create unique ChromaDB IDs
    # --------------------------------------------------------

    ids = [
        f"TEST_{item['id']}_{index}"
        for index, item in enumerate(test_cases)
    ]

    # --------------------------------------------------------
    # Add or update records
    # --------------------------------------------------------

    collection.upsert(

        ids=ids,

        embeddings=[
            item["embedding"]
            for item in test_cases
        ],

        documents=[
            item["text"]
            for item in test_cases
        ],

        metadatas=[
            {
                **item.get(
                    "metadata",
                    {}
                ),

                # Original test case ID
                "record_id": item["id"],

                # Internal unique ChromaDB ID
                "chroma_id": ids[index]
            }

            for index, item
            in enumerate(test_cases)
        ]
    )

    print(
        f"Added/updated {len(test_cases)} "
        "test cases in ChromaDB."
    )


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_database(
    requirement_collection,
    testcase_collection
):
    """
    Display the number of records stored in each collection.
    """

    print(
        "\nDatabase verification:"
    )

    print(
        f"Requirements: "
        f"{requirement_collection.count()}"
    )

    print(
        f"Test cases: "
        f"{testcase_collection.count()}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("CHROMADB SETUP")
    print("=" * 70)

    # --------------------------------------------------------
    # Create persistent ChromaDB client
    # --------------------------------------------------------

    client = create_client()

    print(
        f"\nChromaDB location: {DB_PATH}"
    )

    # --------------------------------------------------------
    # Create collections
    # --------------------------------------------------------

    (
        requirement_collection,
        testcase_collection
    ) = create_collections(
        client
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
        f"Loaded {len(requirements)} "
        "requirement embeddings."
    )

    # --------------------------------------------------------
    # Load test case embeddings
    # --------------------------------------------------------

    print(
        "\nLoading test-case embeddings..."
    )

    test_cases = load_embeddings(
        TEST_CASE_EMBEDDINGS
    )

    print(
        f"Loaded {len(test_cases)} "
        "test-case embeddings."
    )

    # --------------------------------------------------------
    # Store requirements
    # --------------------------------------------------------

    print(
        "\nAdding requirements..."
    )

    add_requirements(
        requirement_collection,
        requirements
    )

    # --------------------------------------------------------
    # Store test cases
    # --------------------------------------------------------

    print(
        "\nAdding test cases..."
    )

    add_test_cases(
        testcase_collection,
        test_cases
    )

    # --------------------------------------------------------
    # Verify database
    # --------------------------------------------------------

    verify_database(
        requirement_collection,
        testcase_collection
    )

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "CHROMADB SETUP COMPLETE"
    )

    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
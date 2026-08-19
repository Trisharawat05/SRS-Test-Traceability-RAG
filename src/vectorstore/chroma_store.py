import json
import shutil
from pathlib import Path

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
# ADD REQUIREMENTS
# ============================================================

def add_requirements(
    collection,
    requirements: list[dict]
):

    if not requirements:

        print(
            "No requirements to add."
        )

        return

    # --------------------------------------------------------
    # Create UNIQUE ChromaDB IDs
    #
    # Source IDs may contain duplicates such as:
    # FR-01
    # FR-01
    # NFR-04
    # NFR-04
    #
    # ChromaDB requires every ID to be unique.
    # --------------------------------------------------------

    ids = [
        f"REQ_{item['id']}_{index}"
        for index, item in enumerate(requirements)
    ]

    # --------------------------------------------------------
    # Add records
    # --------------------------------------------------------

    collection.add(

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

                # Original SRS requirement ID
                "record_id": item["id"],

                # Unique ChromaDB ID
                "chroma_id": ids[index]
            }

            for index, item
            in enumerate(requirements)
        ]
    )

    print(
        f"Added {len(requirements)} "
        "requirements to ChromaDB."
    )


# ============================================================
# ADD TEST CASES
# ============================================================

def add_test_cases(
    collection,
    test_cases: list[dict]
):

    if not test_cases:

        print(
            "No test cases to add."
        )

        return

    # --------------------------------------------------------
    # Create UNIQUE ChromaDB IDs
    # --------------------------------------------------------

    ids = [
        f"TEST_{item['id']}_{index}"
        for index, item in enumerate(test_cases)
    ]

    # --------------------------------------------------------
    # Add records
    # --------------------------------------------------------

    collection.add(

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

                # Original test-case ID
                "record_id": item["id"],

                # Unique ChromaDB ID
                "chroma_id": ids[index]
            }

            for index, item
            in enumerate(test_cases)
        ]
    )

    print(
        f"Added {len(test_cases)} "
        "test cases to ChromaDB."
    )


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_database(
    requirement_collection,
    testcase_collection
):

    print(
        "\nDatabase verification:"
    )

    print(
        "Requirements:",
        requirement_collection.count()
    )

    print(
        "Test cases:",
        testcase_collection.count()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "CHROMADB SETUP"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Create persistent client
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
    # Load test-case embeddings
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
    # Add requirements
    # --------------------------------------------------------

    print(
        "\nAdding requirements..."
    )

    add_requirements(
        requirement_collection,
        requirements
    )

    # --------------------------------------------------------
    # Add test cases
    # --------------------------------------------------------

    print(
        "\nAdding test cases..."
    )

    add_test_cases(
        testcase_collection,
        test_cases
    )

    # --------------------------------------------------------
    # Verify
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
    
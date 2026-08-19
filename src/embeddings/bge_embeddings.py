import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-base-en-v1.5"


def load_documents(path: str) -> list[dict]:

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def create_embeddings(
    documents: list[dict],
    model: SentenceTransformer,
    document_type: str
):

    texts = [
        document["text"]
        for document in documents
    ]

    print(
        f"Generating embeddings for "
        f"{len(texts)} {document_type}s..."
    )

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    results = []

    for document, embedding in zip(
        documents,
        embeddings
    ):

        results.append({

            "id": document["id"],

            "text": document["text"],

            "embedding": embedding.tolist(),

            "metadata": {
                **document.get(
                    "metadata",
                    {}
                ),

                "type": document_type
            }
        })

    return results


def save_embeddings(
    data: list[dict],
    path: str
):

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
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def main():

    print("=" * 70)
    print("BGE-BASE EMBEDDING GENERATION")
    print("=" * 70)

    print("\nLoading model:")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print(
        f"Loaded: {MODEL_NAME}"
    )

    # -----------------------------------------
    # Requirements
    # -----------------------------------------

    requirements = load_documents(
        "output/requirement_documents.json"
    )

    requirement_embeddings = (
        create_embeddings(
            requirements,
            model,
            "requirement"
        )
    )

    save_embeddings(
        requirement_embeddings,
        "output/requirement_embeddings.json"
    )

    # -----------------------------------------
    # Test cases
    # -----------------------------------------

    test_cases = load_documents(
        "output/test_case_documents.json"
    )

    test_case_embeddings = (
        create_embeddings(
            test_cases,
            model,
            "test_case"
        )
    )

    save_embeddings(
        test_case_embeddings,
        "output/test_case_embeddings.json"
    )

    print("\n" + "=" * 70)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"\nRequirements embedded: "
        f"{len(requirement_embeddings)}"
    )

    print(
        f"Test cases embedded: "
        f"{len(test_case_embeddings)}"
    )

    print(
        "\nGenerated files:"
    )

    print(
        "  output/requirement_embeddings.json"
    )

    print(
        "  output/test_case_embeddings.json"
    )


if __name__ == "__main__":
    main()
import asyncio

from app.services.huggingface.embeddings import HuggingFaceEmbeddingsService


async def main() -> None:
    service = HuggingFaceEmbeddingsService()

    result = await service.create_embedding(
        input_text="Python is my favorite programming language."
    )

    print("Dimensions:", len(result))
    print("First 5 values:", result[:5])


asyncio.run(main())

import asyncio
import logging
from typing import List

import yaml
from httpx import AsyncClient, AsyncHTTPTransport, Timeout
from openai import AsyncOpenAI

from config import DEFAULT_MODEL, MAX_CONCURRENT
from schema import ExtractedStakeholderNotes

logger = logging.getLogger(__name__)


class OpenAIManager:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_concurrent: int = MAX_CONCURRENT,
    ):
        self.client = AsyncOpenAI(
            http_client=AsyncClient(
                timeout=Timeout(60.0),
                transport=AsyncHTTPTransport(retries=3),
            ),
        )
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.prompts = self.load_prompts()

    def load_prompts(self) -> dict[str, str]:
        """Load prompts from YAML file."""
        with open("src/prompts.yaml", "r") as file:
            return yaml.safe_load(file)

    async def extract_stakeholder_notes(
        self, chunks: List[str]
    ) -> List[ExtractedStakeholderNotes]:
        """Process structured note extraction concurrently with controlled parallelism."""
        logger.info(
            f"Starting extraction of stakeholder notes from {len(chunks)} chunks"
        )

        tasks = [self._process_with_rate_limit(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and handle exceptions
        filtered_results = [
            r for r in results if isinstance(r, ExtractedStakeholderNotes)
        ]

        logger.info(
            f"Completed extraction. Successfully processed {len(filtered_results)}/{len(results)} chunks"
        )
        return filtered_results

    async def _process_with_rate_limit(
        self, chunk: str
    ) -> ExtractedStakeholderNotes | None:
        async with self.semaphore:
            return await self.process_chunk(chunk)

    async def process_chunk(self, chunk: str) -> ExtractedStakeholderNotes | None:
        """Process a single Slack context."""
        logger.info(
            f"Processing chunk of length {len(chunk)} starting with {chunk[:100]}..."
        )
        try:
            result = await self._create_completion(chunk)
            if result is None:
                logger.warning("No result returned from OpenAI API")
                return None
            logger.info(f"Extracted {len(result.stakeholder_notes)} notes from chunk")
            return result
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            raise

    async def _create_completion(self, chunk: str) -> ExtractedStakeholderNotes | None:
        """Create a single completion for a given Slack context."""
        try:
            logger.debug("Sending request to OpenAI API")
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompts["system_message"]},
                    {
                        "role": "user",
                        "content": self.prompts["user_message"].format(
                            slack_context=chunk
                        ),
                    },
                ],
                response_format=ExtractedStakeholderNotes,
            )
            logger.debug("Received response from OpenAI API")
            result = response.choices[0].message.parsed
            return result
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            raise


# Example usage:
async def main():
    openai_manager = OpenAIManager()

    # load last chunk to be extracted
    with open("data/last_chunk.txt", "r") as file:
        chunk = file.read()

    extracted_notes = await openai_manager.process_chunk(chunk)
    if extracted_notes is not None:
        print(
            f"Extracted {len(extracted_notes.stakeholder_notes)} sets of stakeholder notes"
        )
    else:
        logger.warning("No result returned from OpenAI API")


if __name__ == "__main__":
    asyncio.run(main())

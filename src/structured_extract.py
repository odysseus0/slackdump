import asyncio
import logging
from typing import Callable, List, Optional

import yaml
from httpx import AsyncClient, AsyncHTTPTransport, Timeout
from openai import AsyncOpenAI

from config import DEFAULT_MODEL, MAX_CONCURRENT
from schema import StakeholderNotes

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
        self, chunks: List[str], progress_callback: Optional[Callable[[], None]] = None
    ) -> List[StakeholderNotes]:
        """Extract stakeholder notes with progress tracking."""
        results: List[StakeholderNotes] = []
        for chunk in chunks:
            async with self.semaphore:
                result = await self.process_chunk(chunk)
                if result is not None:
                    results.append(result)
                if progress_callback:
                    progress_callback()
        return results

    async def process_chunk(self, chunk: str) -> StakeholderNotes | None:
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

    async def _create_completion(self, chunk: str) -> StakeholderNotes | None:
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
                response_format=StakeholderNotes,
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

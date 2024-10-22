import asyncio
import logging
from typing import Any, Dict, List

import httpx

from config import PIPEDREAM_WEBHOOK_URL
from postprocess import get_stakeholder_page_id
from schema import PostProcessedStakeholderNote
from stakeholder_name_id import load_stakeholder_page_map

logger = logging.getLogger(__name__)


class NotionManager:
    """Manages interactions with Notion via a Pipedream webhook."""

    def __init__(self, pipedream_webhook_url: str = PIPEDREAM_WEBHOOK_URL):
        """Initialize the NotionManager.

        Args:
            pipedream_webhook_url: The URL of the Pipedream webhook.
        """
        self.pipedream_webhook_url = pipedream_webhook_url
        self.client = None

    async def __aenter__(self):
        """Enter the runtime context and create the HTTP client session."""
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and close the HTTP client session."""
        if self.client:
            await self.client.aclose()

    async def add_postprocessed_notes_to_notion(
        self, post_processed_stakeholder_note: PostProcessedStakeholderNote
    ) -> Dict[str, Any]:
        """Add a single markdown content to Notion."""
        if not self.client:
            raise RuntimeError(
                "HTTP client is not initialized. Use async with context."
            )

        payload = post_processed_stakeholder_note.model_dump()
        logger.debug(
            f"Sending note for {post_processed_stakeholder_note.stakeholder_name} to Notion"
        )

        try:
            response = await self.client.post(
                self.pipedream_webhook_url, json=payload, timeout=30.0
            )
            response.raise_for_status()

            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.content}")

            return {
                "status": "success",
                "status_code": response.status_code,
                "message": response.content.decode("utf-8"),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return {
                "status": "error",
                "status_code": e.response.status_code,
                "message": str(e),
            }
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return {"status": "error", "message": str(e)}

    async def batch_add_postprocessed_notes_to_notion(
        self, pages: List[PostProcessedStakeholderNote]
    ) -> List[Dict[str, Any]]:
        """Add multiple markdown contents to Notion in batch."""
        logger.info(f"Starting batch upload of {len(pages)} notes to Notion")
        tasks = [self.add_postprocessed_notes_to_notion(page) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Completed batch upload to Notion")
        return results


async def main():
    stakeholder_page_map = await load_stakeholder_page_map(
        "data/stakeholder_crm_page_name_id_mapping.csv"
    )

    pages = [
        PostProcessedStakeholderNote(
            stakeholder_name="Coinbase",
            date="2024-07-26",
            title="Page 1",
            summary="A lot of exciting new developments",
            relevant_slack_threads=[],
            full_slack_threads="""
## Slack Thread 1

**John Doe [U123ABC456]:** Hey team, just had a great meeting with Stakeholder 1. They're really excited about our new feature!

**Jane Smith [U789XYZ321]:** That's fantastic news! Did they mention any specific use cases they're interested in?
""",
            stakeholder_page_id=get_stakeholder_page_id(
                stakeholder_page_map, "Coinbase"
            ),
        ),
        PostProcessedStakeholderNote(
            stakeholder_name="OKX",
            date="2024-01-01",
            title="Page 2",
            summary="A lot of exciting new developments",
            relevant_slack_threads=[],
            full_slack_threads="""
## Slack Thread 1

**Emma Davis [U234MNO567]:** Just wrapped up our quarterly review with Stakeholder 2. They're very pleased with our progress!

**Chris Taylor [U876PQR345]:** Great news! Did they give any feedback on the new analytics dashboard?

## Slack Thread 2

**Ryan Green [U765VWX432]:** Heads up, everyone. Stakeholder 2 has requested a demo of our upcoming features next month.

**Emma Davis [U234MNO567]:** Thanks for the info, Ryan. Do we have a specific date yet?

**Ryan Green [U765VWX432]:** Not yet, but they're looking at the second week of April. I'll confirm and send out a calendar invite once we nail down the exact date.

**Chris Taylor [U876PQR345]:** Sounds good. Let's start preparing the demo materials. I'll create a shared doc for us to collaborate on.
""",
            stakeholder_page_id=get_stakeholder_page_id(stakeholder_page_map, "OKX"),
        ),
    ]
    async with NotionManager() as notion_manager:
        results = await notion_manager.batch_add_postprocessed_notes_to_notion(pages)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to create page {i + 1}: {result}")
            else:
                print(f"New page {i + 1} created. {result['message']}")


if __name__ == "__main__":
    asyncio.run(main())

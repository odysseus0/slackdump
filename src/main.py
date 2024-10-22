import asyncio
import logging
from typing import Dict, List

from chunking import ConversationProcessor
from config import (
    DEFAULT_MODEL,
    SLACK_DUMP_PATH,
    STAKEHOLDER_MAPPING_PATH,
)
from logging_config import setup_logging
from notion import NotionManager
from postprocess import post_process
from schema import PostProcessedStakeholderNote, StakeholderNote
from stakeholder_name_id import load_stakeholder_page_map
from structured_extract import OpenAIManager

# Set up logging
logger = setup_logging(level=logging.INFO)  # Change to DEBUG mode


async def process_slack_dump(
    processor: ConversationProcessor, openai_manager: OpenAIManager
) -> List[StakeholderNote]:
    """Process the Slack dump file and extract stakeholder notes."""
    logger.info("Starting to process Slack dump")
    chunks = list(processor.chunk_conversation())
    logger.info(f"Generated {len(chunks)} chunks from the Slack dump")
    logger.debug(f"First chunk sample: {chunks[0][:100]}...")  # Debug sample

    extracted_notes = await openai_manager.extract_stakeholder_notes(chunks)
    logger.info(f"Extracted {len(extracted_notes)} sets of stakeholder notes")
    logger.debug(f"First extracted note sample: {extracted_notes[0]}")  # Debug sample

    all_notes = [note for notes in extracted_notes for note in notes.stakeholder_notes]
    logger.info(f"Total individual stakeholder notes: {len(all_notes)}")
    logger.debug(f"First individual note sample: {all_notes[0]}")  # Debug sample
    return all_notes


async def post_process_notes(
    notes: List[StakeholderNote],
    conversation_processor: ConversationProcessor,
    stakeholder_page_map: Dict[str, str],
) -> List[PostProcessedStakeholderNote]:
    """Post-process the extracted stakeholder notes."""
    logger.info(f"Starting post-processing of {len(notes)} stakeholder notes")
    post_processed = [
        post_process(note, conversation_processor, stakeholder_page_map)
        for note in notes
    ]
    logger.info(f"Completed post-processing. Resulting in {len(post_processed)} notes")
    logger.debug(
        f"First post-processed note sample: {post_processed[0]}"
    )  # Debug sample
    return post_processed


async def main():
    try:
        logger.info("Starting main process")

        # Initialize managers
        logger.info(f"Initializing OpenAIManager with model: {DEFAULT_MODEL}")
        openai_manager = OpenAIManager(model=DEFAULT_MODEL)
        logger.info("Initializing NotionManager")
        notion_manager = NotionManager()

        # Load stakeholder page map
        logger.info(f"Loading stakeholder page map from {STAKEHOLDER_MAPPING_PATH}")
        stakeholder_page_map = await load_stakeholder_page_map(STAKEHOLDER_MAPPING_PATH)
        logger.info(f"Loaded {len(stakeholder_page_map)} stakeholder mappings")
        logger.debug(
            f"Stakeholder map sample: {dict(list(stakeholder_page_map.items())[:5])}"
        )  # Debug sample

        # Process Slack dump
        logger.info(f"Initializing ConversationProcessor with {SLACK_DUMP_PATH}")
        conversation_processor = ConversationProcessor(SLACK_DUMP_PATH)
        extracted_notes = await process_slack_dump(
            conversation_processor, openai_manager
        )
        logger.info(f"Extracted {len(extracted_notes)} stakeholder notes")

        # Post-process notes
        post_processed_notes = await post_process_notes(
            extracted_notes, conversation_processor, stakeholder_page_map
        )
        logger.info(f"Post-processed {len(post_processed_notes)} notes")

        # Add notes to Notion
        logger.info("Starting to add notes to Notion")
        async with notion_manager:
            results = await notion_manager.batch_add_postprocessed_notes_to_notion(
                post_processed_notes
            )

        # Log results
        successful_uploads = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to create page {i + 1}: {result}")
            else:
                logger.info(f"New page {i + 1} created. {result['message']}")
                logger.debug(f"Created page details: {result}")  # Debug details
                successful_uploads += 1

        logger.info(
            f"Successfully uploaded {successful_uploads} out of {len(results)} notes to Notion"
        )
        logger.info("Process completed successfully!")

    except Exception as e:
        logger.exception(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

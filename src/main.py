import asyncio
import logging
from typing import List

from chunking import ConversationProcessor
from config import DEFAULT_MODEL, SLACK_DUMP_PATH
from logging_config import setup_logging
from md_dump import dump_to_markdown
from postprocess import PostProcessedStakeholderNote, post_process
from schema import StakeholderNote
from structured_extract import OpenAIManager

# Set up logging
logger = setup_logging(level=logging.INFO)


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
) -> List[PostProcessedStakeholderNote]:
    """Post-process the extracted stakeholder notes."""
    logger.info(f"Starting post-processing of {len(notes)} stakeholder notes")
    post_processed = [post_process(note, conversation_processor) for note in notes]
    logger.info(f"Completed post-processing. Resulting in {len(post_processed)} notes")
    logger.debug(f"First post-processed note sample: {post_processed[0]}")
    return post_processed


async def main():
    try:
        logger.info("Starting main process")

        # Initialize managers
        logger.info(f"Initializing OpenAIManager with model: {DEFAULT_MODEL}")
        openai_manager = OpenAIManager(model=DEFAULT_MODEL)

        # Process Slack dump
        logger.info(f"Initializing ConversationProcessor with {SLACK_DUMP_PATH}")
        conversation_processor = ConversationProcessor(SLACK_DUMP_PATH)
        extracted_notes = await process_slack_dump(
            conversation_processor, openai_manager
        )
        logger.info(f"Extracted {len(extracted_notes)} stakeholder notes")

        # Post-process notes
        post_processed_notes = await post_process_notes(
            extracted_notes, conversation_processor
        )
        logger.info(f"Post-processed {len(post_processed_notes)} notes")

        # Dump to markdown
        logger.info("Dumping post-processed notes to markdown files")
        dump_to_markdown(post_processed_notes)
        logger.info("Markdown dump completed")

        logger.info("Process completed successfully!")

    except Exception as e:
        logger.exception(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

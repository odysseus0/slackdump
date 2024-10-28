import asyncio
import logging
import shutil
from pathlib import Path
from typing import List

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from chunking import ConversationProcessor
from config import DEFAULT_MODEL
from md_dump import dump_to_markdown
from postprocess import post_process
from schema import PostProcessedStakeholderNote, StakeholderNote
from slack_dump.slack_dump import SlackDumpManager
from structured_extract import OpenAIManager

# Create a single console instance
console = Console()


# Update logging setup to use Rich
def setup_rich_logging(level=logging.INFO):
    """Set up Rich logging handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )
    return logging.getLogger("rich")


logger = setup_rich_logging(level=logging.INFO)


# 1. Move progress bar configuration to a separate function
def create_progress_bar() -> Progress:
    """Create a configured progress bar instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )


# 2. Simplify process_slack_dump function
async def process_slack_dump(
    processor: ConversationProcessor, openai_manager: OpenAIManager
) -> List[StakeholderNote]:
    """Process the Slack dump file and extract stakeholder notes."""
    chunks = list(processor.chunk_conversation())
    logger.debug(f"Generated {len(chunks)} chunks from Slack dump")  # Changed to DEBUG

    progress = create_progress_bar()
    with progress:
        task = progress.add_task("Extracting stakeholder notes...", total=len(chunks))
        extracted_notes = await openai_manager.extract_stakeholder_notes(
            chunks, progress_callback=lambda: progress.advance(task)
        )

    all_notes = [note for notes in extracted_notes for note in notes.stakeholder_notes]
    logger.info(f"Extracted {len(all_notes)} stakeholder notes")
    return all_notes


# 3. Simplify run_pipeline by extracting initialization logic
async def initialize_processors(
    model: str, temp_dump_path: Path
) -> tuple[SlackDumpManager, OpenAIManager, ConversationProcessor]:
    """Initialize all necessary processors."""
    slack_manager = SlackDumpManager(console=console)
    slack_dump = await slack_manager.export_slack_data(temp_dump_path)

    openai_manager = OpenAIManager(model=model)
    conversation_processor = ConversationProcessor(slack_dump)

    return slack_manager, openai_manager, conversation_processor


async def post_process_notes(
    notes: List[StakeholderNote],
    conversation_processor: ConversationProcessor,
) -> List[PostProcessedStakeholderNote]:
    """Post-process the extracted stakeholder notes."""
    logger.debug(
        f"Starting post-processing of {len(notes)} stakeholder notes"
    )  # Changed to DEBUG
    post_processed = [post_process(note, conversation_processor) for note in notes]
    logger.info(f"Completed post-processing. Resulting in {len(post_processed)} notes")

    if post_processed:  # Add null check
        logger.debug(f"Sample post-processed note: {post_processed[0]}")

    return post_processed


async def run_pipeline(
    model: str,
    keep_temp: bool,
    output_dir: Path,
    temp_dump_path: Path,
) -> None:
    """Run the main processing pipeline.

    Args:
        model: OpenAI model to use for extraction
        keep_temp: Whether to keep temporary files
        output_dir: Directory to store output markdown files
        temp_dump_path: Path for temporary Slack dump
    """
    try:
        if temp_dump_path.exists():
            logger.warning("Found existing temporary dump file, removing it...")
            cleanup_temp_files(temp_dump_path)

        # Initialize processors
        _, openai_manager, conversation_processor = await initialize_processors(
            model, temp_dump_path
        )

        # Run extraction pipeline
        extracted_notes = await process_slack_dump(
            conversation_processor, openai_manager
        )

        # Post-process notes
        post_processed_notes = await post_process_notes(
            extracted_notes, conversation_processor
        )

        # Add consolidated logging
        logger.info("Pipeline summary:")
        logger.info(f"- Processed {len(extracted_notes)} raw notes")
        logger.info(f"- Generated {len(post_processed_notes)} processed notes")
        logger.info(f"- Output directory: {output_dir}")

        dump_to_markdown(post_processed_notes, output_dir)
        logger.info("✓ Process completed successfully!")

    except Exception as e:
        cleanup_temp_files(temp_dump_path)
        raise e
    finally:
        if not keep_temp:
            logger.info("Cleaning up temporary files...")
            cleanup_temp_files(temp_dump_path)
        else:
            logger.info(f"Temporary files kept for inspection at: {temp_dump_path}")


@click.command()
@click.option(
    "--model",
    "-m",
    default=DEFAULT_MODEL,
    help="OpenAI model to use for extraction",
)
@click.option(
    "--keep-temp",
    is_flag=True,
    help="Keep temporary Slack dump files for inspection",
)
@click.option(
    "--output",
    "-o",
    default="./output",
    help="Output directory for markdown files",
)
def main(model: str, keep_temp: bool, output: str):
    """Process Slack conversations and extract stakeholder notes."""
    output_dir = Path(output)
    temp_dump_path = Path("./temp_dump")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(run_pipeline(model, keep_temp, output_dir, temp_dump_path))
    except Exception as e:
        console.print_exception(show_locals=True)
        raise click.ClickException(str(e))


def cleanup_temp_files(path: Path) -> None:
    """Clean up temporary files and directories.

    Args:
        path: Path to the temporary files/directory to clean up.
    """
    if path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    main()

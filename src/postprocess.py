import logging
from typing import Dict, List

from rapidfuzz import fuzz, process

from chunking import ConversationProcessor
from schema import PostProcessedStakeholderNote, StakeholderNote

logger = logging.getLogger(__name__)


def get_stakeholder_page_id(
    stakeholder_page_map: Dict[str, str],
    stakeholder_name: str,
    score_cutoff: float = 80.0,
) -> str | None:
    """
    Find the best matching stakeholder name using fuzzy search and return the corresponding page ID.

    This function is designed to handle stakeholder names extracted from unstructured documents,
    accounting for potential discrepancies such as capitalization differences or missing/additional words.

    Args:
        stakeholder_page_map: A dictionary mapping stakeholder names to page IDs.
        stakeholder_name: The stakeholder name to search for.
        score_cutoff: The minimum similarity score to consider a match (default: 80.0).

    Returns:
        The page ID of the best matching stakeholder, or None if no match is found above the score cutoff.
    """
    if not stakeholder_page_map:
        logger.warning("Empty stakeholder_page_map provided")
        return None

    stakeholder_names = list(stakeholder_page_map.keys())
    result = process.extractOne(
        stakeholder_name,
        stakeholder_names,
        scorer=fuzz.WRatio,
        score_cutoff=score_cutoff,
    )

    if result is None:
        logger.info(f"No match found for stakeholder name: {stakeholder_name}")
        return None

    best_match, score, _ = result
    logger.debug(
        f"Best match for '{stakeholder_name}': '{best_match}' (score: {score})"
    )
    return stakeholder_page_map.get(best_match)


def post_process(
    note: StakeholderNote,
    conversation_processor: ConversationProcessor,
) -> PostProcessedStakeholderNote:
    """
    Post-process a StakeholderNote by retrieving full Slack thread content and matching stakeholder ID.

    Args:
        note: The StakeholderNote to be post-processed.
        conversation_processor: An instance of ConversationProcessor to retrieve thread content.

    Returns:
        A PostProcessedStakeholderNote with full Slack thread content as markdown and matched stakeholder ID.
    """
    logger.info(f"Post-processing note for stakeholder: {note.stakeholder_name}")

    full_threads: List[str] = []
    for thread_fingerprint in note.relevant_slack_threads:
        if thread_fingerprint in conversation_processor.thread_map:
            full_threads.append(
                conversation_processor.get_thread_content(thread_fingerprint)
            )
            logger.debug(f"Retrieved full content for thread: {thread_fingerprint}")
        else:
            logger.warning(
                f"Thread fingerprint '{thread_fingerprint}' not found in conversation"
            )

    full_threads_markdown = "\n\n".join(full_threads)
    logger.debug(f"Combined {len(full_threads)} threads into markdown")

    post_processed_note = PostProcessedStakeholderNote(
        **note.model_dump(),
        full_slack_threads=full_threads_markdown,
    )
    logger.info(f"Post-processing completed for stakeholder: {note.stakeholder_name}")
    return post_processed_note

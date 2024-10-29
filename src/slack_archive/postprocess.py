import logging

from slack_archive.chunking import ConversationProcessor
from slack_archive.schema import PostProcessedStakeholderNote, StakeholderNote

logger = logging.getLogger(__name__)


def post_process(
    note: StakeholderNote,
    conversation_processor: ConversationProcessor,
) -> PostProcessedStakeholderNote:
    """
    Post-process a StakeholderNote by retrieving full Slack thread content.

    Args:
        note: The StakeholderNote to be post-processed.
        conversation_processor: An instance of ConversationProcessor to retrieve thread
        content.

    Returns:
        A PostProcessedStakeholderNote with full Slack thread content as markdown.
    """
    logger.info(f"Post-processing note for stakeholder: {note.stakeholder_name}")

    full_threads: list[str] = []
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

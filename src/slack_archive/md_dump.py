from pathlib import Path

from slack_archive.schema import PostProcessedStakeholderNote


def dump_to_markdown(
    post_processed_notes: list[PostProcessedStakeholderNote], output_path: Path
):
    print("Dumping to markdown")

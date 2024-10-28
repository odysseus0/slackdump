from pathlib import Path
from typing import List

from schema import PostProcessedStakeholderNote


def dump_to_markdown(
    post_processed_notes: List[PostProcessedStakeholderNote], output_path: Path
):
    print("Dumping to markdown")

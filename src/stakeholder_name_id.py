"""Module for extracting page title to ID mapping from Notion JSON response."""

import csv
import json
from typing import Dict


def extract_title_id_mapping(json_response: Dict) -> Dict[str, str]:
    """
    Extract page title to ID mapping from Notion JSON response.

    Args:
        json_response: The JSON response from Notion API.

    Returns:
        A dictionary mapping page titles to their corresponding block IDs.
    """
    page_name_id_mapping = {}
    blocks = json_response["recordMap"]["block"]
    print(f"Total number of blocks: {len(blocks)}")

    for block_id, block_data in blocks.items():
        try:
            title = block_data["value"]["value"]["properties"]["title"][0][0]
            page_name_id_mapping[title] = block_id
        except KeyError:
            print(f"KeyError for block ID: {block_id}")
            continue

    print(f"Total number of page name to ID mappings: {len(page_name_id_mapping)}")
    return page_name_id_mapping


def save_mapping_to_csv(mapping: Dict[str, str], output_file: str) -> None:
    """
    Save the page name to ID mapping to a CSV file.

    Args:
        mapping: A dictionary containing page name to ID mappings.
        output_file: The path to the output CSV file.
    """
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Page Name", "ID"])
        for page_name, id in mapping.items():
            writer.writerow([page_name, id])


async def load_stakeholder_page_map(file_path: str) -> Dict[str, str]:
    """Load the stakeholder page map from a CSV file."""
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        return {row[0]: row[1] for row in reader}


def main() -> None:
    input_file = "data/stakeholder_crm.json"
    output_file = "data/stakeholder_crm_page_name_id_mapping.csv"

    with open(input_file, "r") as file:
        response = json.load(file)

    page_name_id_mapping = extract_title_id_mapping(response)
    save_mapping_to_csv(page_name_id_mapping, output_file)


if __name__ == "__main__":
    main()

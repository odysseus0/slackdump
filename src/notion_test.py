from notion import NotionManager


def generate_content(unit, count):
    if unit == "words":
        return "# Test Page\n\n" + "word " * count
    elif unit == "blocks":
        return "# Test Page\n\n" + "\n\n".join([f"Block {i+1}" for i in range(count)])


def test_notion_limit(unit, magnitude):
    pipedream_webhook_url = "https://eoyd1oqis8y2mhq.m.pipedream.net"
    notion_manager = NotionManager(pipedream_webhook_url)

    count = 10**magnitude
    content = generate_content(unit, count)
    page_name = f"Test Page - 10^{magnitude} {unit}"

    print(f"Attempting to add page with roughly 10^{magnitude} {unit}...")

    try:
        notion_manager.add_postprocessed_notes_to_notion(content, page_name)
        print(f"Success: Added page with roughly 10^{magnitude} {unit}")
    except Exception as e:
        print(f"Failed: {str(e)}")


# Run the tests
if __name__ == "__main__":
    # print("Testing word limit:")
    # for magnitude in range(2, 7):  # This will test 10^2 to 10^6 words
    #     test_notion_limit("words", magnitude)
    #     print("---")

    print("\nTesting block limit:")
    for magnitude in [2, 3]:  # This will test 10^1 to 10^4 blocks
        test_notion_limit("blocks", magnitude)
        print("---")

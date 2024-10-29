import re
from collections.abc import Generator, Iterator
from pathlib import Path

import tiktoken

from slack_archive.config import (
    SLACK_DUMP_PATH,
)


class Thread:
    def __init__(self, fingerprint: str, content: str):
        self.fingerprint = fingerprint.strip()
        self.content = content

    def __str__(self):
        return f"{self.fingerprint}\n{self.content}"

    def __repr__(self):
        return f"Thread(fingerprint={self.fingerprint}, content={self.content[:100]})"


class ConversationProcessor:
    """
    Processes and chunks slack dump data.

    Reads a slack dump file, extracts individual threads, and provides methods
    to chunk the conversation into smaller parts based on a specified chunk size.

    Attributes:
        file_path: Path to the slack dump file.
        model_name: Name of the GPT model to use for tokenization.
        chunk_size: Maximum number of tokens for each chunk.
        encoding: Tokenizer for the specified model.
        thread_map: Map of thread fingerprints to Thread objects.
    """

    # this is the fingerprint of message. example:
    # > alex [U03ERC46NKA] @ 06/01/2023 11:44:42 Z:
    THREAD_PATTERN = r"^(> .+? \@\s*\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} Z:)"

    def __init__(
        self, file_path: Path, model_name: str = "gpt-4o", chunk_size: int = 28000
    ):
        self.file_path = file_path
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.encoding = tiktoken.encoding_for_model(model_name)

        self.thread_map = self._extract_threads()

    def _extract_threads(self) -> dict[str, Thread]:
        """
        Extract individual threads from the slack dump file.

        Returns:
            A dictionary mapping thread fingerprints to Thread objects.
        """
        with open(self.file_path, encoding="utf-8") as file:
            conversation_text = file.read()

        threads = re.split(self.THREAD_PATTERN, conversation_text, flags=re.MULTILINE)
        return {
            threads[i].strip().removeprefix("> "): Thread(
                threads[i], threads[i] + threads[i + 1]
            )
            for i in range(1, len(threads) - 1, 2)
        }

    def chunk_conversation(self) -> Generator[str, None, None]:
        """
        Chunk the conversation into smaller parts based on the specified chunk size.

        Yields chunks of the conversation, each within the specified chunk size.
        """
        current_chunk = ""
        current_token_count = 0

        for thread in self.get_threads():
            thread_tokens = self.encoding.encode(str(thread))

            if current_token_count + len(thread_tokens) <= self.chunk_size:
                current_chunk += str(thread)
                current_token_count += len(thread_tokens)
            else:
                yield current_chunk
                current_chunk = str(thread)
                current_token_count = len(thread_tokens)

        if current_chunk:
            yield current_chunk

    def get_thread_content(self, fingerprint: str) -> str:
        """
        Retrieve the full content of a specific thread.

        Args:
            fingerprint: The fingerprint of the desired thread.

        Returns the full content of the specified thread.
        """
        return str(self.thread_map[fingerprint])

    def get_threads(self) -> Generator[Thread, None, None]:
        """
        Get a generator of all Thread objects in the conversation.

        Yields Thread objects representing individual messages in the conversation.
        """
        yield from self.thread_map.values()

    def get_fingerprints(self) -> Iterator[str]:
        """
        Get an iterator of all thread fingerprints in the conversation.

        Returns an iterator of thread fingerprints.
        """
        return iter(self.thread_map.keys())


# Example usage
if __name__ == "__main__":
    processor = ConversationProcessor(SLACK_DUMP_PATH)
    # Print some pairs from the thread_map
    for fingerprint, thread in list(processor.thread_map.items())[:5]:
        print(f"Fingerprint: {fingerprint}")
        print(f"Thread content (first 100 chars): \n{str(thread)[:100]}...")
        print()
    last_chunk_save_path = "data/last_chunk.txt"

    # More efficient way to get the first 3 items
    for i, fingerprint in enumerate(processor.get_fingerprints()):
        if i >= 3:  # noqa: PLR2004
            break
        thread = processor.get_thread_content(fingerprint)
        print(f"Fingerprint: {fingerprint}")
        print(f"Full text: {thread[:100]}...")
        print()

    # Example of using the chunks
    for i, chunk in enumerate(processor.chunk_conversation()):
        print(
            f"Chunk {i + 1} (Token Count: "
            f"{len(processor.encoding.encode(chunk))}):\n"
            f"{chunk[:100]}...\n"
        )

    # Example of retrieving a specific thread
    sample_fingerprint = next(processor.get_fingerprints())  # Get the first fingerprint
    print(f"Full text for fingerprint '{sample_fingerprint}':")
    print(processor.get_thread_content(sample_fingerprint))

    # save as chunk as more information rich example for unit testing in other modules
    chunks = list(processor.chunk_conversation())
    if chunks:
        last_chunk = chunks[-1]
        with open(last_chunk_save_path, "w", encoding="utf-8") as file:
            file.write(last_chunk)
        print(f"Last chunk saved to {last_chunk_save_path}")
    else:
        print("No chunks available to save.")

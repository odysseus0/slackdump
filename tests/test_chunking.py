import pytest

from config import SLACK_DUMP_PATH
from src.chunking import ConversationProcessor, Thread


@pytest.fixture
def processor():
    return ConversationProcessor(SLACK_DUMP_PATH)


def test_thread_map(processor):
    thread_map = processor.thread_map
    assert len(thread_map) > 0
    sample_fingerprint = next(iter(thread_map))
    assert isinstance(sample_fingerprint, str)
    assert isinstance(thread_map[sample_fingerprint], Thread)


def test_get_fingerprints(processor):
    fingerprints = list(processor.get_fingerprints())
    assert len(fingerprints) > 0
    assert all(isinstance(f, str) for f in fingerprints)


def test_get_thread_content(processor):
    sample_fingerprint = next(processor.get_fingerprints())
    thread_content = processor.get_thread_content(sample_fingerprint)
    assert isinstance(thread_content, str)
    assert thread_content.startswith(sample_fingerprint)


def test_get_thread_content_specific(processor):
    sample_fingerprint = "tesa [U06TUB9EW2Y] @ 22/09/2024 09:27:04 Z:"
    thread_content = processor.get_thread_content(sample_fingerprint)
    assert isinstance(thread_content, str)
    assert thread_content.startswith(sample_fingerprint)


def test_chunk_conversation(processor):
    chunks = list(processor.chunk_conversation())
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, str)
        assert len(processor.encoding.encode(chunk)) <= processor.chunk_size


def test_last_chunk_save(processor, tmp_path):
    last_chunk_save_path = tmp_path / "last_chunk.txt"
    chunks = list(processor.chunk_conversation())
    if chunks:
        last_chunk = chunks[-1]
        with open(last_chunk_save_path, "w", encoding="utf-8") as file:
            file.write(last_chunk)

        with open(last_chunk_save_path, "r", encoding="utf-8") as file:
            saved_content = file.read()

        assert saved_content == last_chunk
    else:
        pytest.skip("No chunks available to save.")

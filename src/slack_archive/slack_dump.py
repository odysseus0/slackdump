import asyncio
import platform
from importlib import resources
from pathlib import Path

from rich.console import Console


class SlackDumpManager:
    """Manages slackdump binary execution."""

    def __init__(self, console: Console | None = None):
        """Initialize SlackDumpManager."""
        self.console = console or Console()
        self.binary_name = (
            "slackdump.exe" if platform.system().lower() == "windows" else "slackdump"
        )
        # Get binary from package installation directory
        self.binary_path = Path(
            str(resources.files("slack_dump") / "bin" / self.binary_name)
        )

        if not self.binary_path.exists():
            raise RuntimeError(
                f"Slackdump binary not found at {self.binary_path}. "
                "Please ensure the package was installed correctly."
            )

    async def get_version(self) -> str:
        """Get slackdump binary version."""
        process = await asyncio.create_subprocess_exec(
            str(self.binary_path),
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return stdout.decode().strip()

    async def export_slack_data(self, output_path: Path) -> Path:
        """Run slackdump export and return path to exported data."""
        process = await asyncio.create_subprocess_exec(
            str(self.binary_path),
            "--export",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Slackdump failed: {stderr.decode()}")

        return output_path

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *_):
        """Async context manager exit."""
        pass

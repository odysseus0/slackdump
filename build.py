"""Build script to download and install slackdump binary during package installation."""

import asyncio
import platform
import shutil
import tarfile
import zipfile
from pathlib import Path

import httpx
from github import Github
from rich.console import Console

SLACKDUMP_VERSION = "v2.5.15"
REPO_OWNER = "rusq"
REPO_NAME = "slackdump"


def get_platform_asset() -> tuple[str, str]:
    """Get platform-specific asset name and binary name.

    Returns:
        tuple[str, str]: A tuple containing (asset_filename, binary_name)
    """
    system = platform.system()
    machine = platform.machine().lower()

    # Map system names to match release asset naming
    system_map = {
        "Darwin": "macOS",
        "Windows": "Windows",
        "Linux": "Linux",
        "FreeBSD": "Freebsd",
        "OpenBSD": "Openbsd",
        "NetBSD": "Netbsd",
    }

    # Map machine architectures to asset naming convention
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "arm64": "arm64",
        "i386": "i386",
        "x86": "i386",
    }

    system_name = system_map.get(system)
    if not system_name:
        raise ValueError(f"Unsupported operating system: {system}")

    arch = arch_map.get(machine, machine)

    # Binary name is platform dependent
    binary_name = "slackdump.exe" if system == "Windows" else "slackdump"

    # Asset name follows pattern: slackdump_<OS>_<arch>.<ext>
    extension = "zip" if system == "Windows" else "tar.gz"
    asset_name = f"slackdump_{system_name}_{arch}.{extension}"

    return asset_name, binary_name


async def download_and_extract_binary(console: Console) -> None:
    """Download and extract slackdump binary to package directory."""
    asset_name, binary_name = get_platform_asset()

    # Use PyGithub to get the release asset
    g = Github()
    repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    release = repo.get_release(SLACKDUMP_VERSION)

    # Find the correct asset
    asset = next(
        (asset for asset in release.get_assets() if asset.name == asset_name), None
    )
    if not asset:
        raise ValueError(
            f"Could not find asset {asset_name} in release {SLACKDUMP_VERSION}"
        )

    # Create bin directory in package
    bin_dir = Path("src/slack_dump/bin")
    bin_dir.mkdir(parents=True, exist_ok=True)
    binary_path = bin_dir / binary_name

    console.print(f"Downloading slackdump from {asset.browser_download_url}")

    # Download and extract binary
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", asset.browser_download_url) as response:
            response.raise_for_status()
            download_path = Path(asset_name)

            with open(download_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

        # Extract binary
        if asset_name.endswith(".zip"):
            with zipfile.ZipFile(download_path) as z:
                with z.open(binary_name) as zf, open(binary_path, "wb") as f:
                    shutil.copyfileobj(zf, f)
        else:
            with tarfile.open(download_path) as tar:
                member = tar.getmember(binary_name)
                tf = tar.extractfile(member)
                if tf is None:
                    raise ValueError(f"Failed to extract {binary_name} from archive")
                with tf as tf_handle, open(binary_path, "wb") as f:
                    shutil.copyfileobj(tf_handle, f)

        # Make binary executable on Unix-like systems
        if platform.system() != "Windows":
            binary_path.chmod(0o755)

        # Cleanup downloaded archive
        download_path.unlink()


async def install_binary():
    """Install slackdump binary to user's local binary directory.

    This function is called during package installation via pipx or pip.
    It downloads and installs the slackdump binary to the package's bin directory.
    """
    console = Console()
    try:
        await download_and_extract_binary(console)
    except Exception as e:
        console.print(f"[red]Failed to download slackdump binary: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(install_binary())

#!/usr/bin/env python3
"""Capture TUI screenshot for documentation.

This script captures a screenshot of the PackageBrowserApp TUI
with sample package data and saves it to docs/tui-screenshot.svg.
"""

import asyncio
from pathlib import Path

from apt_registry_explorer.packages import PackageMetadata
from apt_registry_explorer.tui import PackageBrowserApp


def create_sample_packages() -> list[PackageMetadata]:
    """Create sample package data for screenshot."""
    return [
        PackageMetadata(
            package="nginx",
            version="1.18.0-6ubuntu14.4",
            architecture="amd64",
            maintainer="Ubuntu Developers",
            installed_size="1024",
            depends="libc6 (>= 2.34), libssl3",
            description="Small, powerful, scalable web/proxy server",
        ),
        PackageMetadata(
            package="python3",
            version="3.10.6-1~22.04.1",
            architecture="amd64",
            maintainer="Ubuntu Developers",
            installed_size="512",
            depends="python3.10 (>= 3.10.6-1~)",
            description="Interactive high-level object-oriented language",
        ),
        PackageMetadata(
            package="curl",
            version="7.81.0-1ubuntu1.18",
            architecture="amd64",
            maintainer="Ubuntu Developers",
            installed_size="384",
            depends="libc6 (>= 2.34), libcurl4",
            description="Command line tool for transferring data with URL syntax",
        ),
    ]


async def capture_screenshot() -> None:
    """Capture TUI screenshot and save to docs/tui-screenshot.svg."""
    packages = create_sample_packages()
    app = PackageBrowserApp(packages)

    async with app.run_test() as pilot:
        # Wait for app to render
        await pilot.pause(0.5)

        # Save screenshot
        screenshot_path = Path("docs/tui-screenshot.svg")
        screenshot_path.parent.mkdir(exist_ok=True)
        pilot.app.save_screenshot(screenshot_path)

        print(f"✅ Screenshot saved to {screenshot_path}")


def main() -> None:
    """Main entry point."""
    asyncio.run(capture_screenshot())


if __name__ == "__main__":
    main()

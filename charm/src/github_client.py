#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""GitHub repository management for the collector charm."""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GitHubClient:
    """Handles GitHub repository operations for the collector charm."""
    
    @staticmethod
    def fetch_collector(config: Dict[str, Any], dest_dir: str = "/opt/collector") -> None:
        """Fetch the collector from GitHub repository.
        
        Args:
            config: Configuration dictionary containing GitHub settings
            dest_dir: Destination directory for the collector files
        """
        from subprocess import run
        
        token = config.get("github_token")
        repo_url = config.get("github_repo")
        tag = config.get("release_tag")
        subdir = config.get("sub_directory")
        clone_dir = "/tmp/collector-repo"

        # Insert token into repo URL
        parts = repo_url.split("https://", 1)[1]
        authed_url = f"https://oauth2:{token}@{parts}"

        logger.info("Fetching collector from GitHub...")

        # Clean up if needed
        run(["rm", "-rf", clone_dir], check=True)

        # Clone with sparse-checkout from a tag
        run([
            "git", "clone", "--depth=1", "--filter=blob:none", "--sparse", "--branch", tag,
            authed_url, clone_dir
        ], check=True)

        if subdir:  # If a sub-directory is specified, set sparse-checkout to that directory
            logger.info(f"Setting sparse-checkout to sub-directory: {subdir}")
            run(["git", "-C", clone_dir, "sparse-checkout", "set", subdir], check=True)

        run(["rm", "-rf", dest_dir], check=True)

        logger.info(f"Copying files from {clone_dir}/{subdir} to {dest_dir}...")
        os.makedirs(dest_dir, exist_ok=True)
        run(["cp", "-r", f"{clone_dir}/{subdir}/.", dest_dir], check=True)

        logger.info("Collector fetched and copied successfully.")

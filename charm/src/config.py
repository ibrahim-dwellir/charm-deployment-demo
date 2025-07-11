#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""Configuration management for the collector charm."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Handles configuration validation for the collector charm."""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """Validate the configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            ("frequency", "The 'frequency' configuration option is required."),
            ("collector_name", "The 'collector-name' configuration option is required."),
            ("haproxy_name", "The 'haproxy-name' configuration option is required."),
            ("haproxy_url", "The 'haproxy-url' configuration option is required."),
            ("haproxy_username", "The 'haproxy-username' configuration option is required."),
            ("haproxy_password", "The 'haproxy-password' configuration option is required."),
            ("github_repo", "The 'github-repo' configuration option is required."),
            ("github_token", "The 'github-token' configuration option is required."),
            ("release_tag", "The 'release-tag' configuration option is required."),
        ]
        
        for field, error_msg in required_fields:
            if not config.get(field):
                raise ValueError(error_msg)
        
        # Validate URL formats
        if not config.get("haproxy_url", "").startswith("http"):
            raise ValueError("The 'haproxy-url' must be a valid URL starting with 'http' or 'https'.")
        
        if not config.get("github_repo", "").startswith("https://"):
            raise ValueError("The 'github-repo' must be a valid HTTPS URL.")


class ConfigManager:
    """Manages configuration retrieval and conversion."""
    
    def __init__(self, model_config):
        """Initialize with model config object."""
        self.model_config = model_config
    
    def get_config(self) -> Dict[str, Any]:
        """Get the configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            "frequency": self.model_config.get("frequency", 60),
            "collector_name": self.model_config.get("collector-name"),
            "haproxy_name": self.model_config.get("haproxy-name"),
            "haproxy_url": self.model_config.get("haproxy-url"),
            "haproxy_username": self.model_config.get("haproxy-username"),
            "haproxy_password": self.model_config.get("haproxy-password"),
            "github_repo": self.model_config.get("github-repo"),
            "github_token": self.model_config.get("github-token"),
            "release_tag": self.model_config.get("release-tag"),
            "sub_directory": self.model_config.get("sub-directory"),
        }

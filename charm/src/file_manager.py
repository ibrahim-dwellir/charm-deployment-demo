#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""File and environment management for the collector charm."""

import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FileManager:
    """Handles file operations for the collector charm."""
    
    CONFIG_DIR = ".collector"
    CONFIG_FILE = ".collector/config.json"
    ENV_FILE_PATH = "/etc/default/collector_envs"
    DEST_DIR = "/opt/collector"
    
    @classmethod
    def store_config(cls, config: Dict[str, Any]) -> None:
        """Store the configuration in a file.
        
        Args:
            config: Configuration dictionary to store
        """
        from subprocess import run
        
        # Store configuration in .collector folder
        run(["mkdir", "-p", cls.CONFIG_DIR])
        with open(cls.CONFIG_FILE, "w") as config_file:
            config_file.write(json.dumps(config))
    
    @classmethod
    def read_config(cls) -> Dict[str, Any]:
        """Read the configuration from a file.
        
        Returns:
            Configuration dictionary, empty dict if file not found
        """
        try:
            with open(cls.CONFIG_FILE, "r") as config_file:
                return json.loads(config_file.read())
        except FileNotFoundError:
            logger.error("Configuration file not found.")
            return {}
        except json.JSONDecodeError:
            logger.error("Error decoding configuration file.")
            return {}
    
    @classmethod
    def generate_environment_file(cls, config: Dict[str, Any]) -> None:
        """Generate the environment file for the collector service.
        
        Args:
            config: Configuration dictionary containing HAProxy credentials
        """
        with open(cls.ENV_FILE_PATH, "w") as env_file:
            env_file.write(f"HAPROXY_URL={config['haproxy_url']}\n")
            env_file.write(f"HAPROXY_USERNAME={config['haproxy_username']}\n")
            env_file.write(f"HAPROXY_PASSWORD={config['haproxy_password']}\n")

        logger.info(f"Environment file created at {cls.ENV_FILE_PATH}")
    
    @classmethod
    def generate_service_file(cls, config: Dict[str, Any]) -> None:
        """Generate the service file for the collector.
        
        Args:
            config: Configuration dictionary containing service settings
        """
        from subprocess import run
        from templates import SERVICE_TEMPLATE, TIMER_TEMPLATE
        
        service_file_path = "/etc/systemd/system/collector.service"
        entrypoint = f"python3 {cls.DEST_DIR}/main.py"

        with open(service_file_path, "w") as service_file:
            service_file.write(SERVICE_TEMPLATE.substitute(entrypoint=entrypoint))

        logger.info(f"Service file created at {service_file_path}")

        # Generate the timer file
        timer_file_path = "/etc/systemd/system/collector.timer"
        interval = config.get("frequency")

        with open(timer_file_path, "w") as timer_file:
            timer_file.write(TIMER_TEMPLATE.substitute(interval=interval))

        logger.info(f"Timer file created at {timer_file_path}")

        # Reload systemd to recognize the new service and timer
        run(["systemctl", "daemon-reload"], check=True)
        logger.info("Systemd daemon reloaded to recognize new service and timer.")
    
    @classmethod
    def install_dependencies(cls) -> None:
        """Install necessary dependencies for the collector."""
        from subprocess import run
        
        run(["apt", "install", "-y", "python3-pip"])
        run(["pip3", "install", "-r", f"{cls.DEST_DIR}/requirements.txt"], check=True)

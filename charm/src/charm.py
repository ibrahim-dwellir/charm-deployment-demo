#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""Charm the application."""

from subprocess import run
from string import Template

import logging

import ops
import json
import time

logger = logging.getLogger(__name__)

SERVICE_TEMPLATE_STRING = \
"""
[Unit]
Description=Collector Service
After=network.target

[Service]
EnvironmentFile=/etc/default/collector_envs
ExecStart=${entrypoint}
User=ubuntu
Group=ubuntu
Type=oneshot

[Install]
WantedBy=multi-user.target
"""

SERVICE_TEMPLATE = Template(SERVICE_TEMPLATE_STRING)

TIMER_TEMPLATE_STRING = \
"""
[Unit]
Description="Runs the collector periodically"

[Timer]
OnUnitInactiveSec=${interval}seconds
Unit=collector.service


[Install]
WantedBy=multi-user.target
"""

TIMER_TEMPLATE = Template(TIMER_TEMPLATE_STRING)

class CollectorCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)

        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(self.on['start'].action, self._on_service_start)
        framework.observe(self.on['stop'].action, self._on_service_stop)
        framework.observe(self.on['restart'].action, self._on_service_restart)

    def _on_install(self, event: ops.InstallEvent):
        config = self._get_config()
        try:
            logger.info("Validating configuration...")
            self.model.unit.status = ops.MaintenanceStatus("Validating configuration...")

            self._validate_config(config)

            logger.info("Configuration validated successfully.")
            self.model.unit.status = ops.MaintenanceStatus("Configuration validated successfully.")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            self.model.unit.status = ops.BlockedStatus(f"Configuration error: {e}")
            return

        # Store the configuration
        self._store_config(config)
        
        # Generate the environment file
        self._generate_environment_file(config)
        
        try:
            # Install dependencies
            logger.info("Installing dependencies...")
            self.model.unit.status = ops.MaintenanceStatus("Installing dependencies...")
            run(["apt", "install", "-y", "python3-pip"])
            run(["apt", "install", "-y","python-is-python3"])

            logger.info("Dependencies installed successfully.")
            self.model.unit.status = ops.ActiveStatus("Running")
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            self.model.unit.status = ops.BlockedStatus(f"Dependency installation failed: {e}")
            return

            
    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        """Handle configuration changes."""
        logger.info("Configuration changed, updating...")
        self.model.unit.status = ops.MaintenanceStatus("Updating configuration...")

        # Read the old and new configurations
        old_config = self._read_config()

        # Get the new configuration from the event
        new_config = self._get_config()

        logger.info(f"Old configuration: {old_config}")
        logger.info(f"New configuration: {new_config}")

        try:
            # Validate the new configuration
            self._validate_config(new_config)
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            self.model.unit.status = ops.BlockedStatus(f"Configuration error: {e}")
            return

        # Check for changes in the configuration
        changed_configs = {field: new_config[field] for field in new_config if old_config.get(field) != new_config[field]}

        # If there are changes, update the configuration and generate the environment file
        if changed_configs:
            logger.info(f"Configuration changed: {changed_configs}")
            self._store_config(new_config)

            # Generate the environment file
            self._generate_environment_file(new_config)
            logger.info("Configuration updated successfully.")
            self._on_service_restart(event)
        else:
            logger.info("No configuration changes detected.")
            self.model.unit.status = ops.ActiveStatus("Running")


    def _validate_config(self, config: map):
        """Validate the configuration."""
        if not config.get("frequency"):
            raise ValueError("The 'frequency' configuration option is required.")
        if not config.get("collector_name"):
            raise ValueError("The 'collector-name' configuration option is required.")
        if not config.get("haproxy_name"):
            raise ValueError("The 'haproxy-name' configuration option is required.")
        if not config.get("haproxy_url"):
            raise ValueError("The 'haproxy-url' configuration option is required.")
        if not config.get("haproxy_url").startswith("http"):
            raise ValueError("The 'haproxy-url' must be a valid URL starting with 'http' or 'https'.")
        if not config.get("haproxy_username"):
            raise ValueError("The 'haproxy-username' configuration option is required.")
        if not config.get("haproxy_password"):
            raise ValueError("The 'haproxy-password' configuration option is required.")
        
    def _get_config(self) -> dict:
        """Get the configuration as a dictionary."""
        return {
            "frequency": self.model.config.get("frequency", 60),
            "collector_name": self.model.config.get("collector-name"),
            "haproxy_name": self.model.config.get("haproxy-name"),
            "haproxy_url": self.model.config.get("haproxy-url"),
            "haproxy_username": self.model.config.get("haproxy-username"),
            "haproxy_password": self.model.config.get("haproxy-password"),
        }

    def _on_service_start(self, event: ops.ActionEvent):
        """Start the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Starting servcice...")
        time.sleep(5)  # Simulate some delay for maintenance
        # run(["systemctl", "daemon-reload"])
        # run(["systemctl", "start", "collector.service"])
        self.model.unit.status = ops.ActiveStatus("Running")
        
    def _on_service_stop(self, event: ops.ActionEvent):
        """Stop the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Stoping servcice...")
        time.sleep(5)  # Simulate some delay for maintenance
        # run(["systemctl", "stop", "collector.service"])
        # run(["systemctl", "disable", "collector.service"])
        self.model.unit.status = ops.BlockedStatus("Stopped")
    
    def _on_service_restart(self, event):
        """Restart the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Restarting servcice...")
        time.sleep(5)  # Simulate some delay for maintenance
        # run(["systemctl", "daemon-reload"])
        # run(["systemctl", "restart", "collector.service"])

        # run(["systemctl", "daemon-reload"])
        # run(["systemctl", "start", "collector.timer"])
        # run(["systemctl", "enable", "collector.timer"])
        
        # logger.info("Collector service and timer restarted successfully.")
        self.model.unit.status = ops.ActiveStatus("Running")

    def _store_config(self, config: dict):
        """Store the configuration in a file."""

        # Store configuration in .collector folder
        run(["mkdir", "-p", "~/.collector"])
        with open("~/.collector/config.json", "w") as config_file:
            config_file.write(json.dumps(config))
    
    def _read_config(self) -> dict:
        """Read the configuration from a file."""
        try:
            with open("~/.collector/config.json", "r") as config_file:
                return json.loads(config_file.read())
        except FileNotFoundError:
            logger.error("Configuration file not found.")
            return {}
        except json.JSONDecodeError:
            logger.error("Error decoding configuration file.")
            return {}
        
    def _generate_environment_file(self, config: dict):
        """Generate the environment file for the collector service."""
        env_file_path = "/etc/default/collector_envs"
        with open(env_file_path, "w") as env_file:
            env_file.write(f"HAPROXY_URL={config['haproxy_url']}\n")
            env_file.write(f"HAPROXY_USERNAME={config['haproxy_username']}\n")
            env_file.write(f"HAPROXY_PASSWORD={config['haproxy_password']}\n")

        logger.info(f"Environment file created at {env_file_path}")
    
if __name__ == "__main__":  # pragma: nocover
    ops.main(CollectorCharm)  # type: ignore

#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""Charm the application."""

from subprocess import run
from string import Template

import logging

import ops
import json
import os

logger = logging.getLogger(__name__)
dest_dir = '/opt/collector' # Destination directory for the collector files can be set to any path

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
        framework.observe(self.on['reload'].action, self._on_reload)

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

            if ("release_tag" in changed_configs or "github_repo" in changed_configs or "sub_directory" in changed_configs):
                # Fetch the collector from GitHub if the release tag, repo or sub-directory has changed
                try:
                    self._fetch_collector(new_config)
                    logger.info("Collector fetched successfully.")

                    self.unit.set_workload_version(new_config.get("release_tag"))
                except Exception as e:
                    logger.error(f"Failed to fetch collector: {e}")
                    self.model.unit.status = ops.BlockedStatus(f"Failed to fetch collector: {e}")
                    return

            if "haproxy_url" in changed_configs or "haproxy_username" in changed_configs or "haproxy_password" in changed_configs:
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
        if not config.get("github_repo"):
            raise ValueError("The 'github-repo' configuration option is required.")
        if not config.get("github_repo").startswith("https://"):
            raise ValueError("The 'github-repo' must be a valid HTTPS URL.")
        if not config.get("github_token"):
            raise ValueError("The 'github-token' configuration option is required.")
        if not config.get("release_tag"):
            raise ValueError("The 'release-tag' configuration option is required.")
        
    def _get_config(self) -> dict:
        """Get the configuration as a dictionary."""
        return {
            "frequency": self.model.config.get("frequency", 60),
            "collector_name": self.model.config.get("collector-name"),
            "haproxy_name": self.model.config.get("haproxy-name"),
            "haproxy_url": self.model.config.get("haproxy-url"),
            "haproxy_username": self.model.config.get("haproxy-username"),
            "haproxy_password": self.model.config.get("haproxy-password"),
            "github_repo": self.model.config.get("github-repo"),
            "github_token": self.model.config.get("github-token"),
            "release_tag": self.model.config.get("release-tag"),
            "sub_directory": self.model.config.get("sub-directory"),
        }

    def _on_service_start(self, event: ops.ActionEvent):
        """Start the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Starting servcice...")
        # Start the service
        run(["systemctl", "start", "collector.service"], check=True)
        run(["systemctl", "enable", "collector.service"], check=True)
        
        # Start the timer as well
        run(["systemctl", "start", "collector.timer"], check=True)
        run(["systemctl", "enable", "collector.timer"], check=True)
        self.model.unit.status = ops.ActiveStatus("Running")
        
    def _on_service_stop(self, event: ops.ActionEvent):
        """Stop the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Stoping servcice...")
        # Stop the service
        run(["systemctl", "stop", "collector.service"])
        run(["systemctl", "disable", "collector.service"])

        # Stop the timer as well
        run(["systemctl", "stop", "collector.timer"])
        run(["systemctl", "disable", "collector.timer"])
        self.model.unit.status = ops.BlockedStatus("Stopped")
    
    def _on_service_restart(self, event):
        """Restart the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Restarting servcice...")
        run(["systemctl", "daemon-reload"], check=True)
        # Restart the service
        run(["systemctl", "restart", "collector.service"], check=True)
        run(["systemctl", "enable", "collector.service"], check=True)
        
        # Restart the timer as well
        run(["systemctl", "restart", "collector.timer"], check=True)
        run(["systemctl", "enable", "collector.timer"], check=True)
        
        logger.info("Collector service and timer restarted successfully.")
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

    def _generate_service_file(self, config: dict):
        """Generate the service file for the collector."""
        service_file_path = "/etc/systemd/system/collector.service"
        entrypoint = f"python3 {dest_dir}/main.py"

        with open(service_file_path, "w") as service_file:
            service_file.write(SERVICE_TEMPLATE.substitute(entrypoint=entrypoint))

        logger.info(f"Service file created at {service_file_path}")

        # Generate the timer file
        timer_file_path = "/etc/systemd/system/collector.timer"
        interval = config.get("frequency")

        with open(timer_file_path, "w") as timer_file:
            timer_file.write( TIMER_TEMPLATE.substitute(interval=interval))

        logger.info(f"Timer file created at {timer_file_path}")

        # Reload systemd to recognize the new service and timer
        run(["systemctl", "daemon-reload"], check=True)
        logger.info("Systemd daemon reloaded to recognize new service and timer.")

    def _install_dependencies(self):
        """Install necessary dependencies for the collector."""
        run(["apt", "install", "-y", "python3-pip"])
        run(["pip3", "install", "-r", f"{dest_dir}/requirements.txt"], check=True)

    def _fetch_collector(self, config: dict):
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

        if subdir: # If a sub-directory is specified, set sparse-checkout to that directory
            logger.info(f"Setting sparse-checkout to sub-directory: {subdir}")
            run(["git", "-C", clone_dir, "sparse-checkout", "set", subdir], check=True)

        run(["rm", "-rf", dest_dir], check=True)

        logger.info(f"Copying files from {clone_dir}/{subdir} to {dest_dir}...")
        os.makedirs(dest_dir, exist_ok=True)
        run(["cp", "-r", f"{clone_dir}/{subdir}/.", dest_dir], check=True)

        logger.info("Collector fetched and copied successfully.")

    def _on_reload(self, event: ops.ActionEvent):
        """Refresh the collector service."""
        self.model.unit.status = ops.MaintenanceStatus("Refreshing collector service...")
        logger.info("Refreshing collector service with new configuration...")

        config = self._get_config()

        # Validate the configuration
        self.model.unit.status = ops.MaintenanceStatus("Validating configuration...")
        logger.info("Validating configuration...")
        self._validate_config(config)
        logger.info("Configuration validated successfully.")
        
        # Store the configuration
        self.model.unit.status = ops.MaintenanceStatus("Storing configuration...")
        logger.info("Storing configuration...")
        self._store_config(config)
        logger.info("Configuration stored successfully.")

        # Stop the service
        logger.info("Stopping collector service...")
        self._on_service_stop(event)
        logger.info("Collector service stopped successfully.")

        # Fetch the collector from GitHub if needed
        self.model.unit.status = ops.MaintenanceStatus("Fetching collector from GitHub...")
        logger.info("Fetching collector from GitHub...")
        # Fetch the collector from GitHub if needed
        self._fetch_collector(config)
        logger.info("Collector fetched successfully.")

        # Install dependencies
        self.model.unit.status = ops.MaintenanceStatus("Installing dependencies...")
        logger.info("Installing dependencies...")
        try:
            self._install_dependencies()
            logger.info("Dependencies installed successfully.")
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            self.model.unit.status = ops.BlockedStatus(f"Dependency installation failed: {e}")
            return

        # Generate the environment file
        self.model.unit.status = ops.MaintenanceStatus("Generating environment file...")
        logger.info("Generating environment file...")
        self._generate_environment_file(config)
        logger.info("Environment file generated successfully.")

        # Generate the service file
        self.model.unit.status = ops.MaintenanceStatus("Generating service file...")
        logger.info("Generating service file...")
        self._generate_service_file(config)
        logger.info("Service file generated successfully.")

        # Set the workload version
        logger.info("Setting workload version...")
        self.unit.set_workload_version(config.get("release_tag"))
        logger.info("Workload version set successfully.")

        # Start the service
        logger.info("Starting collector service...")
        self._on_service_start(event)
        logger.info("Collector service started successfully.")

        # Update the status
        self.model.unit.status = ops.ActiveStatus("Running")
        logger.info("Collector service refreshed successfully.")

if __name__ == "__main__":  # pragma: nocover
    ops.main(CollectorCharm)  # type: ignore

#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""Service management for the collector charm."""

import logging
from subprocess import run

logger = logging.getLogger(__name__)


class ServiceManager:
    """Handles systemd service operations for the collector charm."""
    
    def __init__(self, unit_status_setter):
        """Initialize with a unit status setter function.
        
        Args:
            unit_status_setter: Function to set unit status (e.g., self.model.unit.status)
        """
        self.set_status = unit_status_setter
    
    def start_service(self) -> None:
        """Start the collector service and timer."""
        
        # Start the service
        logger.info("Starting collector service and timer...")
        run(["systemctl", "start", "collector.service"], check=True)
        run(["systemctl", "enable", "collector.service"], check=True)
        
        # Start the timer as well
        run(["systemctl", "start", "collector.timer"], check=True)
        run(["systemctl", "enable", "collector.timer"], check=True)
        logger.info("Collector service and timer started successfully.")

    def stop_service(self) -> None:
        """Stop the collector service and timer."""
        
        # Stop the service
        logger.info("Stopping collector service and timer...")
        run(["systemctl", "stop", "collector.service"])
        run(["systemctl", "disable", "collector.service"])

        # Stop the timer as well
        run(["systemctl", "stop", "collector.timer"])
        run(["systemctl", "disable", "collector.timer"])
        logger.info("Collector service and timer stopped successfully.")

    def reload_daemon(self) -> None:
        """Reload the systemd daemon to apply changes."""
        logger.info("Reloading systemd daemon...")
        run(["systemctl", "daemon-reload"], check=True)
        logger.info("Systemd daemon reloaded successfully.")
    
    def restart_service(self) -> None:
        """Restart the collector service and timer."""
        
        logger.info("Restarting collector service and timer...")
        self.reload_daemon()
        
        # Restart the service
        run(["systemctl", "restart", "collector.service"], check=True)
        run(["systemctl", "enable", "collector.service"], check=True)
        
        # Restart the timer as well
        run(["systemctl", "restart", "collector.timer"], check=True)
        run(["systemctl", "enable", "collector.timer"], check=True)
        
        logger.info("Collector service and timer restarted successfully.")

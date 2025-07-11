#!/usr/bin/env python3
# Copyright 2024 Adrian Wennström
# See LICENSE file for licensing details.

"""Service and timer templates for the collector."""

from string import Template

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

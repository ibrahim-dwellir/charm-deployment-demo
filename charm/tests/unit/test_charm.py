# Copyright 2025 Alhassan Ibrahim
# See LICENSE file for licensing details.
#
# To learn more about testing, see https://ops.readthedocs.io/en/latest/explanation/testing.html

import pytest
from ops import testing

from charm import CollectorCharm


def mock_get_version():
    """Get a mock version string without executing the workload code."""
    return "1.0.0"


def test_start(monkeypatch: pytest.MonkeyPatch):
    """Test that the charm has the correct state after handling the start event."""
    # Arrange:
    ctx = testing.Context(CollectorCharm)
    monkeypatch.setattr("charm.workload.get_version", mock_get_version)
    # Act:
    state_out = ctx.run(ctx.on.start(), testing.State())
    # Assert:
    assert state_out.workload_version is not None
    assert state_out.unit_status == testing.ActiveStatus()

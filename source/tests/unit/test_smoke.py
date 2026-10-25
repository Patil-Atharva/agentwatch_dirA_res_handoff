"""Basic smoke test for AgentWatch-A foundation."""

import agentwatch_a


def test_package_import():
    """Verify that agentwatch_a package imports and exposes __version__."""
    assert hasattr(agentwatch_a, "__version__")
    assert agentwatch_a.__version__ == "0.1.0"

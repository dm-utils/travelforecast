"""Shared fixtures for the Travel Forecast tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ loadable in every test in this package."""
    yield

import os


def pytest_configure(config):
    """Provide stable defaults for backend test runs without weakening production behavior."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SESSION_SECRET", "test-session-secret")

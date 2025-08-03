"""Playwright configuration for end-to-end tests."""

import pytest
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
import subprocess
import time
import os
import signal
from typing import Generator


@pytest.fixture(scope="session")
def streamlit_app() -> Generator[str, None, None]:
    """Start Streamlit app for testing and return the URL."""
    # Create a mock .env file for testing
    test_env_content = """
KITE_API_KEY=test_api_key_for_testing
KITE_ACCESS_TOKEN=test_access_token_for_testing
"""
    
    # Save original .env if it exists
    env_path = "d:\\repos\\new_strategy\\.env"
    original_env_backup = None
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            original_env_backup = f.read()
    
    # Write test environment
    with open(env_path, 'w') as f:
        f.write(test_env_content)
    
    try:
        # Start Streamlit app
        env = os.environ.copy()
        env['PYTHONPATH'] = 'd:\\repos\\new_strategy\\src'
        
        process = subprocess.Popen(
            ["streamlit", "run", "src/app.py", "--server.port=8502", "--server.headless=true"],
            cwd="d:\\repos\\new_strategy",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        # Wait for app to start
        time.sleep(10)
        
        url = "http://localhost:8502"
        yield url
        
    finally:
        # Cleanup: kill the process
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], 
                         capture_output=True)
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        # Restore original .env
        if original_env_backup is not None:
            with open(env_path, 'w') as f:
                f.write(original_env_backup)
        elif os.path.exists(env_path):
            os.remove(env_path)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture
def app_page(page: Page, streamlit_app: str) -> Page:
    """Navigate to the Streamlit app and return the page."""
    page.goto(streamlit_app)
    page.wait_for_load_state('networkidle')
    return page

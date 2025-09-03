"""
Shared pytest fixtures for the Zap2it Guide Scraper test suite.

This module provides common test fixtures that can be used across
unit and integration tests.
"""

import pytest
import tempfile
import os
import json
import configparser
from unittest.mock import Mock, MagicMock
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock config file for testing."""
    config_path = temp_dir / "test_config.ini"
    
    config = configparser.ConfigParser()
    config['creds'] = {
        'username': 'test_user',
        'password': 'test_password'
    }
    config['prefs'] = {
        'lang': 'en',
        'country': 'us',
        'zipCode': '12345',
        'guideDays': '7',
        'historicalGuideDays': '30'
    }
    config['lineup'] = {
        'lineupId': 'TEST-LINEUP',
        'headendId': 'TEST-HEADEND',
        'device': 'X'
    }
    
    with open(config_path, 'w') as f:
        config.write(f)
    
    yield str(config_path)


@pytest.fixture
def sample_guide_response():
    """Sample API response data for guide scraping tests."""
    return {
        "channels": [
            {
                "channelId": "12345",
                "channelNo": "2.1",
                "callSign": "ABC",
                "affiliateName": "ABC Network",
                "thumbnail": "https://example.com/thumb.jpg",
                "events": [
                    {
                        "startTime": "2023-01-01T20:00:00Z",
                        "endTime": "2023-01-01T21:00:00Z",
                        "duration": 60,
                        "seriesId": "SH123456",
                        "program": {
                            "id": "EP1234567890",
                            "title": "Sample Show",
                            "episodeTitle": "Episode 1",
                            "shortDesc": "A sample TV show episode",
                            "season": 1,
                            "episode": 1
                        },
                        "thumbnail": "thumb123",
                        "filter": ["filter-comedy", "filter-new"],
                        "flag": ["New"],
                        "tags": ["CC"],
                        "rating": "TV-PG"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_urllib_response():
    """Mock urllib response for HTTP requests."""
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        "token": "test_token",
        "properties": {"2004": "test_headend"}
    }).encode('utf-8')
    return mock_response


@pytest.fixture
def mock_ssl_context():
    """Mock SSL context for secure connections."""
    mock_context = Mock()
    return mock_context


@pytest.fixture
def mock_dom_document():
    """Mock XML DOM document for XML generation tests."""
    mock_doc = MagicMock()
    mock_element = MagicMock()
    mock_doc.createElement.return_value = mock_element
    mock_doc.createTextNode.return_value = MagicMock()
    return mock_doc


@pytest.fixture
def sample_zip_codes():
    """Sample zip codes for testing multi-zip functionality."""
    return ["12345", "67890", "11111"]


@pytest.fixture
def mock_time_functions(monkeypatch):
    """Mock time-related functions for consistent testing."""
    import time
    
    # Mock current time to a fixed value
    fixed_time = 1640995200.0  # 2022-01-01 00:00:00 UTC
    monkeypatch.setattr(time, 'time', lambda: fixed_time)
    
    # Mock sleep to avoid delays in tests
    monkeypatch.setattr(time, 'sleep', lambda x: None)
    
    return fixed_time


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Setup mock environment variables for configuration testing."""
    env_vars = {
        'ZAP2IT_CREDS_USERNAME': 'env_user',
        'ZAP2IT_CREDS_PASSWORD': 'env_password',
        'ZAP2IT_PREFS_COUNTRY': 'ca',
        'ZAP2IT_PREFS_LANG': 'fr'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    yield env_vars


@pytest.fixture
def mock_file_operations(temp_dir):
    """Mock file operations with actual temporary files."""
    test_files = {}
    
    def create_test_file(filename, content=""):
        file_path = temp_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        test_files[filename] = str(file_path)
        return str(file_path)
    
    def get_test_file_path(filename):
        return test_files.get(filename)
    
    yield {
        'create_file': create_test_file,
        'get_path': get_test_file_path,
        'temp_dir': temp_dir
    }


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state variables before each test."""
    # Import the module to reset its global variables
    import sys
    if 'zap2it-GuideScrape' in sys.modules:
        module = sys.modules['zap2it-GuideScrape']
        if hasattr(module, 'ADDED_CHANNELS'):
            module.ADDED_CHANNELS.clear()
        if hasattr(module, 'ADDED_EVENTS'):
            module.ADDED_EVENTS.clear()


@pytest.fixture
def capture_output():
    """Capture stdout and stderr for testing print statements."""
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        yield {
            'stdout': stdout_capture,
            'stderr': stderr_capture
        }


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def mock_argparse_args():
    """Mock command line arguments for testing."""
    mock_args = Mock()
    mock_args.configfile = None
    mock_args.outputfile = None
    mock_args.language = None
    mock_args.findid = False
    mock_args.channels = False
    mock_args.web = False
    return mock_args
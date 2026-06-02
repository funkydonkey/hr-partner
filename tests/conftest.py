import sys
from unittest.mock import MagicMock

# Mock serpapi before any app module is imported
mock_serpapi = MagicMock()
sys.modules.setdefault("serpapi", mock_serpapi)

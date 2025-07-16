import os
from pathlib import Path

def validate_test_file(test_path: str) -> str:
    """
    Validate that the test file exists and return its absolute path.
    Raises ValueError if file doesn't exist.
    """
    # Convert to Path object for better path handling
    path = Path(test_path)
    
    # If path is relative, make it relative to current directory
    if not path.is_absolute():
        path = Path.cwd() / path
    
    # Check if file exists
    if not path.is_file():
        raise ValueError(f"Test file not found: {test_path}")
    
    # Check if it's a JavaScript/TypeScript file
    if not path.suffix in ['.js', '.ts', '.spec.js', '.spec.ts']:
        raise ValueError(f"Invalid test file type. Must be .js, .ts, .spec.js, or .spec.ts: {test_path}")
    
    return str(path.absolute()) 
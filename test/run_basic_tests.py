#!/usr/bin/env python

"""
Run the basic tests that work with mock data and don't require the actual implementation.
"""

import pytest
import sys

def main():
    """Run the basic tests"""
    print("Running basic tests for Iron Condor Finder...")
    
    # Tests we know work with mocks
    test_files = [
        "test/data_sources/test_mock_data_source.py",
        "test/test_basic_iron_condor_finder.py",
        "test/test_utilities.py",
        "test/test_visualization.py",
    ]
    
    # Run the tests
    result = pytest.main(["-v"] + test_files)
    
    # Return the result as the exit code
    return result

if __name__ == "__main__":
    sys.exit(main()) 
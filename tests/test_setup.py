"""Setup the test title

"""
import pytest


@pytest.mark.dev
def test_set_test_title():
    """Set the test title
    """
    print('##vso[task.setvariable variable=test_title]Test results'
          'for Azure Functions (Support)')

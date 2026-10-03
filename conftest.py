"""Provide unittest-style assert helpers to plain test classes.

The test classes in this project do not inherit from
``unittest.TestCase`` but call ``self.assert*`` helpers. Binding the
``unittest.TestCase`` implementations at collection time keeps the
test files untouched while letting those assertions work.
"""

import unittest

_ASSERT_HELPERS = (
    "assertIsNotNone",
    "assertIsNone",
    "assertTrue",
    "assertFalse",
    "assertEqual",
    "assertNotEqual",
    "assertIn",
    "assertGreater",
    "assertLess",
)


def pytest_pycollect_makeitem(collector, name, obj):
    if isinstance(obj, type) and name.startswith("Test") \
            and not issubclass(obj, unittest.TestCase):
        for helper in _ASSERT_HELPERS:
            if not hasattr(obj, helper):
                setattr(obj, helper, getattr(unittest.TestCase, helper))
    return None

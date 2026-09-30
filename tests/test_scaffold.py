import sys

import value_sort


def test_package_imports():
    assert value_sort.__version__ == "0.1.0"


def test_python_version():
    assert sys.version_info[:2] == (3, 11)

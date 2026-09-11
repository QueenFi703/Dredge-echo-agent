import unittest

import bridge


class BridgePackageTests(unittest.TestCase):
    def test_legacy_python_adapter_remains_available_lazily(self):
        self.assertEqual(bridge.PythonAdapter.__name__, "PythonAdapter")


if __name__ == "__main__":
    unittest.main()

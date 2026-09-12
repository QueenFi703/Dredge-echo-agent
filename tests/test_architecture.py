import unittest

from unittest.mock import Mock

from bridge.architecture import (
    DEFAULT_ARCHITECTURE,
    Architecture,
    build_selected_architecture,
    resolve_architecture,
)


class ArchitectureRoutingTests(unittest.TestCase):
    def test_astra_is_the_default(self):
        self.assertIs(DEFAULT_ARCHITECTURE, Architecture.ASTRA)
        self.assertIs(resolve_architecture(None), Architecture.ASTRA)

    def test_nebius_requires_explicit_selection(self):
        self.assertIs(
            resolve_architecture(Architecture.NEBIUS.value), Architecture.NEBIUS
        )

    def test_unknown_route_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_architecture("automatic-provider-fallback")

    def test_default_invokes_only_astra_builder(self):
        astra = Mock(return_value="astra-agent")
        nebius = Mock(return_value="nebius-agent")

        result = build_selected_architecture(
            None, astra_builder=astra, nebius_builder=nebius
        )

        self.assertEqual(result, "astra-agent")
        astra.assert_called_once_with()
        nebius.assert_not_called()

    def test_explicit_nebius_invokes_only_nebius_builder(self):
        astra = Mock(return_value="astra-agent")
        nebius = Mock(return_value="nebius-agent")

        result = build_selected_architecture(
            Architecture.NEBIUS.value,
            astra_builder=astra,
            nebius_builder=nebius,
        )

        self.assertEqual(result, "nebius-agent")
        nebius.assert_called_once_with()
        astra.assert_not_called()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib
import sys
import unittest
from datetime import date


class CollectorCliTest(unittest.TestCase):
    def test_main_module_imports_without_asyncpg_for_cli_parsing(self) -> None:
        previous_asyncpg = sys.modules.pop("asyncpg", None)
        sys.modules.pop("collector.main", None)
        try:
            module = importlib.import_module("collector.main")
            self.assertEqual(module.parse_cli_date("2026-06-28"), date(2026, 6, 28))
        finally:
            sys.modules.pop("collector.main", None)
            if previous_asyncpg is not None:
                sys.modules["asyncpg"] = previous_asyncpg


if __name__ == "__main__":
    unittest.main()

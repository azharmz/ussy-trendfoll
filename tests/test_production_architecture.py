from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductionArchitectureContract(unittest.TestCase):
    def test_single_production_entrypoint(self):
        daily = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
        self.assertIn("run: python main.py", daily)
        self.assertFalse((ROOT / "r2_main.py").exists())

    def test_r2_integration_is_adapter_to_feature_engine(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        integration = (ROOT / "r2_integration.py").read_text(encoding="utf-8")
        self.assertIn("from r2_integration import build_feature_store_from_r2", main)
        self.assertIn("import feature_engine as fe", integration)
        self.assertFalse((ROOT / "r2_feature_engine.py").exists())

    def test_no_python_consumer_uses_retired_module(self):
        offenders = []
        for path in ROOT.rglob("*.py"):
            if path == Path(__file__):
                continue
            if "r2_feature_engine" in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()

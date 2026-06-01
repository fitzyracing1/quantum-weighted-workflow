import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class PrivacyRouterTests(unittest.TestCase):
    def test_dry_run_emits_approved_profile_and_guardrails(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            circuit = Path(directory) / "circuit.json"
            vpn_config = Path(directory) / "selected.conf"
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "privacy_router.py"),
                    "--seed",
                    "7",
                    "--output",
                    str(output),
                    "--circuit-output",
                    str(circuit),
                    "--vpn-config-output",
                    str(vpn_config),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            config = json.loads((ROOT / "profiles.example.json").read_text(encoding="utf-8"))
            self.assertEqual(report["mode"], "dry-run-vpn-plan-only")
            self.assertIn(report["selected_policy"], config["approved_profiles"])
            self.assertEqual(len(report["guardrails"]), 4)
            self.assertTrue(circuit.exists())
            self.assertTrue(vpn_config.exists())
            rendered = vpn_config.read_text(encoding="utf-8")
            self.assertIn("[Interface]", rendered)
            self.assertIn("[Peer]", rendered)
            self.assertIn("REPLACE_WITH_CLIENT_PRIVATE_KEY", rendered)
            self.assertEqual(report["activation_plan"]["mode"], "manual-activation-required")


if __name__ == "__main__":
    unittest.main()

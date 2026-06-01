import json
import tempfile
import unittest
from pathlib import Path

from weighted_model import (
    STATE_ORDER,
    build_circuit,
    decode_histogram,
    expected_histogram,
    load_config,
    prepares_superposition,
)


ROOT = Path(__file__).resolve().parent


class WeightedModelTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / "actions.example.json")

    def test_builds_three_qubit_ionq_circuit(self):
        circuit = build_circuit(self.config["actions"])
        self.assertEqual(circuit["qubits"], 3)
        self.assertEqual(circuit["gateset"], "qis")
        self.assertEqual(len(circuit["circuit"]), 10)

    def test_expected_histogram_decodes_to_configured_weights(self):
        histogram = expected_histogram(self.config["actions"])
        decoded = decode_histogram(self.config["actions"], histogram)
        total = sum(action["weight"] for action in self.config["actions"])
        for action in self.config["actions"]:
            self.assertAlmostEqual(decoded[action["name"]], action["weight"] / total)

    def test_requires_exactly_five_actions(self):
        invalid = {"model_name": "invalid", "actions": self.config["actions"][:4]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly five"):
                load_config(path)

    def test_state_order_is_stable(self):
        self.assertEqual(STATE_ORDER, ("0", "4", "2", "1", "3"))

    def test_example_prepares_superposition(self):
        self.assertTrue(prepares_superposition(self.config["actions"]))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parents[1] / "template"
sys.path.insert(0, str(TEMPLATE))

from weighted_model import build_circuit, choose_action, decode_histogram, expected_histogram, load_config, load_histogram


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recommend an approved privacy-routing profile from a weighted quantum histogram."
    )
    parser.add_argument("--config", type=Path, default=ROOT / "profiles.example.json")
    parser.add_argument("--histogram", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--circuit-output", type=Path, default=ROOT / "generated_privacy_router_circuit.json")
    parser.add_argument("--output", type=Path, default=ROOT / "privacy_router_report.json")
    args = parser.parse_args()

    config = load_config(args.config)
    circuit = build_circuit(config["actions"])
    args.circuit_output.write_text(json.dumps(circuit, indent=2) + "\n", encoding="utf-8")

    histogram = load_histogram(args.histogram) if args.histogram else expected_histogram(config["actions"])
    probabilities = decode_histogram(config["actions"], histogram)
    selected = choose_action(config["actions"], probabilities, random.Random(args.seed))
    profile = config["approved_profiles"][selected["name"]]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run-recommendation-only",
        "selected_policy": selected["name"],
        "selected_profile": profile,
        "decoded_action_probabilities": probabilities,
        "cryptography_requirements": config["cryptography_requirements"],
        "guardrails": [
            "This example does not create a VPN tunnel.",
            "This example does not change routes, DNS, firewall rules, or network interfaces.",
            "Only endpoint aliases from the approved profile configuration are considered.",
            "Quantum-weighted profile selection is not a replacement for post-quantum cryptography."
        ]
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("quantum-aware privacy router")
    print("mode: dry-run-recommendation-only")
    print(f"selected policy: {selected['name']}")
    print(f"endpoint alias: {profile['endpoint_alias']}")
    print(f"circuit: {args.circuit_output}")
    print(f"report: {args.output}")


if __name__ == "__main__":
    main()

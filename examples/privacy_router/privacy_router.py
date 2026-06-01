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
from vpn_backend import activation_plan, write_wireguard_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recommend an approved privacy-routing profile from a weighted quantum histogram."
    )
    parser.add_argument("--config", type=Path, default=ROOT / "profiles.example.json")
    parser.add_argument("--histogram", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--circuit-output", type=Path, default=ROOT / "generated_privacy_router_circuit.json")
    parser.add_argument("--vpn-config-output", type=Path, default=ROOT / "generated_selected_wireguard.conf")
    parser.add_argument("--output", type=Path, default=ROOT / "privacy_router_report.json")
    args = parser.parse_args()

    config = load_config(args.config)
    circuit = build_circuit(config["actions"])
    args.circuit_output.write_text(json.dumps(circuit, indent=2) + "\n", encoding="utf-8")

    histogram = load_histogram(args.histogram) if args.histogram else expected_histogram(config["actions"])
    probabilities = decode_histogram(config["actions"], histogram)
    selected = choose_action(config["actions"], probabilities, random.Random(args.seed))
    profile = config["approved_profiles"][selected["name"]]
    vpn_config_path = None
    plan = {
        "mode": "manual-review-required",
        "reason": "Selected policy does not produce a tunnel config.",
        "not_performed": [
            "No tunnel was started.",
            "No route was changed.",
            "No DNS setting was changed.",
            "No firewall rule was changed.",
        ],
    }
    if profile.get("wireguard"):
        vpn_config_path = write_wireguard_config(profile, args.vpn_config_output)
        plan = activation_plan(profile, vpn_config_path)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run-vpn-plan-only",
        "selected_policy": selected["name"],
        "selected_profile": profile,
        "vpn_config_path": str(vpn_config_path) if vpn_config_path else None,
        "activation_plan": plan,
        "decoded_action_probabilities": probabilities,
        "cryptography_requirements": config["cryptography_requirements"],
        "guardrails": [
            "This example may render a WireGuard-compatible config, but it does not create a VPN tunnel.",
            "This example does not change routes, DNS, firewall rules, or network interfaces.",
            "Only endpoint aliases from the approved profile configuration are considered.",
            "Quantum-weighted profile selection is not a replacement for post-quantum cryptography."
        ]
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("quantum-aware privacy router")
    print("mode: dry-run-vpn-plan-only")
    print(f"selected policy: {selected['name']}")
    print(f"endpoint alias: {profile['endpoint_alias']}")
    if vpn_config_path:
        print(f"vpn config: {vpn_config_path}")
    print(f"circuit: {args.circuit_output}")
    print(f"report: {args.output}")


if __name__ == "__main__":
    main()

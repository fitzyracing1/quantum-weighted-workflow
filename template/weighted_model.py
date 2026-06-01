#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from math import asin, sqrt
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
STATE_ORDER = ("0", "4", "2", "1", "3")


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    actions = config.get("actions", [])
    if len(actions) != 5:
        raise ValueError("This three-qubit template requires exactly five actions.")
    names = [action["name"] for action in actions]
    if len(set(names)) != len(names):
        raise ValueError("Action names must be unique.")
    if any(action["weight"] <= 0 for action in actions):
        raise ValueError("Action weights must be positive.")
    return config


def build_circuit(actions: list[dict[str, Any]]) -> dict[str, Any]:
    weights = [action["weight"] for action in actions]
    first_branch = sum(weights[:3])
    second_branch = sum(weights[3:])

    def angle(numerator: int, denominator: int) -> float:
        return 2 * asin(sqrt(numerator / denominator))

    return {
        "qubits": 3,
        "gateset": "qis",
        "circuit": [
            {"gate": "ry", "target": 0, "rotation": angle(second_branch, sum(weights))},
            {"gate": "x", "target": 0},
            {"gate": "ry", "controls": [0], "target": 1, "rotation": angle(weights[2], first_branch)},
            {"gate": "x", "target": 0},
            {"gate": "ry", "controls": [0], "target": 1, "rotation": angle(weights[4], second_branch)},
            {"gate": "x", "target": 0},
            {"gate": "x", "target": 1},
            {"gate": "ry", "controls": [0, 1], "target": 2, "rotation": angle(weights[1], weights[0] + weights[1])},
            {"gate": "x", "target": 1},
            {"gate": "x", "target": 0},
        ],
    }


def expected_histogram(actions: list[dict[str, Any]]) -> dict[str, float]:
    total = sum(action["weight"] for action in actions)
    return {
        state: action["weight"] / total
        for state, action in zip(STATE_ORDER, actions)
    }


def load_histogram(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    histogram = payload.get("histogram", payload)
    return {str(state): float(probability) for state, probability in histogram.items()}


def decode_histogram(actions: list[dict[str, Any]], histogram: dict[str, float]) -> dict[str, float]:
    decoded = {
        action["name"]: histogram.get(state, 0.0)
        for state, action in zip(STATE_ORDER, actions)
    }
    total = sum(decoded.values())
    if total <= 0:
        raise ValueError("Histogram does not contain any configured states.")
    return {name: probability / total for name, probability in decoded.items()}


def choose_action(actions: list[dict[str, Any]], probabilities: dict[str, float], rng: random.Random) -> dict[str, Any]:
    roll = rng.random()
    cumulative = 0.0
    for action in actions:
        cumulative += probabilities[action["name"]]
        if roll < cumulative:
            return action
    return actions[-1]


def render_prompt(template: str, config: dict[str, Any], probabilities: dict[str, float], selected: dict[str, Any]) -> str:
    table = "\n".join(
        f"- `{action['name']}`: {probabilities[action['name']]:.2%}"
        for action in config["actions"]
    )
    return template.format(
        model_name=config["model_name"],
        probability_table=table,
        selected_action=selected["name"],
        selected_instruction=selected["instruction"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and consume a five-action quantum weighted workflow.")
    parser.add_argument("--config", type=Path, default=ROOT / "actions.example.json")
    parser.add_argument("--circuit-output", type=Path, default=ROOT / "generated_circuit.json")
    parser.add_argument("--histogram", type=Path)
    parser.add_argument("--prompt-template", type=Path, default=ROOT / "weighted_model_prompt.md")
    parser.add_argument("--prompt-output", type=Path, default=ROOT / "generated_prompt.md")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    config = load_config(args.config)
    circuit = build_circuit(config["actions"])
    args.circuit_output.write_text(json.dumps(circuit, indent=2) + "\n", encoding="utf-8")

    histogram = load_histogram(args.histogram) if args.histogram else expected_histogram(config["actions"])
    probabilities = decode_histogram(config["actions"], histogram)
    selected = choose_action(config["actions"], probabilities, random.Random(args.seed))
    template = args.prompt_template.read_text(encoding="utf-8")
    args.prompt_output.write_text(
        render_prompt(template, config, probabilities, selected),
        encoding="utf-8",
    )

    print(f"model: {config['model_name']}")
    for name, probability in probabilities.items():
        print(f"{name:12} {probability:7.2%}")
    print(f"selected: {selected['name']}")
    print(f"circuit: {args.circuit_output}")
    print(f"prompt: {args.prompt_output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from workflow import ROOT, cast, listen, observe, post, reflect


STATE_TO_ACTION = {
    "0": "observe",
    "4": "cast",
    "2": "listen",
    "1": "post",
    "3": "reflect",
}


def load_histogram(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    histogram = payload.get("histogram", payload)
    decoded = {
        STATE_TO_ACTION[state]: float(probability)
        for state, probability in histogram.items()
        if state in STATE_TO_ACTION
    }
    total = sum(decoded.values())
    if total <= 0:
        raise ValueError("Histogram does not contain any actionable probability.")
    return {action: probability / total for action, probability in decoded.items()}


def choose_action(histogram: dict[str, float], rng: random.Random) -> str:
    roll = rng.random()
    cumulative = 0.0
    for action in ("observe", "cast", "listen", "post", "reflect"):
        cumulative += histogram.get(action, 0.0)
        if roll < cumulative:
            return action
    return "reflect"


def execute_action(action: str, conversation_file: Path, context: dict[str, Any]) -> dict[str, Any]:
    def get_observation() -> dict[str, Any]:
        if "observation" not in context:
            context["observation"] = observe(conversation_file)
        return context["observation"]

    def get_iterations() -> list[dict[str, Any]]:
        if "iterations" not in context:
            context["iterations"] = listen()
        return context["iterations"]

    def observe_action() -> dict[str, Any]:
        context["observation"] = observe(conversation_file)
        return context["observation"]

    def cast_action() -> dict[str, Any]:
        result = cast()
        context["cast_result"] = result
        return {
            "discovered_devices": result["discovered_devices"],
            "note": result["note"],
        }

    def listen_action() -> dict[str, Any]:
        iterations = get_iterations()
        return {
            "possibilities_generated": len(iterations),
            "sample": iterations[:5],
        }

    def post_action() -> dict[str, Any]:
        observation = get_observation()
        cast_result = context.setdefault("cast_result", {"discovered_devices": []})
        iterations = get_iterations()
        result = post(observation, cast_result, iterations)
        result["note"] += " Controller execution never publishes automatically."
        return result

    def reflect_action() -> dict[str, Any]:
        iterations = get_iterations()
        result = reflect(iterations)
        return {
            "iterations_reviewed": result["iterations_reviewed"],
            "highest_scoring": result["highest_scoring"][:5],
            "lowest_scoring": result["lowest_scoring"][:5],
        }

    actions: dict[str, Callable[[], dict[str, Any]]] = {
        "observe": observe_action,
        "cast": cast_action,
        "listen": listen_action,
        "post": post_action,
        "reflect": reflect_action,
    }
    return actions[action]()


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch bounded actions from a quantum histogram.")
    parser.add_argument(
        "--histogram",
        type=Path,
        default=ROOT / "nightshift_evidence_histogram.json",
        help="IonQ-style JSON histogram to consume.",
    )
    parser.add_argument(
        "--conversation-file",
        type=Path,
        default=ROOT / "conversation_snapshot.txt",
    )
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "controller_report.json",
    )
    args = parser.parse_args()

    if not 1 <= args.cycles <= 100:
        raise ValueError("--cycles must be between 1 and 100.")

    histogram = load_histogram(args.histogram)
    rng = random.Random(args.seed)
    context: dict[str, Any] = {}
    executions = []
    for cycle in range(1, args.cycles + 1):
        action = choose_action(histogram, rng)
        executions.append(
            {
                "cycle": cycle,
                "action": action,
                "result": execute_action(action, args.conversation_file, context),
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "quantum-histogram-controller",
        "histogram_source": str(args.histogram),
        "decoded_action_probabilities": histogram,
        "cycles": args.cycles,
        "seed": args.seed,
        "guardrails": {
            "observe": "Reads only the explicitly supplied conversation file.",
            "cast": "Discovers endpoints only; never connects or controls a screen.",
            "post": "Creates an X draft only; never publishes automatically.",
            "listen": "Generates a bounded set of 120 permutations.",
            "reflect": "Reviews the bounded set of generated permutations.",
        },
        "executions": executions,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("quantum histogram controller")
    for execution in executions:
        print(f"cycle {execution['cycle']:02}: {execution['action']}")
    print(f"report: {args.output}")


if __name__ == "__main__":
    main()

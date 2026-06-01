#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from itertools import permutations
from math import asin, sqrt
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
STAGES = ("observe", "cast", "listen", "post", "reflect")
WEIGHTS = {
    "observe": 1,
    "cast": 10,
    "listen": 100,
    "post": 40,
    "reflect": 50,
}


def run_command(command: list[str], timeout: float = 4.0) -> dict[str, Any]:
    def as_text(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace").strip()
        return (value or "").strip()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired as error:
        return {
            "command": command,
            "returncode": None,
            "stdout": as_text(error.stdout),
            "stderr": as_text(error.stderr),
            "timed_out": True,
        }


def observe(conversation_file: Path) -> dict[str, Any]:
    text = conversation_file.read_text(encoding="utf-8")
    words = text.split()
    return {
        "source": str(conversation_file),
        "characters": len(text),
        "words": len(words),
        "requested_stages_found": [stage for stage in STAGES if stage in text.lower()],
        "excerpt": text[:500],
    }


def cast() -> dict[str, Any]:
    displays = run_command(["/usr/sbin/system_profiler", "SPDisplaysDataType"])
    services = {}
    for service in ("_airplay._tcp", "_googlecast._tcp", "_raop._tcp"):
        result = run_command(["/usr/bin/dns-sd", "-B", service, "local"], timeout=3.0)
        result["discovered_instances"] = [
            line
            for line in result.get("stdout", "").splitlines()
            if " Add " in line
        ]
        services[service] = result
    discovered_devices = sorted(
        {
            line.split(service, 1)[1].strip().lstrip(". ")
            for service, result in services.items()
            for line in result["discovered_instances"]
            if service in line
        }
    )
    return {
        "local_displays": displays,
        "discovered_cast_services": services,
        "discovered_devices": discovered_devices,
        "note": "Discovery only. This workflow does not connect to or control a screen.",
    }


def listen() -> list[dict[str, Any]]:
    iterations = []
    for index, order in enumerate(permutations(STAGES), start=1):
        iterations.append(
            {
                "iteration": index,
                "order": order,
                "weight_trace": [WEIGHTS[stage] for stage in order],
                "score": sum((position + 1) * WEIGHTS[stage] for position, stage in enumerate(order)),
            }
        )
    return iterations


def post(observation: dict[str, Any], cast_result: dict[str, Any], iterations: list[dict[str, Any]]) -> dict[str, Any]:
    discovered = len(cast_result["discovered_devices"])
    draft = (
        "Hello, world. Quantum workflow completed: "
        f"{observation['words']} conversation words observed, "
        f"{discovered} cast endpoints discovered, "
        f"and {len(iterations)} program iterations reflected."
    )
    return {
        "platform": "X",
        "status": "draft",
        "text": draft,
        "note": "Publishing is intentionally separate: it requires an explicit authenticated X API client.",
    }


def reflect(iterations: list[dict[str, Any]]) -> dict[str, Any]:
    reviewed = sorted(iterations, key=lambda iteration: iteration["score"], reverse=True)
    return {
        "iterations_reviewed": len(reviewed),
        "highest_scoring": reviewed[:10],
        "lowest_scoring": reviewed[-10:],
        "all_iterations": reviewed,
    }


def build_weighted_circuit(weights: dict[str, int]) -> dict[str, Any]:
    left = weights["observe"] + weights["cast"] + weights["listen"]
    right = weights["post"] + weights["reflect"]
    total = left + right
    observe_cast = weights["observe"] + weights["cast"]

    def angle(numerator: int, denominator: int) -> float:
        return 2 * asin(sqrt(numerator / denominator))

    return {
        "qubits": 3,
        "gateset": "qis",
        "circuit": [
            {"gate": "ry", "target": 0, "rotation": angle(right, total)},
            {"gate": "x", "target": 0},
            {"gate": "ry", "controls": [0], "target": 1, "rotation": angle(weights["listen"], left)},
            {"gate": "x", "target": 0},
            {"gate": "ry", "controls": [0], "target": 1, "rotation": angle(weights["reflect"], right)},
            {"gate": "x", "target": 0},
            {"gate": "x", "target": 1},
            {"gate": "ry", "controls": [0, 1], "target": 2, "rotation": angle(weights["cast"], observe_cast)},
            {"gate": "x", "target": 1},
            {"gate": "x", "target": 0},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run every weighted quantum-workflow stage.")
    parser.add_argument(
        "--conversation-file",
        type=Path,
        default=ROOT / "conversation_snapshot.txt",
        help="Explicit conversation snapshot to probe during observe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "workflow_report.json",
        help="Path for the complete workflow report.",
    )
    parser.add_argument("--program", default="Q# hello-world demo")
    parser.add_argument("--program-process", default="")
    parser.add_argument(
        "--circuit-output",
        type=Path,
        default=ROOT / "workflow_ionq_histogram.json",
        help="Path for the stage-evidence IonQ circuit.",
    )
    args = parser.parse_args()

    observation = observe(args.conversation_file)
    cast_result = cast()
    iterations = listen()
    post_result = post(observation, cast_result, iterations)
    reflection = reflect(iterations)
    evidence_weights = {
        "observe": observation["words"],
        "cast": len(cast_result["discovered_devices"]),
        "listen": len(iterations),
        "post": 1 if post_result["status"] == "draft" else 0,
        "reflect": reflection["iterations_reviewed"],
    }
    args.circuit_output.write_text(
        json.dumps(build_weighted_circuit(evidence_weights), indent=2) + "\n",
        encoding="utf-8",
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "execute-all-stages",
        "program": {
            "name": args.program,
            "process": args.program_process,
        },
        "quantum_weights": WEIGHTS,
        "evidence_quantum_weights": evidence_weights,
        "evidence_quantum_circuit": str(args.circuit_output),
        "observe": observation,
        "cast": cast_result,
        "listen": {"possibilities_generated": len(iterations)},
        "post": post_result,
        "reflect": reflection,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("Hello, world!")
    print("executed:", ", ".join(STAGES))
    print(f"iterations reflected: {reflection['iterations_reviewed']}")
    print(f"X post: {post_result['status']}")
    print(f"report: {args.output}")


if __name__ == "__main__":
    main()

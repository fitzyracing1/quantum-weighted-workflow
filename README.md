# Quantum Weighted Workflow Template

This repository contains a reusable template and a working prototype for
encoding workflow evidence into a three-qubit IonQ circuit. The returned
histogram becomes a probabilistic control signal for a bounded Python or AI
controller.

## Start Here

Use the generic [template](template/README.md) to define five weighted actions,
generate an IonQ circuit, decode its histogram, sample one action, and render a
guardrailed AI prompt.

```bash
cd template
python3 weighted_model.py --seed 7
```

The included Nightshift files are a concrete example of the same pattern.

## Architecture

```text
approved evidence
-> weighted five-action configuration
-> generated three-qubit IonQ circuit
-> simulator or quantum processor histogram
-> Python decoder and bounded action sampler
-> AI prompt or permissioned action handler
-> measured result for the next cycle
```

## Published Result

The Nightshift evidence circuit was submitted to `ionq.simulator` in Azure
Quantum workspace `fly2`.

| Action | Evidence Weight | Histogram Probability |
| --- | ---: | ---: |
| observe | 79 | 24.1% |
| cast | 8 | 2.4% |
| listen | 120 | 36.6% |
| post | 1 | 0.3% |
| reflect | 120 | 36.6% |

Azure Quantum job: `3d3db565-6c73-4df8-8824-284861dff509`

## Guardrails

- `observe` reads only an explicitly supplied snapshot.
- `cast` discovers endpoints but never connects to or controls a display.
- `post` produces a draft but never publishes automatically.
- `listen` and `reflect` operate on a bounded set of 120 permutations.
- The histogram controller is capped at 100 cycles.

Raw local reports are ignored because they can contain device names and
absolute paths.

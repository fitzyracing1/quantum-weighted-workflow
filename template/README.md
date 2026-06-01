# Weighted Histogram Workflow Template

Use this folder as a starting point for a five-action hybrid quantum workflow.
The Python model turns action weights into a three-qubit IonQ circuit, decodes
an IonQ histogram, samples one bounded action, and renders an AI prompt.

## Configure

Edit `actions.example.json`. Keep exactly five actions and assign each action a
positive weight plus a clear instruction.

## Generate Locally

```bash
python3 weighted_model.py --seed 7
```

Without `--histogram`, the script uses the ideal weighted distribution. This
lets you test the controller before submitting a quantum job.

## Run On Azure Quantum

Generate `generated_circuit.json`, then submit it to an IonQ simulator:

```bash
az quantum run \
  --resource-group <resource-group> \
  --workspace-name <workspace> \
  --location <location> \
  --target-id ionq.simulator \
  --job-name weighted-workflow \
  --shots 1000 \
  --job-input-format ionq.circuit.v1 \
  --job-input-file generated_circuit.json \
  --job-output-format ionq.quantum-results.v1 \
  --job-params shots=1000 content-type=application/json \
  -o json
```

Save the result and pass it back into the model:

```bash
python3 weighted_model.py --histogram histogram.json --seed 7
```

The rendered `generated_prompt.md` is an input for an AI agent or human
operator. The prompt deliberately selects one action per cycle and requires
separate approval for high-impact behavior.

## State Mapping

The circuit uses five of the eight available basis states:

| Configured action position | IonQ histogram state |
| ---: | --- |
| 1 | `0` |
| 2 | `4` |
| 3 | `2` |
| 4 | `1` |
| 5 | `3` |

Unused states remain at zero probability in the ideal circuit.

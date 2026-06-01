# Quantum-Aware Privacy Router Example

This example uses the weighted-circuit template to recommend one approved VPN
or privacy-routing profile. It is deliberately dry-run only: it generates an
IonQ circuit, a JSON recommendation, and a WireGuard-compatible config file
for manual review. It does not modify the network.

```bash
python3 privacy_router.py --seed 7
```

Output files:

- `generated_privacy_router_circuit.json`: IonQ circuit for the weighted model.
- `generated_selected_wireguard.conf`: selected WireGuard-style config with
  placeholder keys.
- `privacy_router_report.json`: selected policy and manual activation plan.

The weighted circuit can rotate policy choices, but it does not make a VPN
quantum resistant. That security property must come from a vetted
implementation using post-quantum cryptography. NIST standardized ML-KEM for
key establishment in FIPS 203 and ML-DSA for signatures in FIPS 204.

Do not invent a cipher, tunnel protocol, or endpoint-discovery mechanism in
this example. Integrate the generated config with a reviewed WireGuard-compatible
client or VPN product only after replacing placeholders, verifying the endpoint,
and adding explicit user approval and product-specific tests.

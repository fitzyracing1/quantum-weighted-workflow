# Quantum-Aware Privacy Router Example

This example uses the weighted-circuit template to recommend one approved VPN
or privacy-routing profile. It is deliberately dry-run only: it generates an
IonQ circuit and a JSON recommendation but does not modify the network.

```bash
python3 privacy_router.py --seed 7
```

The weighted circuit can rotate policy choices, but it does not make a VPN
quantum resistant. That security property must come from a vetted
implementation using post-quantum cryptography. NIST standardized ML-KEM for
key establishment in FIPS 203 and ML-DSA for signatures in FIPS 204.

Do not invent a cipher, tunnel protocol, or endpoint-discovery mechanism in
this example. Integrate the recommendation with a reviewed VPN product only
after adding explicit user approval and product-specific tests.

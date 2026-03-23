# Hexarch Guardrails Demos

These demos focus on fast local validation and first-run ergonomics.

## Included demos

1. `hexarch_guardrails_demo.ipynb`
   - Colab-friendly interactive walkthrough.

2. `first_run_guarded_call_demo.py`
   - A minimal guarded function demo with clear OPA readiness/error guidance.

3. `opa_preflight_policy_probe.py`
   - Connectivity preflight + policy probe helper for local troubleshooting.

## Quick run

```bash
# From repo root
python demos/opa_preflight_policy_probe.py
python demos/first_run_guarded_call_demo.py
```

If OPA is not running, start it first:

```bash
docker run -p 8181:8181 openpolicyagent/opa:latest run --server
```

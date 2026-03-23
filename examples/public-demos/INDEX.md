# Public Demo Index

This folder contains compact, executable policy-enforcement demonstrations.

General runnable demos are also available in `demos/`:

- `demos/first_run_guarded_call_demo.py`
- `demos/opa_preflight_policy_probe.py`
- `demos/hexarch_guardrails_demo.ipynb`

1. **Threshold pre-execution blocking**
   - Doc: `examples/public-demos/THRESHOLD_PRE_EXECUTION_DEMO.md`
   - Focus: block requests after count threshold.
2. **Recursion / loop prevention**
   - Doc: `examples/public-demos/RECURSION_LOOP_PREVENTION_NODE_RED.md`
   - Flow: `examples/public-demos/flows/recursion-loop-prevention-node-red.json`
   - Focus: block continuation after recursion depth threshold.
3. **Model usage containment**
   - Doc: `examples/public-demos/MODEL_USAGE_CONTAINMENT.md`
   - JSON artifacts: model allowlist rule, token ceiling rule, containment policy.
   - Focus: gate model invocations by model ID and token budget.

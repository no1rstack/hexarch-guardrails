"""OPA preflight + policy probe demo.

Purpose:
- Quickly confirm OPA and policy wiring
- Evaluate one policy directly without decorating app code
"""

from __future__ import annotations

import pathlib
from typing import Dict

from hexarch_guardrails import Guardian
from hexarch_guardrails.exceptions import OPAConnectionError, PolicyConfigError
from hexarch_guardrails.runtime_settings import resolve_runtime_settings


def _policy_path() -> str:
    settings = resolve_runtime_settings()
    if settings.policy_file:
        return settings.policy_file

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    return str(repo_root / "hexarch.yaml")


def _probe_context() -> Dict[str, object]:
    return {
        "resource": "openai",
        "operation": "inference",
        "tokens": 250,
        "api": "openai",
    }


def main() -> int:
    policy_file = _policy_path()
    print("Hexarch OPA preflight + policy probe")
    print("=" * 38)
    print(f"Using policy file: {policy_file}")

    try:
        guardian = Guardian(policy_file=policy_file)
    except PolicyConfigError as exc:
        print("\n[POLICY CONFIG ERROR]")
        print(str(exc))
        return 2
    except OPAConnectionError as exc:
        print("\n[OPA CONNECTION ERROR]")
        print(str(exc))
        print("\nHint:")
        print("  docker run -p 8181:8181 openpolicyagent/opa:latest run --server")
        return 1

    policies = guardian.list_policies()
    print("\nLoaded policies:", policies)

    probe_policy = "api_budget" if "api_budget" in policies else policies[0]
    decision = guardian.evaluate_policy(probe_policy, _probe_context())

    print("\nProbe policy:", probe_policy)
    print("Probe decision:", decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

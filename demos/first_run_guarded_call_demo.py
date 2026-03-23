"""First-run guarded call demo.

Purpose:
- Validate that Guardian can initialize with your policy file
- Execute one guarded function and print deterministic outcomes
- Provide friendly remediation if OPA is not reachable
"""

from __future__ import annotations

import pathlib
from typing import Dict

from hexarch_guardrails import Guardian
from hexarch_guardrails.exceptions import OPAConnectionError, PolicyViolation
from hexarch_guardrails.runtime_settings import resolve_runtime_settings


def _find_policy() -> str:
    settings = resolve_runtime_settings()
    if settings.policy_file:
        return settings.policy_file

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    default_policy = repo_root / "hexarch.yaml"
    return str(default_policy)


def _build_context() -> Dict[str, object]:
    return {
        "resource": "demo_api",
        "operation": "read",
        "metadata": {"source": "first_run_guarded_call_demo"},
    }


def main() -> int:
    policy_path = _find_policy()
    print("Hexarch first-run guarded call demo")
    print("=" * 40)
    print(f"Policy file: {policy_path}")

    try:
        guardian = Guardian(policy_file=policy_path)
    except OPAConnectionError as exc:
        print("\n[OPA NOT REACHABLE]")
        print(str(exc))
        print("\nStart OPA locally with:")
        print("  docker run -p 8181:8181 openpolicyagent/opa:latest run --server")
        return 1

    @guardian.check("rate_limit", context=_build_context())
    def guarded_operation() -> str:
        return "guarded operation executed"

    try:
        result = guarded_operation()
        print("\n[ALLOW]")
        print(result)
    except PolicyViolation as exc:
        print("\n[BLOCK]")
        print(str(exc))

    print("\nAvailable policies:", guardian.list_policies())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

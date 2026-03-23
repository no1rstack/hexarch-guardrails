"""Packaged Rego policy bundles with optional external override layer."""

import os
from importlib import resources
from typing import Optional

from .opa_client import OPAClient


VALID_POLICY_PROFILES = {"default", "strict", "permissive"}


def _resolve_profile(profile: Optional[str]) -> str:
    selected = (profile or os.getenv("POLICY_PROFILE") or "default").strip().lower()
    if selected not in VALID_POLICY_PROFILES:
        raise ValueError(
            f"Unknown policy profile '{selected}'. "
            f"Valid profiles: {sorted(VALID_POLICY_PROFILES)}"
        )
    return selected


def _load_packaged_profile(profile: str) -> str:
    with resources.files("hexarch_guardrails.policies").joinpath(f"{profile}.rego").open(
        "r", encoding="utf-8"
    ) as policy_file:
        return policy_file.read()


def _load_external_policy(policy_path: str) -> str:
    if not os.path.isfile(policy_path):
        raise FileNotFoundError(f"External policy file not found: {policy_path}")
    with open(policy_path, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


def load_policy_bundle(
    profile: Optional[str] = None,
    policy_path: Optional[str] = None,
    merge_mode: str = "append",
) -> str:
    """
    Load packaged policy profile and optionally merge/replace it with external policy.

    Args:
        profile: Policy profile name; defaults to POLICY_PROFILE env var or 'default'.
        policy_path: Optional external policy path; defaults to POLICY_PATH env var.
        merge_mode: 'append' (default) or 'replace'.

    Returns:
        Combined Rego policy module content.
    """
    selected_profile = _resolve_profile(profile)
    bundled_policy = _load_packaged_profile(selected_profile)

    resolved_path = policy_path or os.getenv("POLICY_PATH")
    if not resolved_path:
        return bundled_policy

    override_policy = _load_external_policy(resolved_path)
    if merge_mode == "replace":
        return override_policy
    if merge_mode != "append":
        raise ValueError("merge_mode must be one of: append, replace")

    return f"{bundled_policy}\n\n{override_policy}\n"


def publish_policy_bundle(
    opa_client: Optional[OPAClient] = None,
    *,
    opa_url: str = "http://localhost:8181",
    profile: Optional[str] = None,
    policy_path: Optional[str] = None,
    merge_mode: str = "append",
    policy_name: str = "policy_bundle",
) -> bool:
    """
    Publish selected policy bundle to OPA under /v1/policies/{policy_name}.
    """
    client = opa_client or OPAClient(opa_url)
    bundle = load_policy_bundle(profile=profile, policy_path=policy_path, merge_mode=merge_mode)
    return client.publish_policy(policy_name, bundle)

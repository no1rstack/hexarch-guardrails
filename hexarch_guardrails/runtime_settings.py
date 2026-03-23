"""Shared runtime settings resolution for SDK, CLI-adjacent tools, and demos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import os

import yaml


@dataclass(frozen=True)
class RuntimePolicySettings:
    """Resolved runtime policy settings used by demos and SDK integrations."""

    policy_file: Optional[str] = None
    opa_url: str = "http://localhost:8181"
    profile: Optional[str] = None
    policy_path: Optional[str] = None
    merge_mode: str = "append"
    engine_mode: str = "auto"
    fail_closed: bool = True
    runtime_mode: str = "guardian-yaml"


def _config_file_path() -> Path:
    configured = os.getenv("HEXARCH_CONFIG")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".hexarch" / "config.yml"


def _load_cli_config() -> Dict[str, Any]:
    config_path = _config_file_path()
    if not config_path.exists():
        return {}

    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def resolve_runtime_settings(
    *,
    policy_file: Optional[str] = None,
    opa_url: Optional[str] = None,
    profile: Optional[str] = None,
    policy_path: Optional[str] = None,
    merge_mode: Optional[str] = None,
    engine_mode: Optional[str] = None,
    fail_closed: Optional[bool] = None,
    runtime_mode: Optional[str] = None,
) -> RuntimePolicySettings:
    """Resolve runtime settings from explicit args, env vars, CLI config, and defaults."""
    config = _load_cli_config()
    policies = config.get("policies") or {}

    resolved_policy_file = (
        policy_file
        or os.getenv("HEXARCH_POLICY_FILE")
        or policies.get("policy_file")
    )
    resolved_opa_url = (
        opa_url
        or os.getenv("HEXARCH_POLICY_OPA_URL")
        or os.getenv("OPA_URL")
        or policies.get("opa_url")
        or "http://localhost:8181"
    )
    resolved_profile = (
        profile
        or os.getenv("HEXARCH_POLICY_PROFILE")
        or os.getenv("POLICY_PROFILE")
        or policies.get("profile")
    )
    resolved_policy_path = (
        policy_path
        or os.getenv("HEXARCH_POLICY_PATH")
        or os.getenv("POLICY_PATH")
        or policies.get("policy_path")
    )
    resolved_merge_mode = (
        merge_mode
        or os.getenv("HEXARCH_POLICY_MERGE_MODE")
        or policies.get("merge_mode")
        or "append"
    )
    resolved_engine_mode = (
        engine_mode
        or os.getenv("HEXARCH_POLICY_ENGINE_MODE")
        or policies.get("engine_mode")
        or "auto"
    )

    if fail_closed is not None:
        resolved_fail_closed = fail_closed
    elif os.getenv("HEXARCH_POLICY_FAIL_CLOSED") is not None:
        resolved_fail_closed = os.getenv("HEXARCH_POLICY_FAIL_CLOSED", "true").lower() == "true"
    else:
        resolved_fail_closed = policies.get("fail_closed", True)

    resolved_runtime_mode = (
        runtime_mode
        or os.getenv("HEXARCH_POLICY_RUNTIME_MODE")
        or policies.get("runtime_mode")
        or "guardian-yaml"
    )
    if resolved_runtime_mode not in {"guardian-yaml", "rego-bundle"}:
        resolved_runtime_mode = "guardian-yaml"

    return RuntimePolicySettings(
        policy_file=resolved_policy_file,
        opa_url=resolved_opa_url,
        profile=resolved_profile,
        policy_path=resolved_policy_path,
        merge_mode=resolved_merge_mode,
        engine_mode=resolved_engine_mode,
        fail_closed=resolved_fail_closed,
        runtime_mode=resolved_runtime_mode,
    )


__all__ = ["RuntimePolicySettings", "resolve_runtime_settings"]
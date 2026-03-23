"""Tests for shared runtime settings resolution."""

from pathlib import Path

from hexarch_guardrails import runtime_settings
from hexarch_guardrails.runtime_settings import resolve_runtime_settings


def test_resolve_runtime_settings_prefers_env(monkeypatch, tmp_path):
    policy_file = tmp_path / "hexarch.yaml"
    policy_file.write_text("policies: []\n", encoding="utf-8")

    monkeypatch.setenv("HEXARCH_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("HEXARCH_POLICY_OPA_URL", "http://localhost:9191")

    settings = resolve_runtime_settings()

    assert settings.policy_file == str(policy_file)
    assert settings.opa_url == "http://localhost:9191"


def test_resolve_runtime_settings_reads_cli_config(monkeypatch, tmp_path):
    monkeypatch.setattr(
        runtime_settings,
        "_load_cli_config",
        lambda: {
            "policies": {
                "policy_file": "./hexarch.yaml",
                "opa_url": "http://localhost:8282",
                "profile": "strict",
                "policy_path": "./override.rego",
                "merge_mode": "replace",
                "engine_mode": "local",
                "fail_closed": False,
                "runtime_mode": "rego-bundle",
            }
        },
    )

    settings = resolve_runtime_settings()

    assert settings.policy_file == "./hexarch.yaml"
    assert settings.opa_url == "http://localhost:8282"
    assert settings.profile == "strict"
    assert settings.policy_path == "./override.rego"
    assert settings.merge_mode == "replace"
    assert settings.engine_mode == "local"
    assert settings.fail_closed is False
    assert settings.runtime_mode == "rego-bundle"


def test_explicit_runtime_settings_override_env_and_config(monkeypatch, tmp_path):
    monkeypatch.setattr(
        runtime_settings,
        "_load_cli_config",
        lambda: {"policies": {"policy_file": "./from-config.yaml", "opa_url": "http://localhost:8181"}},
    )
    monkeypatch.setenv("HEXARCH_POLICY_FILE", "./from-env.yaml")
    monkeypatch.setenv("HEXARCH_POLICY_OPA_URL", "http://localhost:9191")

    settings = resolve_runtime_settings(policy_file="./explicit.yaml", opa_url="http://localhost:9393")

    assert settings.policy_file == "./explicit.yaml"
    assert settings.opa_url == "http://localhost:9393"


def test_resolve_runtime_settings_runtime_mode_from_env(monkeypatch):
    monkeypatch.setenv("HEXARCH_POLICY_RUNTIME_MODE", "rego-bundle")
    settings = resolve_runtime_settings()
    assert settings.runtime_mode == "rego-bundle"
"""Tests for packaged policy bundles and override behavior."""

import os

import pytest

from hexarch_guardrails.policy_bundles import load_policy_bundle


def test_load_default_profile_contains_policy_package():
    content = load_policy_bundle(profile="default")
    assert "package policy" in content
    assert "default allow = false" in content


def test_load_strict_profile_is_default_deny():
    content = load_policy_bundle(profile="strict")
    assert "default allow = false" in content


def test_unknown_profile_raises():
    with pytest.raises(ValueError):
        load_policy_bundle(profile="unknown")


def test_append_merge_mode_includes_override(tmp_path):
    external = tmp_path / "custom.rego"
    external.write_text('package policy\nallow if { input.path == "/custom" }\n', encoding="utf-8")

    merged = load_policy_bundle(profile="default", policy_path=str(external), merge_mode="append")
    assert "default allow = false" in merged
    assert "/custom" in merged


def test_replace_merge_mode_returns_override_only(tmp_path):
    external = tmp_path / "custom.rego"
    external.write_text('package policy\ndefault allow = true\n', encoding="utf-8")

    merged = load_policy_bundle(profile="default", policy_path=str(external), merge_mode="replace")
    assert 'default allow = true' in merged
    assert 'input.path == "/health"' not in merged


def test_env_vars_profile_and_path(tmp_path, monkeypatch):
    external = tmp_path / "custom.rego"
    external.write_text('package policy\ndefault allow = true\n', encoding="utf-8")

    monkeypatch.setenv("POLICY_PROFILE", "strict")
    monkeypatch.setenv("POLICY_PATH", str(external))

    merged = load_policy_bundle()
    assert "default allow = false" in merged
    assert "default allow = true" in merged

"""Reusable policy decision engine backed by remote OPA or local OPA CLI."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional
import json
import os
import shutil
import subprocess

import requests

from .policy_bundles import load_policy_bundle


class RegoDecisionEngine:
    """Evaluate request policy input against OPA decision paths."""

    def __init__(
        self,
        opa_url: str = "http://localhost:8181",
        decision_path: str = "policy/allow",
        fail_closed: bool = True,
        timeout_seconds: int = 3,
        mode: str = "remote",
        policy_bundle: Optional[str] = None,
    ):
        self.opa_url = opa_url.rstrip("/")
        self.decision_path = decision_path.strip("/")
        self.fail_closed = fail_closed
        self.timeout_seconds = timeout_seconds
        self.mode = mode
        self.policy_bundle = policy_bundle

    @staticmethod
    def resolve_opa_executable() -> Optional[str]:
        """Resolve the OPA binary from PATH or common WinGet install location."""
        path = shutil.which("opa")
        if path:
            return path

        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            candidate = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages" / "open-policy-agent.opa_Microsoft.Winget.Source_8wekyb3d8bbwe" / "opa.exe"
            if candidate.exists():
                return str(candidate)

            packages_dir = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
            if packages_dir.exists():
                for directory in packages_dir.glob("*open-policy-agent.opa*"):
                    candidate = directory / "opa.exe"
                    if candidate.exists():
                        return str(candidate)

        return None

    def _evaluate_remote(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"input": input_data}
        endpoint = f"{self.opa_url}/v1/data/{self.decision_path}"

        response = requests.post(endpoint, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        return {"result": body.get("result")}

    def _evaluate_local(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        opa_executable = self.resolve_opa_executable()
        if not opa_executable:
            raise RuntimeError(
                "OPA executable not found for local mode. Install with: winget install --id open-policy-agent.opa -e"
            )

        if not self.policy_bundle:
            raise RuntimeError("Local mode requires a policy bundle string.")

        with NamedTemporaryFile("w", suffix=".rego", delete=False, encoding="utf-8") as policy_file:
            policy_file.write(self.policy_bundle)
            policy_path = policy_file.name

        with NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as input_file:
            json.dump(input_data, input_file)
            input_path = input_file.name

        try:
            proc = subprocess.run(
                [
                    opa_executable,
                    "eval",
                    "-f",
                    "json",
                    "-d",
                    policy_path,
                    "-i",
                    input_path,
                    f"data.{self.decision_path}",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout_seconds,
            )
            body = json.loads(proc.stdout)
            expressions = (((body.get("result") or [{}])[0]).get("expressions") or [{}])
            result = expressions[0].get("value") if expressions else None
            return {"result": result}
        finally:
            try:
                os.unlink(policy_path)
            except OSError:
                pass
            try:
                os.unlink(input_path)
            except OSError:
                pass

    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate input against OPA decision path.

        Returns a stable decision envelope:
          {
            "allow": bool,
            "raw": object | None,
            "error": str | None,
          }
        """
        try:
            mode = self.mode.lower()
            if mode == "remote":
                body = self._evaluate_remote(input_data)
            elif mode == "local":
                body = self._evaluate_local(input_data)
            elif mode == "auto":
                try:
                    body = self._evaluate_remote(input_data)
                except Exception:
                    body = self._evaluate_local(input_data)
            else:
                raise ValueError("mode must be one of: remote, local, auto")

            result = body.get("result")

            if isinstance(result, bool):
                return {"allow": result, "raw": result, "error": None}

            if isinstance(result, dict):
                if "allow" in result:
                    return {"allow": bool(result["allow"]), "raw": result, "error": None}
                if "allowed" in result:
                    return {"allow": bool(result["allowed"]), "raw": result, "error": None}

            return {
                "allow": not self.fail_closed,
                "raw": result,
                "error": "OPA result missing allow/allowed boolean",
            }

        except Exception as exc:
            return {
                "allow": not self.fail_closed,
                "raw": None,
                "error": str(exc),
            }


def build_engine_from_bundle(
    *,
    profile: Optional[str] = None,
    policy_path: Optional[str] = None,
    merge_mode: str = "append",
    mode: str = "auto",
    opa_url: str = "http://localhost:8181",
    decision_path: str = "policy/allow",
    fail_closed: bool = True,
    timeout_seconds: int = 3,
) -> RegoDecisionEngine:
    """Convenience builder for CLI/runtime flows using packaged policy bundles."""
    bundle = load_policy_bundle(profile=profile, policy_path=policy_path, merge_mode=merge_mode)
    return RegoDecisionEngine(
        opa_url=opa_url,
        decision_path=decision_path,
        fail_closed=fail_closed,
        timeout_seconds=timeout_seconds,
        mode=mode,
        policy_bundle=bundle,
    )

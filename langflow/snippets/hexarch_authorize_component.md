# `Hexarch Authorize` custom component starter

This starter shows how to wrap Hexarch authorization into a reusable Langflow custom component.

## Suggested component behavior

- Inputs:
  - `api_url`
  - `api_token`
  - `action`
  - `resource_name`
  - `provider_action`
  - `risk_score`
- Output:
  - structured `Data` object with `allowed`, `decision`, `reason`, and raw response data

## Example starter code

```python
from typing import Any

import httpx
from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema import Data


class HexarchAuthorize(Component):
    display_name = "Hexarch Authorize"
    description = "Calls Hexarch /authorize before a model or tool step runs."
    documentation = "https://github.com/no1rstack/hexarch-guardrails"
    icon = "shield-check"
    name = "hexarch_authorize"

    inputs = [
        MessageTextInput(name="api_url", display_name="API URL", value="http://127.0.0.1:8099"),
        MessageTextInput(name="api_token", display_name="API Token", value="dev-token"),
        MessageTextInput(name="action", display_name="Action", value="invoke_provider"),
        MessageTextInput(name="resource_name", display_name="Resource Name", value="llm-provider"),
        MessageTextInput(name="provider_action", display_name="Provider Action", value="chat_completion"),
        MultilineInput(name="risk_score", display_name="Risk Score", value="7"),
    ]

    outputs = [
        Output(name="auth_result", display_name="Authorization Result", method="authorize")
    ]

    def authorize(self) -> Data:
        payload: dict[str, Any] = {
            "action": self.action,
            "resource": {"name": self.resource_name},
            "context": {
                "client": "langflow",
                "provider_action": self.provider_action,
                "risk_score": int(str(self.risk_score).strip()),
                "workflow": "langflow-pre-execution-policy-gate-demo",
            },
        }

        response = httpx.post(
            f"{self.api_url.rstrip('/')}/authorize",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return Data(data=data)
```

## Notes

- For production use, add error handling and return a `Data` object with an `error` field instead of crashing the flow outright.
- If you want to expose this component to agents later, adapt one of the supported inputs to use `tool_mode=True`.
- To load custom components in Docker, mount the component directory and set `LANGFLOW_COMPONENTS_PATH` as described in the Langflow docs.

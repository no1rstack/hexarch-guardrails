// Code by Zapier — Run Javascript
// Step name: check_policy
//
// PURPOSE
// Call Hexarch Guardrails /authorize before any downstream Zapier action runs.
// The filter step that follows this step checks the `allowed` output field.
// The Zap continues only when allowed === "true".
//
// INPUT DATA (configure in Zapier's Input Data section)
// Map each key to a value from your trigger or a previous step:
//
//   hexarchApiUrl   — base URL of your Hexarch instance (e.g. http://127.0.0.1:8099)
//   hexarchApiToken — API token for authentication (e.g. dev-token)
//   action          — the action being authorized (e.g. "invoke_provider")
//   resourceName    — the resource name (e.g. "llm-provider")
//   providerAction  — what the downstream step will do (e.g. "chat_completion")
//   riskScore       — numeric risk score from your trigger data (e.g. 7)
//   threshold       — maximum allowed risk score (e.g. 5)
//
// NOTE: Code by Zapier does NOT support npm modules. Only fetch (built-in)
// and the standard Node.js library are available.

const hexarchApiUrl   = inputData.hexarchApiUrl   || "http://127.0.0.1:8099";
const hexarchApiToken = inputData.hexarchApiToken || "dev-token";
const action          = inputData.action          || "invoke_provider";
const resourceName    = inputData.resourceName    || "llm-provider";
const providerAction  = inputData.providerAction  || "chat_completion";
const riskScore       = Number(inputData.riskScore)  || 0;
const threshold       = Number(inputData.threshold)  || 5;

const payload = {
  action: action,
  resource: {
    name: resourceName
  },
  context: {
    provider_action: providerAction,
    risk_score:      riskScore,
    threshold:       threshold,
    platform:        "zapier"
  }
};

let result;

try {
  const response = await fetch(`${hexarchApiUrl}/authorize`, {
    method:  "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${hexarchApiToken}`
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  // Normalize allowed to a string so the Filter step can match on "true"/"false"
  // (Zapier Filter text matching works on string values)
  result = {
    allowed:  String(data.allowed === true || data.allowed === "true"),
    decision: data.decision || "UNKNOWN",
    reason:   data.reason   || ""
  };
} catch (err) {
  // If Hexarch is unreachable, fail closed: deny the action
  // This mirrors Hexarch's own failure_mode: FAIL_CLOSED behavior
  result = {
    allowed:  "false",
    decision: "DENY",
    reason:   `Policy engine unreachable: ${err.message}`
  };
}

output = result;

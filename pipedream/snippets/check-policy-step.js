// Step name: check_policy
// Place this as the first code step after the HTTP trigger.
//
// Reads the request body from the HTTP trigger, posts to Hexarch /authorize,
// and returns the full authorization decision for the next step to act on.
//
// Environment variables required (Settings → Environment Variables):
//   HEXARCH_API_URL   — e.g. http://127.0.0.1:8099
//   HEXARCH_API_TOKEN — your API token

import axios from "axios";

export default defineComponent({
  async run({ steps, $ }) {
    const body = steps.trigger.event.body;

    const payload = {
      action: body.action ?? "invoke_provider",
      resource: { name: body.resource_name ?? "llm-provider" },
      context: {
        client: "pipedream",
        provider_action: body.provider_action ?? "chat_completion",
        risk_score: body.risk_score ?? 7,
        threshold: body.threshold ?? 5,
        workflow: steps.trigger.context.workflow_name,
      },
    };

    const response = await axios.post(
      `${process.env.HEXARCH_API_URL}/authorize`,
      payload,
      {
        headers: {
          Authorization: `Bearer ${process.env.HEXARCH_API_TOKEN}`,
          "Content-Type": "application/json",
        },
        // Do not throw on 4xx — let the enforce step handle the decision
        validateStatus: () => true,
      }
    );

    // Export the full Hexarch response for downstream steps
    return response.data;
  },
});

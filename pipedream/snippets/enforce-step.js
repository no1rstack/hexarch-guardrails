// Step name: enforce
// Place this immediately after the check_policy step.
//
// Reads the authorization decision from check_policy. On deny:
//   1. Responds to the HTTP caller with a 403 and a structured error body.
//   2. Calls $.flow.exit() to stop all remaining workflow steps immediately.
//
// On allow, this step is a no-op and the workflow continues normally.

export default defineComponent({
  async run({ steps, $ }) {
    const decision = steps.check_policy.$return_value;

    if (!decision.allowed) {
      await $.respond({
        status: 403,
        headers: { "Content-Type": "application/json" },
        body: {
          allowed: false,
          decision: decision.decision ?? "DENY",
          reason: decision.reason ?? "policy_denied",
          message: "Request blocked by pre-execution policy gate",
        },
      });

      // Terminate the workflow — no downstream steps will run
      return $.flow.exit("Blocked by Hexarch policy gate");
    }

    // Allow: export the decision so downstream steps can log or branch on it
    return { allowed: true, decision: decision.decision };
  },
});

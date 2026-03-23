# Public Distribution Channels

## PyPI release refinement checklist

- **Why this audience cares**: Python developers need verifiable installability and execution paths before adopting governance layers.
- **Which demo to link**: Threshold pre-execution blocking (n8n or Node-RED).
- **Axis**: Pre-execution control, execution stability.
- **Technical framing**: Confirm package metadata and classifiers reflect current API endpoints. Verify README threshold demo commands execute unchanged. Run focused test coverage for `/rules`, `/policies`, and `/authorize` before release tag. Update CHANGELOG with concrete request/response examples from threshold scenario.
- **Link target**: `https://pypi.org/project/hexarch-guardrails/`

## Dev.to article

- **Why this audience cares**: Workflow builders have debugged runaway loops; pre-execution gating is an immediate engineering pattern.
- **Which demo to link**: Threshold pre-execution blocking (n8n version).
- **Axis**: Pre-execution control.
- **Technical framing**: Open with one-sentence runaway-loop failure mode. Walk through threshold rule creation, policy binding, and `/authorize` request/response. Show importable n8n workflow with allow/deny routing. Close with HTTP trace of blocked execution at threshold breach. Total article length: 800 words maximum.
- **Link target**: `https://dev.to/new`

## Medium article

- **Why this audience cares**: Platform teams need deterministic control-plane patterns for AI and automation governance.
- **Which demo to link**: Model usage containment.
- **Axis**: Model containment, AI-specific policy.
- **Technical framing**: Frame as technical note on allowlist + token ceiling enforcement before LLM invocation. Include rule condition JSON, policy binding, and real deny responses for disallowed model and token overage. Position as composable pre-execution pattern adaptable to other provider types. Minimal architecture context; lead with concrete HTTP payloads.
- **Link target**: `https://medium.com/new-story`

## GitHub discussion post

- **Why this audience cares**: Repository users need concrete examples to validate applicability and provide structured feedback.
- **Which demo to link**: Threshold pre-execution blocking (Node-RED version).
- **Axis**: Pre-execution control, execution stability.
- **Technical framing**: See dedicated draft in `GITHUB_DISCUSSION_POST_DRAFT.md`.
- **Link target**: `https://github.com/noir/hexarch-guardrails/discussions`

## n8n forum post

- **Why this audience cares**: n8n users need importable workflow patterns for governance without platform lock-in.
- **Which demo to link**: Threshold pre-execution blocking (n8n version).
- **Axis**: Pre-execution control.
- **Technical framing**: Title: "Pre-execution policy gate for n8n workflows". Body: One-sentence problem (unbounded API calls in loops). Link to importable workflow JSON. Show sample `/authorize` request and deny response. Mention recursion and model containment as adjacent patterns without expanding into those demos. Total post: 150 words maximum.
- **Link target**: `https://community.n8n.io/`

## Node-RED forum post

- **Why this audience cares**: Node-RED developers build reusable flow patterns; switch-based routing on policy decisions is a direct analogy.
- **Which demo to link**: Recursion loop prevention (Node-RED version).
- **Axis**: Execution stability, structural safety.
- **Technical framing**: Title: "Recursion depth guard using external policy check". Body: One-sentence problem (self-triggering flows amplify without visible runtime signal). Link to importable flow JSON with split/switch/authorize pattern. Show depth=2 allow and depth=4 deny responses. Close with pointer to model containment JSON for users extending pattern to AI use cases. Total post: 150 words maximum.
- **Link target**: `https://discourse.nodered.org/`

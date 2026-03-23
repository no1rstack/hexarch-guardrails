# Hexarch Guardrails — Governance Axes

This brief defines the core governance dimensions used to describe Hexarch Guardrails internally. It is intended to keep documentation, implementation notes, and external communications consistent.

1. **Pre-Execution Control**: Decisions are evaluated before downstream side effects occur.
2. **Policy Determinism**: Allow/deny outcomes are computed from explicit rule logic and context.
3. **Identity-Bound Enforcement**: Authorization decisions are tied to actor and scope attributes.
4. **Scope Segmentation**: Policies can be applied at global, organization, team, or user scope.
5. **Execution Stability**: Guard conditions reduce runaway loops and uncontrolled call amplification.
6. **Cost Containment**: Request-level gating constrains unnecessary external API consumption.
7. **Trust Boundary Clarity**: Protected and unprotected paths are separated through explicit enforcement points.
8. **Auditability**: Decision paths and enforcement actions are recorded as verifiable events.
9. **Failure-Mode Explicitness**: Policy behavior under evaluation failure is defined as fail-open or fail-closed.
10. **Orchestrator Portability**: The same enforcement pattern is reusable across workflow runtimes.
11. **Data-Minimal Contexting**: Policy evaluation accepts only the context needed for decision logic.
12. **Operational Composability**: Guardrails integrate as a discrete control layer without replacing orchestration logic.

# Integration Patterns

Pre-execution policy enforcement can be integrated into automation systems using several architectural approaches. Each pattern addresses different operational constraints and deployment topologies.

## Pattern A: Direct Pre-Execution Gate

The orchestrator calls `/authorize` before invoking downstream APIs. Authorization decisions control workflow routing through switch or conditional nodes.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Workflow   │────▶│  /authorize  │────▶│  Continue?  │
│   Trigger   │     │   (Hexarch)  │     │  (If/Switch)│
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                        ┌────────┴────────┐
                                        ▼                 ▼
                                   ┌─────────┐      ┌─────────┐
                                   │  Allow  │      │  Deny   │
                                   │  Branch │      │  Branch │
                                   └─────────┘      └─────────┘
```

**Usage**: Single workflow or agent execution with inline policy check.

**Tradeoff**: Network latency added to every guarded operation; simple to implement and audit.

## Pattern B: Sidecar Policy Proxy

A proxy service wraps the target API and enforces policy before forwarding requests. The orchestrator calls the proxy instead of the target directly.

```
┌─────────────┐     ┌──────────────────────────┐     ┌─────────────┐
│  Workflow   │────▶│   Policy Proxy Service   │────▶│  Target API │
│             │     │  (Hexarch + Forwarding)  │     │  (OpenAI)   │
└─────────────┘     └──────────────────────────┘     └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  /authorize  │
                       │   (Hexarch)  │
                       └──────────────┘
```

**Usage**: Centralized enforcement for multiple workflows calling the same provider.

**Tradeoff**: Requires proxy deployment and routing configuration; reduces per-workflow policy logic duplication.

## Pattern C: Centralized Policy Service for Multiple Orchestrators

Multiple orchestrators (n8n, Node-RED, custom services) call a shared Hexarch instance. Policies segment by scope (TEAM, ORGANIZATION, RESOURCE).

```
┌─────────────┐     ┌──────────────────────────┐
│  n8n Flow   │────▶│                          │
└─────────────┘     │   Centralized Hexarch    │
                    │   Policy Service         │
┌─────────────┐     │  (Scope: ORG, TEAM)      │
│  Node-RED   │────▶│                          │
└─────────────┘     └──────────────────────────┘
                              │
┌─────────────┐               │
│  Custom App │───────────────┘
└─────────────┘
```

**Usage**: Multi-team or multi-workflow environments with shared governance.

**Tradeoff**: Single point of enforcement; requires operational monitoring and availability guarantees.

## Pattern D: Multi-Environment Policy Segmentation

Separate Hexarch instances for dev, staging, and production. Policy rules mirror across environments but differ in threshold values or failure modes.

```
┌──────────────────┐     ┌──────────────────┐
│  Dev Workflow    │────▶│  Hexarch (Dev)   │  FAIL_OPEN, threshold=1000
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  Staging Flow    │────▶│ Hexarch (Staging)│  FAIL_CLOSED, threshold=100
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  Prod Workflow   │────▶│  Hexarch (Prod)  │  FAIL_CLOSED, threshold=50
└──────────────────┘     └──────────────────┘
```

**Usage**: Environment-specific risk tolerance and testing isolation.

**Tradeoff**: Requires policy synchronization tooling; prevents production policy from blocking development experimentation.

## Pattern Selection

- **Pattern A**: Start here for single-workflow validation.
- **Pattern B**: Use when multiple workflows call the same external API and enforcement logic is identical.
- **Pattern C**: Deploy for organizational governance with shared policy across tools.
- **Pattern D**: Required for production-grade deployments with environment-specific risk profiles.

Patterns can combine: a centralized policy service (C) with environment segmentation (D) and sidecar proxies (B) for high-traffic APIs.

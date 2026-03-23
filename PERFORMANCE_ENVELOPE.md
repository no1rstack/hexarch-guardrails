# Performance Envelope

Pre-execution policy enforcement adds latency to the request path. This document defines expected performance characteristics and deployment patterns for latency-sensitive workloads.

## Evaluation Complexity

Policy evaluation scans all rules in matching policies sequentially. For a single `/authorize` request:

- **Policy filtering**: O(P) where P = total policies in system. Filters by requested scope (GLOBAL, ORGANIZATION, etc.).
- **Rule evaluation**: O(R) where R = rules bound to matching policies. Each rule condition evaluates once.
- **Context field resolution**: O(1) per field lookup in context dictionary.
- **Overall**: O(P + R) for typical requests with small constant factors.

**Example**: 
- 10 policies in system, 2 match scope → filter cost is 10 comparisons.
- 5 rules per policy → evaluate 10 rules total.
- Each rule checks 1 context field → 10 field lookups.

For most automation workloads (10-100 policies, 5-20 rules per policy), evaluation time is sub-millisecond on modern hardware.

## Dominant Latency Source

Network round-trip time dominates policy evaluation time. For a typical deployment:

- **Network latency**: 5-50ms (same datacenter: ~5ms, cross-region: 50-200ms).
- **Evaluation time**: 0.5-2ms (10 policies, 20 rules, 10 context fields).
- **Database query** (if rule/policy definitions stored externally): 1-10ms depending on cache hit rate.

**Conclusion**: Reducing network distance between orchestrator and Hexarch provides the largest latency reduction. Optimizing rule count yields marginal improvement unless rule sets exceed 1000 rules per policy.

## Suggested Deployment Topologies

### Topology 1: Co-located with Orchestrator

Deploy Hexarch on the same host or pod as the orchestrator (n8n, Node-RED). Reduces network latency to <1ms via localhost or pod-local networking.

```
┌─────────────────────────┐
│   Host / Pod            │
│  ┌──────────┐           │
│  │  n8n     │──────┐    │
│  └──────────┘      │    │
│                    ▼    │
│  ┌──────────────────┐   │
│  │  Hexarch         │   │
│  │  (localhost:8000)│   │
│  └──────────────────┘   │
└─────────────────────────┘
```

**Use case**: Single-workflow or single-orchestrator deployments with strict latency requirements (<10ms total overhead).

### Topology 2: Centralized Policy Service

Deploy Hexarch as a shared service in the same availability zone as orchestrators. Accept 5-10ms network latency for centralized policy management.

```
┌──────────┐     ┌──────────────┐
│  n8n     │────▶│              │
└──────────┘     │  Hexarch     │
                 │  (shared)    │
┌──────────┐     │              │
│ Node-RED │────▶│              │
└──────────┘     └──────────────┘
```

**Use case**: Multi-team or multi-orchestrator environments requiring policy consistency across workflows.

### Topology 3: Edge Proxy with Cached Policies

Deploy lightweight Hexarch instances at edge locations with policy definitions replicated from central source. Reduces cross-region latency for geographically distributed orchestrators.

```
┌─────────────┐         ┌─────────────┐
│  US-East    │         │  EU-West    │
│  Hexarch    │◀────────│  Central    │
│  (cached)   │  sync   │  Policy DB  │
└─────────────┘         └─────────────┘
      ▲
      │
┌─────────────┐
│  US-East    │
│  n8n        │
└─────────────┘
```

**Use case**: Global deployment with region-specific orchestrators and <20ms latency requirements.

## When Not to Use Inline Policy Checks

Avoid pre-execution policy enforcement for:

### High-frequency, low-latency paths

If the orchestrator must respond in <5ms (e.g., real-time API gateway, in-stream data processing), adding a network round-trip for policy evaluation violates latency budget.

**Alternative**: Use post-execution sampling and async alerting for compliance monitoring.

### Idempotent, low-risk operations

For operations with no side effects (read-only queries, cache lookups), pre-execution enforcement adds overhead without commensurate risk reduction.

**Alternative**: Apply policy enforcement only to stateful or high-cost operations (writes, external API calls, LLM invocations).

### Ultra-high-throughput batch processing

If the workflow processes 10,000+ operations per second, serializing `/authorize` calls creates a bottleneck.

**Alternative**: 
- Apply policy checks at batch boundaries (authorize once per 1000 operations).
- Use local policy evaluation (embed rule engine in orchestrator process).
- Deploy Hexarch with horizontal scaling and connection pooling.

## Performance Benchmarking

To measure policy evaluation impact in your deployment:

1. Call `/authorize` with a test payload 1000 times.
2. Measure p50, p95, and p99 response times.
3. Compare to orchestrator's baseline operation latency.

**Example test**:
```bash
for i in {1..1000}; do
  curl -w "%{time_total}\n" -o /dev/null -s \
    -X POST http://localhost:8000/authorize \
    -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
    -d '{"action":"test","resource":{"name":"test"},"context":{"count":1}}'
done | sort -n | awk '{times[NR]=$1} END {print "p50:", times[int(NR*0.5)], "p95:", times[int(NR*0.95)], "p99:", times[int(NR*0.99)]}'
```

If p95 latency exceeds 50ms, investigate network topology or rule set complexity.

## Summary

- **Complexity**: O(P + R) for policy filtering and rule evaluation.
- **Dominant latency**: Network round-trip (5-50ms) exceeds evaluation time (0.5-2ms).
- **Topology**: Co-locate with orchestrator for <10ms overhead; centralize for policy consistency.
- **Skip inline checks**: For <5ms latency requirements, ultra-high throughput, or idempotent operations.

Transparent performance characteristics allow informed deployment decisions.

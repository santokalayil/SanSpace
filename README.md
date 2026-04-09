# SanSpace

Personal knowledge workspace — research notes, technical references, and agentic workflow config.

## Structure

```
.claude/            VS Code agent skills (diagram-creator, research-library, skill-creator)
docs/
  home_automation/  IoT / home lab reference docs
  protocols/        Protocol deep-dives (A2A, etc.)
  research/         Technology research notes and implementation ideas
repos/              Cloned third-party repos for local reference (git-ignored)
```

## docs

### research/

| File | Description |
|------|-------------|
| [langfuse_python_tracing_evals.md](docs/research/langfuse_python_tracing_evals.md) | Langfuse Python SDK v4.0.6 full reference — OTel-native tracing, scores, datasets, evals (746 lines) |
| [langfuse_sim_search_qna_idea.md](docs/research/langfuse_sim_search_qna_idea.md) | Eval strategy for a retrieval-only QnA system (Cosmos DB vector search, no LLM). Advanced patterns: Precision@K, ground truth mining, doc analytics, A/B embedding tests, rollout maturity model |
| [langfuse_sim_search_qna_idea_with_llm.md](docs/research/langfuse_sim_search_qna_idea_with_llm.md) | Companion doc — same system with LLM augmentation (RAG). LLM-as-judge evals, faithfulness/hallucination scoring, prompt management, cost tracking |

### home_automation/

| File | Description |
|------|-------------|
| [zigbee_mqtt_mosquitto.md](docs/home_automation/zigbee_mqtt_mosquitto.md) | Zigbee2MQTT + Mosquitto primer — QoS, topics/wildcards, LWT, retained messages, MQTT 5, TLS/ACL |

### protocols/

| File | Description |
|------|-------------|
| [a2a/a2a-protocol.md](docs/protocols/a2a/a2a-protocol.md) | Agent-to-Agent (A2A) protocol reference |

## repos (git-ignored)

Cloned locally for source reading and research — not tracked in this repo.

| Repo | Used for |
|------|----------|
| `langfuse-python` | SDK source reference for Langfuse Python SDK v4.x (OTel-native) |
| `a2a-python` | A2A protocol Python SDK source |
| `skills` | Anthropic skills reference repo |

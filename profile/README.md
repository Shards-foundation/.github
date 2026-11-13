<div align="center">

<img src="https://raw.githubusercontent.com/Shards-foundation/.github/main/profile/assets/shards-inc-animated.gif" alt="Animated Shards Inc logo" width="620" />

# Shards Foundation

**Open-source infrastructure for governable autonomous AI.**

*Deterministic control · Agent orchestration · Practical automation*

[![Profile views](https://komarev.com/ghpvc/?username=Shards-foundation&label=Profile%20views&color=ef8d32&style=flat-square)](https://github.com/Shards-foundation)
[![GitHub followers](https://img.shields.io/github/followers/Shards-foundation?label=Followers&logo=github&style=flat-square&color=ef8d32)](https://github.com/orgs/Shards-foundation/followers)

[Explore repositories](https://github.com/orgs/Shards-foundation/repositories) · [Shards-Kernel](https://github.com/Shards-foundation/Shards-kernel) · [PyPI package](https://pypi.org/project/shards-kernel/)

</div>

---

## Shards in motion

<div align="center">

[![Watch Shards showcase](https://raw.githubusercontent.com/Shards-foundation/.github/main/profile/assets/shards-showcase.gif)](https://raw.githubusercontent.com/Shards-foundation/.github/main/profile/assets/shards-showcase.mp4)

[▶ Watch the video](https://raw.githubusercontent.com/Shards-foundation/.github/main/profile/assets/shards-showcase.mp4)

*15-second SHARDS INC showcase · tap to watch the full video with audio.*

</div>

## What we're building

Shards Foundation is the open-source engineering home for the wider Shards ecosystem. Our work explores how AI agents can operate usefully **without treating model output as permission to act**.

The direction is deliberately modular: agent runtimes, orchestration, policy-controlled execution, audit trails, retrieval, and applications that can use those foundations. Projects are at different levels of maturity; a repository's design or roadmap does **not** imply that its integrations have been deployed.

## Featured projects

### Control, governance and agent infrastructure

| Project | Focus | Status / scope |
| --- | --- | --- |
| **[Shards-Kernel](https://github.com/Shards-foundation/Shards-kernel)** | Python package providing deterministic execution decisions, scoped permits and hash-chained audit evidence. | **Published on [PyPI](https://pypi.org/project/shards-kernel/)**; local reference operations, not a general-purpose OS or sandbox. |
| **[Shards Agent Core](https://github.com/Shards-foundation/shards-agent-core)** | Modular Python agent runtime, specialist agents and workflow coordination. | Framework and integration work. |
| **[Shards Swarm Agent](https://github.com/Shards-foundation/Shards-Swarm-Agent)** | Multi-agent registration, task coordination, workflow and monitoring prototype. | **Alpha**; not production-ready. |
| **[Super-Intelligence Agent](https://github.com/Shards-foundation/Shards-Super-Intelligence-Agent)** | Multi-provider agent framework experiments and local API scaffold. | **Experimental**; not a deployed service. |
| **[AgentMesh](https://github.com/Shards-foundation/AgentMesh)** | Architecture for connecting agent swarms and messaging-platform bot networks. | Integration-oriented project. |

### AI platforms, data and automation

| Project | Focus |
| --- | --- |
| **[Omni-LLM Orchestrator](https://github.com/Shards-foundation/omni-llm-orchestrator)** | Intent-aware multi-model routing, weighted response synthesis and chat UI. |
| **[Shards RAG](https://github.com/Shards-foundation/Shards-Rag)** | Enterprise document retrieval and AI knowledge-hub application. |
| **[Workflow Hub](https://github.com/Shards-foundation/shards-workflow-hub)** | Business operations, connected tools and workflow orchestration. |
| **[Shards Playbooks](https://github.com/Shards-foundation/shards-playbooks)** | Reusable operational workflows, automation patterns and engineering guidance. |
| **[Revenue Engine](https://github.com/Shards-foundation/Shards-Revenue-Engine)** | Early-stage digital-product, payment and fulfilment automation. **Alpha**, not a live commercial service. |

### Research and specialised applications

| Project | Focus |
| --- | --- |
| **[Shards Agent Trading Network](https://github.com/Shards-foundation/Shards-Agent-Trading-Network)** | Agent profiles, verifiable journals, read-only market data and simulated paper execution. **Live trading is disabled.** |
| **[PATENT-OS](https://github.com/Shards-foundation/PATENT-OS)** | AI-supported patent and prior-art research. Not legal advice. |
| **[Nexus Components Library](https://github.com/Shards-foundation/Components-library)** | React component library and AI-assisted UI playground. |
| **[Lumina](https://github.com/Shards-foundation/Lumina)** | Headless commerce application and integration patterns. |
| **[AI Agent Sketchbook](https://github.com/Shards-foundation/ai-agent-sketchbook)** | Planning, prototyping and governance-oriented agent workspace. |

## Start here: Shards-Kernel

[![PyPI](https://img.shields.io/pypi/v/shards-kernel?label=shards-kernel%20on%20PyPI)](https://pypi.org/project/shards-kernel/)
[![CI](https://github.com/Shards-foundation/Shards-kernel/actions/workflows/ci.yml/badge.svg)](https://github.com/Shards-foundation/Shards-kernel/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-orange)](https://github.com/Shards-foundation/Shards-kernel/blob/main/LICENSE)

Shards-Kernel separates an agent's **proposed action** from an **authorised action**. It provides a concrete starting point for exploring fail-closed decisions, permits and audit evidence.

```bash
python -m pip install shards-kernel
shards-kernel --version
shards-kernel demo --json
```

The demo runs local reference tools. It **does not** connect an agent to GitHub, wallets, trading venues or infrastructure by itself. For supported commands and integration boundaries, see the [package README](https://github.com/Shards-foundation/Shards-kernel#readme) and [agent quickstart](https://github.com/Shards-foundation/Shards-kernel/blob/main/docs/AGENT_QUICKSTART.md).

## How the pieces relate

```text
Applications & operator interfaces
           |
Agent runtimes / orchestration
           |
Policy, permissions & audit boundary  <-- Shards-Kernel
           |
Trusted tool adapters / APIs / data
           |
      External systems
```

**This is the intended architectural direction, not a claim that every linked repository already integrates with Shards-Kernel.** An actual deployment needs its own authentication, isolation, secrets management, monitoring, operational controls and testing.

## Contribute

The repositories are public so developers can inspect the implementation, evaluate design decisions and propose improvements. Start with a project's README, check its licence and contribution guidelines, and open an **issue or pull request in that repository**.

- [Browse all public repositories](https://github.com/orgs/Shards-foundation/repositories)
- [Shards-Kernel issues](https://github.com/Shards-foundation/Shards-kernel/issues)
- [Foundation GitHub profile source](https://github.com/Shards-foundation/.github/blob/main/profile/README.md)

## Support Shards

Support the wider Shards ecosystem, including open-source projects, developer tools and ongoing development. Contributions are voluntary.

<div align="center">

<a href="https://www.paypal.com/ncp/payment/PLB-FL23DP5NGC4S"><img src="https://img.shields.io/badge/Support%20Shards-PayPal-003087?style=for-the-badge&logo=paypal&logoColor=white" alt="Support Shards via PayPal" height="40" /></a>
<a href="https://buymeacoffee.com/shardsinc"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Support Shards on Buy Me a Coffee" height="40" /></a>

</div>

<sub>Shards Foundation · Building useful autonomous systems with explicit boundaries.</sub>

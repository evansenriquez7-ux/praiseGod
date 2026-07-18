# AI Agent Workflow (Graphify & MCP)

To ensure Large Language Models (LLMs) and autonomous agents can dynamically understand and navigate this entire repository efficiently, the project is integrated with **Graphify** via the **Model Context Protocol (MCP)**.

## The Pipeline
1. **Automated Graphing (Git Hook):** A local `.git/hooks/pre-commit` script is installed. Every time a developer commits code, Graphify automatically scans the repository, builds a new semantic AST graph, and overwrites `graphify-out/graph.json`. This JSON graph is instantly bundled with the commit.
2. **Optimized Inference:** Instead of parsing hundreds of raw files, the agent queries the Graphify server dynamically for shortest-paths and community summaries, significantly increasing context window efficiency and precision.

## Agent Environment
Any agent initialized in this repository must use its Graphify MCP connection to map, plan, and execute adjustments purely derived from the live GitHub repository graph.

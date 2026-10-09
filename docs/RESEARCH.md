# Design notes

I looked at a few existing coding agents and how they structure the tool-use loop, planning, and safety before building this one.

Main ideas I kept:

- Simple tool-calling loop (model → tools → results → model)
- Explicit todo list so progress is visible
- Keep old tool results short so the context doesn’t explode
- Strict sandbox for file access
- Command execution is optional and limited

I deliberately kept the scope small: no sub-agents, no hooks, no MCP. Just the core loop + a usable GUI/CLI.

The system prompt and tool design are in `code_agent/prompts.py` and `code_agent/tools.py`.

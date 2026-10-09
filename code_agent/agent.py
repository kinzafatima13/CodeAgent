"""The agent loop: LLM <-> tools until the model calls `finish` and the deliverable check passes."""
from __future__ import annotations

import copy
import json
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any

from .config import Settings
from .llm import DeepSeekClient, ToolCall, Message
from .tools import Workspace, TOOL_SCHEMAS
from .prompts import SYSTEM_PROMPT, build_task_message


@dataclass
class AgentEvent:
    kind: str
    data: Any = None


class CodeAgent:
    def __init__(self, settings: Settings, workspace: Workspace, on_event: Optional[Callable[[AgentEvent], None]] = None):
        self.settings = settings
        self.workspace = workspace
        self.on_event = on_event or (lambda e: None)
        self.client = DeepSeekClient(settings)
        self.messages: List[Dict] = []
        self.todos: List[Dict] = []
        self.turn = 0
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def _emit(self, kind: str, data=None):
        self.on_event(AgentEvent(kind, data))

    def _compact(self):
        """Shorten old bulky tool results so context stays manageable."""
        if len(self.messages) < 12:
            return
        for i, m in enumerate(self.messages[:-6]):
            if m.get("role") == "tool" and isinstance(m.get("content"), str) and len(m["content"]) > 800:
                self.messages[i] = {**m, "content": m["content"][:400] + "\n...[truncated]..."}

    def check_deliverables(self) -> List[str]:
        missing = []
        required = ["README.md", "Dockerfile"]
        files = self.workspace.list_files("")
        names = {f.split("/")[-1] for f in files}
        for r in required:
            if r not in names and r not in files:
                missing.append(r)
        has_src = any(f.endswith((".py", ".js", ".ts")) for f in files)
        if not has_src:
            missing.append("source files")
        has_tests = any("test" in f.lower() for f in files)
        if not has_tests:
            missing.append("tests")
        has_manifest = any(f in files or f.split("/")[-1] in ("package.json", "requirements.txt") for f in files)
        if not has_manifest:
            missing.append("dependency manifest")
        return missing

    def run(self, compact_input_json: str, extra_instructions: str = "") -> None:
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_task_message(compact_input_json, extra_instructions)},
        ]
        self._emit("status", "starting")
        max_turns = self.settings.max_turns
        finish_rejects = 0

        while self.turn < max_turns and not self._stop.is_set():
            self.turn += 1
            self._emit("turn", self.turn)
            self._compact()
            try:
                resp = self.client.chat(self.messages, tools=TOOL_SCHEMAS)
            except Exception as e:
                self._emit("error", str(e))
                break

            msg = resp.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content")

            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            if reasoning:
                assistant_msg["reasoning_content"] = reasoning
            self.messages.append(assistant_msg)

            if content:
                self._emit("assistant", content[:500])

            if not tool_calls:
                self._emit("status", "model stopped without finish")
                break

            for tc in tool_calls:
                name = tc.get("function", {}).get("name") or tc.get("name")
                args_raw = tc.get("function", {}).get("arguments") or tc.get("arguments") or "{}"
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                except json.JSONDecodeError:
                    args = {}
                    result = f"Error: could not parse arguments for {name}"
                else:
                    if name == "finish":
                        missing = self.check_deliverables()
                        if missing and finish_rejects < 2:
                            finish_rejects += 1
                            result = f"Cannot finish yet. Missing: {', '.join(missing)}. Keep working."
                        else:
                            self._emit("finish", args)
                            self.messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": "ok"})
                            return
                    else:
                        result = self.workspace.execute(name, args)
                        if name == "todo_write":
                            self.todos = args.get("todos") or self.todos
                            self._emit("todos", self.todos)

                self._emit("tool", {"name": name, "result": str(result)[:300]})
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": str(result)[:8000],
                })

        self._emit("status", "max turns or stopped")

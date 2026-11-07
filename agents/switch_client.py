"""Minimal Switch agent-protocol client: WebSocket in, HTTP out (docs.switchagents.ai, "The agent protocol").

- Opens /agents/{id}/connection/ws?connection_id=...&rooms=...&filter=all with the agent's API key.
- Answers every `ping` with {"type": "pong", "cursor": n} BEFORE handling events.
- Resumes after a drop with start_from + expected_generation; stops on `taken_over`.
- Posts with POST /agents/{id}/message {room_id, content} (needs no connection).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.request
import uuid
from pathlib import Path
from typing import Awaitable, Callable

import websockets

ROOT = Path(__file__).resolve().parent.parent
AGENTS_FILE = ROOT / ".agents.json"  # gitignored: holds agent API keys
log = logging.getLogger("switch")


def console_ports() -> dict:
    """Ports Switch Console picked for the local server (they change on every restart)."""
    path = Path(os.environ.get("APPDATA", "")) / "switchdash" / "local-switch-server" / "ports.json"
    return json.loads(path.read_text()) if path.exists() else {}


def base_url() -> str:
    if os.environ.get("SWITCH_URL"):
        return os.environ["SWITCH_URL"].rstrip("/")
    api = console_ports().get("api")
    if not api:
        raise SystemExit("Set SWITCH_URL (the server address), or run Switch Console's local server.")
    return f"http://127.0.0.1:{api}"


def load_agents() -> dict:
    return json.loads(AGENTS_FILE.read_text()) if AGENTS_FILE.exists() else {}


def http(method: str, url: str, body: dict | None = None, headers: dict | None = None, opener=None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with (opener.open if opener else urllib.request.urlopen)(req, timeout=30) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


Handler = Callable[[dict], Awaitable[list[str]]]


class AgentConnection:
    def __init__(self, name: str, room_id: str, handler: Handler):
        creds = load_agents().get(name)
        if not creds:
            raise SystemExit(f"Agent '{name}' is not registered. Run: python scripts/register_agents.py")
        self.name, self.agent_id, self.key = name, creds["id"], creds["api_key"]
        self.room_id = room_id
        self.handler = handler
        self.connection_id = creds.get("connection_id") or str(uuid.uuid5(uuid.NAMESPACE_URL, f"paidsafe/{name}"))
        self.base = base_url()
        self.cursor: int | None = None
        self.generation = None

    def post(self, content: str) -> None:
        http("POST", f"{self.base}/agents/{self.agent_id}/message", {"room_id": self.room_id, "content": content},
             {"Authorization": f"Bearer {self.key}"})

    def op(self, name: str, args: dict) -> dict:
        """Call an agent-protocol operation bound to this connection's room."""
        return http("POST", f"{self.base}/agents/{self.agent_id}/ops/{name}", args,
                    {"Authorization": f"Bearer {self.key}", "X-Switch-Connection-Id": self.connection_id})

    def ws_url(self) -> str:
        ws = self.base.replace("http://", "ws://").replace("https://", "wss://")
        q = f"connection_id={self.connection_id}&rooms={self.room_id}&filter=all&scope=single&client=paidsafe-{self.name}"
        if self.cursor is not None:
            q += f"&start_from={self.cursor}"
        if self.generation is not None:
            q += f"&expected_generation={self.generation}"
        return f"{ws}/agents/{self.agent_id}/connection/ws?{q}"

    async def run(self) -> None:
        queue: asyncio.Queue = asyncio.Queue()
        worker = asyncio.create_task(self._work(queue))
        backoff = 1
        try:
            while True:
                try:
                    async with websockets.connect(self.ws_url(),
                                                  additional_headers={"Authorization": f"Bearer {self.key}"},
                                                  ping_interval=None, max_size=None) as ws:
                        backoff = 1
                        async for raw in ws:
                            frame = json.loads(raw)
                            kind = frame.get("type") or frame.get("event")
                            if kind == "ping":  # answer pings first, always
                                await ws.send(json.dumps({"type": "pong", "cursor": self.cursor or 0}))
                                continue
                            if kind == "connection_state":
                                self.generation = frame.get("generation")
                                log.info("%s connected: rooms=%s cursor=%s", self.name, frame.get("rooms"), frame.get("cursor"))
                                continue
                            if kind == "evicted":
                                log.warning("%s evicted: %s", self.name, frame)
                                if frame.get("code") in ("taken_over", "closed"):
                                    return
                                break
                            if kind == "refused":
                                log.error("%s refused: %s", self.name, frame)
                                return
                            if kind == "gap":
                                self.cursor = frame.get("resumed_at", self.cursor)
                                continue
                            if frame.get("event") in ("message", "command", "room_join"):
                                self.cursor = frame.get("id", self.cursor)
                                queue.put_nowait(frame["data"])
                except (OSError, websockets.ConnectionClosed, websockets.InvalidStatus) as e:
                    log.warning("%s connection dropped (%s); reconnecting in %ss", self.name, e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15)
        finally:
            worker.cancel()

    async def _work(self, queue: asyncio.Queue) -> None:
        while True:
            data = await queue.get()
            if data.get("type") != "message" or data.get("room_id") != self.room_id:
                continue
            p = data.get("payload", {})
            log.info("%s <- %s (%s) addressed=%s: %s", self.name, p.get("sender_name"), p.get("sender"),
                     p.get("addressed"), (p.get("body") or "")[:80].replace("\n", " "))
            try:
                replies = await self.handler(p)
            except Exception:
                log.exception("%s handler failed", self.name)
                continue
            for r in replies:
                try:
                    await asyncio.to_thread(self.post, r)
                except Exception:
                    log.exception("%s post failed", self.name)

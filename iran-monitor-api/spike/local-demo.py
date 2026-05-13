"""End-to-end local demo of the A2A protocol surface.

Runs against the MockBackend on :8081 (echo agent — completes in <1s) so you
can see the full submit → SSE-stream → completed cycle without waiting on
real LLM calls. Then makes a real call against the iran-monitor backend on
:8080 to show the agent card + submit working with the production code path
(the actual perspective stack only runs if the worker is started).

Run:
    uv run python spike/local-demo.py

Prereq:
    Two servers running in the background:
      uv run iran-monitor-api                       # → :8080
      uv run python -m a2a_protocol._mock_server    # → :8081
"""

from __future__ import annotations

import asyncio
import json
import sys
import time

import httpx


async def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


async def show_card(base_url: str, label: str) -> dict:
    await section(f"{label}: agent card discovery")
    r = await asyncio.get_event_loop().run_in_executor(
        None, lambda: httpx.get(f"{base_url}/.well-known/agent-card.json", timeout=5),
    )
    print(f"GET {base_url}/.well-known/agent-card.json → {r.status_code}")
    card = r.json()
    print(f"\nAgent name:        {card['name']}")
    print(f"Description:       {card['description'][:120]}…")
    print(f"Version:           {card['version']}")
    print(f"Protocol version:  {card['protocolVersion']}")
    print(f"Capabilities:      streaming={card['capabilities']['streaming']}  "
          f"push={card['capabilities']['pushNotifications']}  "
          f"granularity={card['capabilities'].get('streamingGranularity', 'n/a')}")
    print(f"Auth:              {card['authentication']['schemes']}")
    print(f"Skills ({len(card['skills'])}):")
    for s in card["skills"]:
        print(f"   - {s['id']}: {s['name']}")
        print(f"     {s['description'][:120]}…")
        if s.get("examples"):
            print(f"     example: {s['examples'][0][:90]}…")
    return card


async def jsonrpc(base_url: str, method: str, params: dict, *, token: str) -> dict:
    envelope = {"jsonrpc": "2.0", "id": str(time.time()), "method": method, "params": params}
    r = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: httpx.post(
            f"{base_url}/v1/jsonrpc",
            json=envelope,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        ),
    )
    body = r.json()
    return body


async def mock_full_cycle() -> None:
    """Show the full A2A cycle against MockBackend — fast, deterministic."""
    BASE = "http://127.0.0.1:8081"
    TOKEN = "mock-key"

    card = await show_card(BASE, "MOCK BACKEND (port 8081)")

    await section("MOCK BACKEND: message/send (synchronous)")
    msg = {
        "role": "user",
        "parts": [{"kind": "text", "text": "ping — show me the protocol working"}],
    }
    body = await jsonrpc(BASE, "message/send", {"message": msg}, token=TOKEN)
    if "error" in body:
        print("ERROR:", body["error"])
        return
    task_id = body["result"]["id"]
    print(f"Submitted. task_id = {task_id}")
    print(f"Initial status: {body['result']['status']['state']}")

    # MockBackend completes asynchronously; poll until done
    await section("MOCK BACKEND: tasks/get (polling)")
    for i in range(20):
        body = await jsonrpc(BASE, "tasks/get", {"id": task_id}, token=TOKEN)
        state = body["result"]["status"]["state"]
        artifacts = len(body["result"].get("artifacts", []))
        print(f"  poll {i+1}: state={state}  artifacts={artifacts}")
        if state in ("completed", "failed", "canceled", "rejected"):
            break
        await asyncio.sleep(0.1)

    if body["result"].get("artifacts"):
        a = body["result"]["artifacts"][0]
        text = next((p["text"] for p in a["parts"] if p["kind"] == "text"), "")
        print(f"\nFinal artifact ({a['name']}): {text}")

    await section("MOCK BACKEND: streaming (message/stream + SSE)")
    print("Streaming a new submission via SSE…")
    envelope = {
        "jsonrpc": "2.0", "id": "stream-1", "method": "message/stream",
        "params": {"message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "stream-test"}],
        }},
    }
    async with httpx.AsyncClient(timeout=10) as ac:
        async with ac.stream(
            "POST", f"{BASE}/v1/jsonrpc/stream",
            json=envelope,
            headers={"Authorization": f"Bearer {TOKEN}"},
        ) as r:
            print(f"  HTTP {r.status_code}  Content-Type: {r.headers.get('content-type')}")
            event_count = 0
            buffer: list[str] = []
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    buffer.append(line[5:].lstrip())
                elif line == "" and buffer:
                    payload = json.loads("".join(buffer))
                    buffer.clear()
                    result = payload.get("result", {})
                    kind = result.get("kind", "?")
                    extra = ""
                    if kind == "status-update":
                        extra = f"state={result['status']['state']}  final={result.get('final', False)}"
                    elif kind == "artifact-update":
                        a = result.get("artifact", {})
                        extra = f"artifact={a.get('name', '?')}"
                    print(f"  SSE event #{event_count + 1}  kind={kind}  {extra}")
                    event_count += 1
                    if kind == "status-update" and result.get("final"):
                        break


async def iran_monitor_submit() -> None:
    """Demonstrate the real backend handling a JSON-RPC submission. The full
    pipeline takes 8-25 min (perspective subagents); we just show submit +
    initial task state. To watch the full pipeline run, start the worker
    in another shell: `uv run iran-monitor-worker`."""
    BASE = "http://127.0.0.1:8080"
    TOKEN = "dev-key-local"

    card = await show_card(BASE, "IRAN MONITOR (port 8080)")

    await section("IRAN MONITOR: REST surface still works (back-compat)")
    r = httpx.post(
        f"{BASE}/v1/queries",
        json={
            "scenario": (
                "Iran launches a meaningfully disruptive cyber attack on German "
                "critical infrastructure within 30 days, with German government "
                "public attribution."
            ),
            "horizon": "30d",
            "tier": "standard",
        },
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=5,
    )
    print(f"POST /v1/queries → HTTP {r.status_code}")
    if r.status_code == 202:
        body = r.json()
        print(f"  query_id: {body['query_id']}")
        print(f"  status:   {body['status']}")
        print(f"  estimated completion: {body['estimated_completion_utc']}")

    await section("IRAN MONITOR: A2A JSON-RPC surface (data-part submission)")
    msg = {
        "role": "user",
        "parts": [{"kind": "data", "data": {
            "scenario": (
                "Iran launches a meaningfully disruptive cyber attack on German "
                "critical infrastructure within 30 days, with German government "
                "public attribution."
            ),
            "horizon": "30d",
            "tier": "premium",
        }}],
    }
    body = await jsonrpc(BASE, "message/send", {"message": msg}, token=TOKEN)
    if "error" in body:
        print("ERROR:", body["error"])
        return
    task = body["result"]
    print(f"task_id:      {task['id']}")
    print(f"status:       {task['status']['state']}")
    print(f"tier:         {task['metadata'].get('tier')}")
    print(f"horizon:      {task['metadata'].get('horizon')}")
    print(f"perspectives_invoked: {len(task['metadata'].get('perspectives_invoked', []))}")

    await section("IRAN MONITOR: tasks/get on the submitted task")
    body = await jsonrpc(BASE, "tasks/get", {"id": task["id"]}, token=TOKEN)
    print(f"state: {body['result']['status']['state']}")
    print(f"history length: {len(body['result'].get('history', []))}")
    print(f"artifacts: {len(body['result'].get('artifacts', []))}")
    print()
    print("(Task sits at 'submitted' until you run `uv run iran-monitor-worker` in")
    print("another shell — the worker is what claims tasks from the queue and runs")
    print("the perspective stack. Production deploys run the worker as a systemd")
    print("service alongside the API.)")


async def main() -> None:
    print()
    print("Iran Monitor A2A — local end-to-end demo")
    print("Prereq: two servers running in the background.")
    print("  Iran monitor API:  http://127.0.0.1:8080  (uv run iran-monitor-api)")
    print("  Mock backend:      http://127.0.0.1:8081  (uv run python -m a2a_protocol._mock_server)")

    # Quick reachability check
    for base, label in [("http://127.0.0.1:8080", "iran-monitor"),
                        ("http://127.0.0.1:8081", "mock")]:
        try:
            r = httpx.get(f"{base}/healthz", timeout=2)
            print(f"  {label:13s} {base} → {r.status_code} {r.text}")
        except Exception as e:
            print(f"  {label:13s} {base} → NOT RUNNING ({type(e).__name__})")
            print(f"\n  Start it first, then re-run this demo.")
            sys.exit(1)

    await mock_full_cycle()
    await iran_monitor_submit()
    print()
    print("Done. See ONBOARDING.md for the full integration story.")


if __name__ == "__main__":
    asyncio.run(main())

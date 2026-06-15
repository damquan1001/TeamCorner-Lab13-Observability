import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")


def server_python() -> str:
    windows_python = Path(".venv/Scripts/python.exe")
    posix_python = Path(".venv/bin/python")
    if windows_python.exists():
        return str(windows_python)
    if posix_python.exists():
        return str(posix_python)
    return sys.executable


def wait_for_server(base_url: str, timeout_s: float = 10.0) -> bool:
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            r = httpx.get(f"{base_url}/health", timeout=1.0)
            if r.status_code == 200:
                return True
        except httpx.HTTPError:
            time.sleep(0.25)
    return False


def ensure_server(base_url: str) -> subprocess.Popen | None:
    if wait_for_server(base_url, timeout_s=1.0):
        return None

    print(f"No server detected at {base_url}; starting uvicorn for this load test...")
    process = subprocess.Popen(
        [server_python(), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if wait_for_server(base_url, timeout_s=10.0):
        return process

    process.terminate()
    raise RuntimeError(f"Server did not become ready at {base_url}")


def send_request(client: httpx.Client, base_url: str, payload: dict) -> None:
    try:
        start = time.perf_counter()
        r = client.post(f"{base_url}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        print(f"[{r.status_code}] {r.json().get('correlation_id')} | {payload['feature']} | {latency:.1f}ms")
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--base-url", default=BASE_URL, help="FastAPI base URL")
    args = parser.parse_args()

    lines = [line for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    server_process = ensure_server(args.base_url)

    try:
        with httpx.Client(timeout=30.0) as client:
            if args.concurrency > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                    futures = [executor.submit(send_request, client, args.base_url, json.loads(line)) for line in lines]
                    concurrent.futures.wait(futures)
            else:
                for line in lines:
                    send_request(client, args.base_url, json.loads(line))
    finally:
        if server_process is not None:
            server_process.terminate()
            server_process.wait(timeout=5)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Plato behind a local copy of the dev-daily gateway, for browser checks.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

dev-daily serves Plato at ``https://dev-daily-gw.jazzx.dev/plato/``: the gateway strips ``/plato`` and sends
``X-Forwarded-Prefix: /plato``. This starts a Plato in the dev-daily posture on a throwaway SQLite database in a
temporary directory (never :8000 or its Postgres), puts a small reverse proxy in front of it that does what the gateway
does, and prints the URL to open. No provider key is passed down, so no model call can happen.

    python scripts/local/plato_gateway_emulation.py            # runs until Ctrl-C, then removes the temp directory
    python scripts/local/plato_gateway_emulation.py --check    # fetch every page through the proxy, report, exit

The proxy forwards what the app sends, redirects included, so a link or redirect that forgets the mount shows up as a
404 in the browser, as it would behind the gateway.
"""

from __future__ import annotations

import argparse
import http.client
import http.server
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

DEFAULT_TREE = "/Users/sangit/src/japes-v27"
DEFAULT_MOUNT = "/plato"
DEFAULT_TENANTS = "acra-lending"
DEFAULT_ENVIRONMENT = "dev-daily"
HEALTH_WAIT_SECONDS = 90
PROXY_READ_CHUNK = 8192
UPSTREAM_TIMEOUT_SECONDS = 300
CHECK_TIMEOUT_SECONDS = 30
MIGRATE_TIMEOUT_SECONDS = 120
#: The variables a workstation shell may hold that would let Plato reach a provider or another service.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "GEMINI_API_KEY",
                "AI_GATEWAY_BASE_HOST", "AI_GATEWAY_API_KEY", "KNOWLEDGE_HUB_URL", "JAPES_KNOWLEDGE_HUB_URL",
                "KNOWLEDGE_HUB_TOKEN", "JAPES_KNOWLEDGE_HUB_TOKEN", "DATABASE_URL", "JAPES_DATABASE_URL")
#: Hop-by-hop headers a proxy does not forward.
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
              "transfer-encoding", "upgrade", "host", "content-length"}
#: The pages `--check` opens through the proxy, relative to the mount.
CHECK_PATHS = ("/", "/docs", "/internals", "/api/v1/blueprints/ui", "/api/v1/ontology/ui", "/api/v1/packs/ui",
               "/api/v1/info/ui", "/api/v1/logs/ui", "/api/v1/coverage/ui", "/api/v1/vocabulary/ui")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def plato_env(tree: Path, scratch: Path, port: int, tenants: str, environment: str = DEFAULT_ENVIRONMENT,
              extra_pythonpath: str = "", extra_env: tuple[str, ...] = ()) -> dict[str, str]:
    """The environment of the Plato process: a deployed posture (dev-daily by default; ``local`` admits writes) on a database of its own."""
    env = {k: v for k, v in os.environ.items()
           if k not in STRIPPED_ENV and not re.search(r"POSTGRES|^PG|DATABASE|DB_", k.upper())}
    empty_env_file = scratch / "empty.env"
    empty_env_file.write_text("", encoding="utf-8")
    env.update({
        "PYTHONPATH": os.pathsep.join([p for p in (extra_pythonpath, str(tree), str(tree / "jazzx_plato_client")) if p]),
        "JAPES_ENV_FILE": str(empty_env_file),
        "JAPES_ENVIRONMENT": environment,
        "PORT": str(port),
        "PLATO_WIRING": "plato.wiring.default:build",
        "PLATO_PROFILE": "packs",
        "JAPES_RUN_MODE": "server",
        "PLATO_DB_BACKEND": "sqlite",
        "PLATO_SQLITE_PATH": str(scratch / "plato.db"),
        "PLATO_TENANTS": tenants,
        "PLATO_PACK_BLOB_DIR": str(scratch / "pack-blobs"),
        "PLATO_PACK_CACHE_DIR": str(scratch / "pack-cache"),
        "JAPES_LOCAL_DATA_DIR": str(scratch / "documents"),
    })
    env.update(item.split("=", 1) for item in extra_env)
    return env


#: Migrates the throwaway file to the revision the image expects, through the image's own migration (what the Details
#: page's migrate does).
MIGRATE = """
import asyncio
import os
from jazzx_sdk.fabric.db.store import DbStore
from plato.boot.schema_version import upgrade_to_head

async def main():
    db = DbStore(backend="sqlite", sqlite_path=os.environ["PLATO_SQLITE_PATH"])
    print("migrated to", await upgrade_to_head(db))
    await db.dispose()

asyncio.run(main())
"""

#: Ports a shared Postgres listens on; a Plato of this script's must hold no connection to one.
SHARED_POSTGRES_PORTS = (5432, 55432)


class Gateway(http.server.BaseHTTPRequestHandler):
    """Strips the mount, forwards to Plato with ``X-Forwarded-Prefix``, streams the answer back."""

    mount = DEFAULT_MOUNT
    upstream_port = 0

    def _forward(self) -> None:
        if self.path != self.mount and not self.path.startswith((self.mount + "/", self.mount + "?")):
            self.send_error(404, f"the gateway routes {self.mount} only")
            return
        path = self.path[len(self.mount):] or "/"
        if not path.startswith("/"):
            path = "/" + path
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        headers["X-Forwarded-Prefix"] = self.mount
        headers["Host"] = f"127.0.0.1:{self.upstream_port}"
        upstream = http.client.HTTPConnection("127.0.0.1", self.upstream_port, timeout=UPSTREAM_TIMEOUT_SECONDS)
        try:
            upstream.request(self.command, path, body=body, headers=headers)
            response = upstream.getresponse()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in HOP_BY_HOP:
                    self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()
            while chunk := response.read1(PROXY_READ_CHUNK):
                self.wfile.write(chunk)
                self.wfile.flush()
        except (ConnectionError, TimeoutError, OSError) as exc:
            self.send_error(502, f"upstream: {exc}")
        finally:
            upstream.close()

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _forward

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        sys.stderr.write(f"[gateway] {self.command} {self.path} -> {fmt % args}\n")


def holds_shared_postgres(pid: int) -> str:
    """The lsof line of any connection ``pid`` holds to a shared Postgres port, or an empty string."""
    out = subprocess.run(["lsof", "-nP", "-a", "-p", str(pid), "-iTCP"], capture_output=True, text=True).stdout
    return next((line for line in out.splitlines() if any(f":{port}" in line for port in SHARED_POSTGRES_PORTS)), "")


def run_guarded(command: list[str], cwd: Path, env: dict[str, str]) -> str:
    """Run ``command`` to its end and return its output; kill it and stop if it connects to a shared Postgres."""
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.monotonic() + MIGRATE_TIMEOUT_SECONDS
    while process.poll() is None:
        if shared := holds_shared_postgres(process.pid):
            process.kill()
            raise SystemExit(f"killed: the migration connected to a shared Postgres: {shared}")
        if time.monotonic() > deadline:
            process.kill()
            raise SystemExit(f"the migration did not finish in {MIGRATE_TIMEOUT_SECONDS}s")
        time.sleep(0.2)
    output = process.stdout.read().strip()
    if process.returncode != 0:
        raise SystemExit("the migration failed:\n" + output[-2000:])
    return output


def wait_healthy(port: int, process: subprocess.Popen) -> None:
    for _ in range(HEALTH_WAIT_SECONDS * 2):
        if process.poll() is not None:
            raise SystemExit(f"Plato exited with {process.returncode} before serving; see its log")  # health is not asked: a dev-daily set with no Knowledge Hub or provider key answers 503 there by design
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/info", timeout=2):
                return
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"Plato not healthy after {HEALTH_WAIT_SECONDS}s")


def check(base: str, mount: str) -> int:
    """Open each page through the proxy; every root-absolute link must carry the mount and every page must load."""
    problems = 0
    for path in CHECK_PATHS:
        url = base + mount + path
        try:
            with urllib.request.urlopen(url, timeout=CHECK_TIMEOUT_SECONDS) as response:
                page = response.read().decode("utf-8", "replace")
                status = response.status
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path}: {exc}")
            problems += 1
            continue
        bare = sorted({m for m in re.findall(r"""\b(?:href|src|action)=["'](/[^"']*)["']""", page)
                       if not m.startswith(("//", mount + "/")) and m != mount})
        print(f"{'FAIL' if bare else 'ok  '} {path} [{status}]" + (f" unmounted links: {bare}" if bare else ""))
        problems += bool(bare)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tree", default=DEFAULT_TREE, help="the checkout to run Plato from")
    parser.add_argument("--python", default=sys.executable, help="the interpreter with Plato's dependencies")
    parser.add_argument("--mount", default=DEFAULT_MOUNT)
    parser.add_argument("--tenants", default=DEFAULT_TENANTS, help="PLATO_TENANTS (comma separated)")
    parser.add_argument("--environment", default=DEFAULT_ENVIRONMENT, help="JAPES_ENVIRONMENT: dev-daily refuses writes without an auth dependency, local admits them")
    parser.add_argument("--extra-pythonpath", default="", help="a directory searched before the checkout (a sitecustomize that instruments a run, kept outside the tree)")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="an extra variable for Plato (for example KNOWLEDGE_HUB_URL=http://127.0.0.1:9 so a strict posture builds its app with no hub to reach)")
    parser.add_argument("--port", type=int, default=0, help="the proxy's port (default: a free one)")
    parser.add_argument("--check", action="store_true", help="fetch the pages through the proxy and exit")
    parser.add_argument("--keep", action="store_true", help="keep the temporary directory")
    args = parser.parse_args()

    tree = Path(args.tree).resolve()
    scratch = Path(tempfile.mkdtemp(prefix="plato-gateway-"))
    plato_port, proxy_port = free_port(), args.port or free_port()
    env = plato_env(tree, scratch, plato_port, args.tenants, args.environment, args.extra_pythonpath, tuple(args.env))
    log = scratch / "plato.log"
    process = None
    try:
        # The working directory is the temporary one, not the checkout: a checkout's `.env` is read from the working
        # directory by the settings layer and can name a shared database. The code comes from PYTHONPATH.
        print(run_guarded([args.python, "-c", MIGRATE], scratch, env))
        with log.open("w") as sink:
            process = subprocess.Popen([args.python, "-m", "plato"], cwd=scratch, env=env, stdout=sink,
                                       stderr=subprocess.STDOUT)
            wait_healthy(plato_port, process)
            if shared := holds_shared_postgres(process.pid):
                raise SystemExit(f"refusing to continue: this Plato holds a connection to a shared Postgres: {shared}")
            Gateway.mount, Gateway.upstream_port = args.mount, plato_port
            server = http.server.ThreadingHTTPServer(("127.0.0.1", proxy_port), Gateway)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://localhost:{proxy_port}"
            print(f"Plato ({args.environment} posture, PLATO_TENANTS={args.tenants}, throwaway database) behind the gateway:")
            print(f"  open {base}{args.mount}/")
            print(f"  Plato's own log: {log}")
            if args.check:
                return 1 if check(base, args.mount) else 0
            print("Ctrl-C to stop; the temporary directory is removed.")
            try:
                while process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            server.shutdown()
            return 0
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
        if args.keep:
            print(f"kept {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

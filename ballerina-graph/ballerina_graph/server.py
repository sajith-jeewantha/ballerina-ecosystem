"""Local server for the viewer with title editing that writes back to the node YAML files."""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml
from pydantic import ValidationError

from .loader import load_graph
from .models import Node
from .viewer import render_viewer

TITLE_LINE = re.compile(r"^title:.*$", re.M)
TITLE_API = re.compile(r"^/api/nodes/([a-z0-9_.]+)/title$")
MAX_BODY = 4096


def yaml_scalar(value: str) -> str:
    """Plain scalar when YAML reads it back unchanged, otherwise a double-quoted one."""
    try:
        if yaml.safe_load(f"k: {value}") == {"k": value}:
            return value
    except yaml.YAMLError:
        pass
    return json.dumps(value, ensure_ascii=False)


def set_title(path: Path, title: str) -> Node:
    """Rewrite only the title: line of a node file, keeping the rest of the file as written."""
    text = path.read_text(encoding="utf-8")
    line = "title: " + yaml_scalar(title)
    new_text, n = TITLE_LINE.subn(lambda _: line, text, count=1)
    if n != 1:
        raise ValueError(f"{path.name} has no top-level title line")
    node = Node.model_validate(yaml.safe_load(new_text))
    if node.title != title:
        raise ValueError("title did not round-trip through YAML")
    path.write_text(new_text, encoding="utf-8")
    return node


def make_handler(nodes_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: str, ctype: str = "application/json") -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _error(self, status: int, msg: str) -> None:
            self._send(status, json.dumps({"error": msg}))

        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?")[0] not in ("/", "/index.html", "/viewer.html"):
                return self._error(404, "not found")
            try:
                graph = load_graph(nodes_dir)
            except Exception as exc:  # noqa: BLE001
                return self._send(500, f"Could not load {nodes_dir}: {exc}", "text/plain")
            self._send(200, render_viewer(graph, editable=True), "text/html")

        def do_POST(self) -> None:  # noqa: N802
            m = TITLE_API.match(self.path)
            if not m:
                return self._error(404, "not found")
            # A JSON content type forces a CORS preflight, which this server never answers,
            # so other websites cannot post here from the browser.
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._error(415, "expected application/json")
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                return self._error(400, "bad request body")
            try:
                title = json.loads(self.rfile.read(length))["title"]
            except (ValueError, KeyError, TypeError):
                return self._error(400, "body must be {\"title\": \"...\"}")
            if not isinstance(title, str) or not title.strip() or "\n" in title or "\r" in title:
                return self._error(400, "title must be one non-empty line")
            path = nodes_dir / f"{m.group(1)}.yaml"
            if not path.is_file():
                return self._error(404, f"no node file {path.name}")
            try:
                node = set_title(path, title.strip())
            except (ValueError, ValidationError, yaml.YAMLError) as exc:
                return self._error(400, str(exc))
            print(f"updated {path.name}: title = {node.title!r}", flush=True)
            self._send(200, json.dumps({"id": node.id, "title": node.title}))

        def log_request(self, code="-", size="-") -> None:  # keep the console to edits and errors
            if isinstance(code, int) and code >= 400:
                super().log_request(code, size)

    return Handler


def serve(nodes_dir: str | Path, host: str = "127.0.0.1", port: int = 8000) -> None:
    nodes = Path(nodes_dir).resolve()
    load_graph(nodes)  # fail fast if the graph does not validate
    try:
        httpd = HTTPServer((host, port), make_handler(nodes))
    except OSError as exc:
        raise SystemExit(f"cannot listen on {host}:{port} ({exc.strerror}); try another --port")
    print(f"serving {nodes} at http://{host}:{port}/ - press Ctrl+C to stop", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

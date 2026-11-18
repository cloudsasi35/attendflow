"""Private webhook receiver for Alertmanager.

Alertmanager POSTs a JSON body with an `alerts` list to /critical or /warning.
Each alert is printed as one JSON line to stdout (read with `docker logs`).
The last 50 alerts are kept in memory and returned by GET /alerts so that
delivery can be checked without reading logs. This container is not published
to the host; it is reachable only on observability-net.
"""

import json
import sys
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RECENT = deque(maxlen=50)
ROUTES = {"/critical", "/warning"}


def log(message: dict) -> None:
    print(json.dumps(message), flush=True)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, body) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/alerts":
            self._send_json(200, list(RECENT))
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path not in ROUTES:
            self._send_json(404, {"error": "unknown route"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        route = self.path.lstrip("/")
        received_at = datetime.now(timezone.utc).isoformat()
        alerts = body.get("alerts", [])
        for alert in alerts:
            entry = {
                "received_at": received_at,
                "route": route,
                "status": alert.get("status"),
                "alertname": alert.get("labels", {}).get("alertname"),
                "severity": alert.get("labels", {}).get("severity"),
                "instance": alert.get("labels", {}).get("instance"),
                "summary": alert.get("annotations", {}).get("summary"),
                "startsAt": alert.get("startsAt"),
            }
            RECENT.append(entry)
            log(entry)
        self._send_json(200, {"received": len(alerts)})

    def log_message(self, fmt: str, *args) -> None:
        # Suppress the default access log; the alert lines above are the output.
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    log({"message": "alert sink listening", "port": 8080, "python": sys.version.split()[0]})
    server.serve_forever()

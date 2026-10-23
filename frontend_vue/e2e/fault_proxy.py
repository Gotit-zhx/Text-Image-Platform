"""Loopback-only fault proxy for manual/CUA acceptance; never imported by the app.

Control JSON: {"rules": [{"method": "POST", "path": "/api/media",
"mode": "error", "remaining": 1}]}. Rules are consumed atomically on match.
Modes: error (500), disconnect (no upstream write), hold (timeout without write),
delay_after (forward/commit, then delay response). No headers/bodies are logged.
"""
import argparse
import http.client
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8126)
    parser.add_argument('--upstream-port', type=int, default=8125)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--events', type=Path, required=True)
    args = parser.parse_args()
    lock = threading.Lock()
    hop_headers = {'connection', 'transfer-encoding', 'keep-alive', 'proxy-connection'}

    def take_rule(method, path):
        with lock:
            data = json.loads(args.control.read_text()) if args.control.exists() else {}
            for rule in data.get('rules', []):
                if rule['method'] == method and rule['path'] == path and rule.get('remaining', 1) > 0:
                    rule['remaining'] = rule.get('remaining', 1) - 1
                    args.control.write_text(json.dumps(data))
                    return dict(rule)
        return None

    def event(method, path, mode, status=None):
        with lock:
            with args.events.open('a') as stream:
                stream.write(json.dumps({'method': method, 'path': path, 'mode': mode,
                                         'upstreamStatus': status, 'time': time.time()}) + '\n')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def handle_request(self):
            path = urlsplit(self.path).path
            rule = take_rule(self.command, path)
            mode = rule['mode'] if rule else 'pass'
            body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            if mode in {'error', 'disconnect', 'hold'}:
                event(self.command, path, mode)
                if mode == 'disconnect':
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if mode == 'hold':
                    time.sleep(min(rule.get('delay_ms', 17000), 35000) / 1000)
                payload = json.dumps({'code': 500, 'message': '验收模拟服务错误，输入应保留'}).encode()
                try:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            connection = http.client.HTTPConnection('127.0.0.1', args.upstream_port, timeout=40)
            try:
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in hop_headers | {'host'}}
                connection.request(self.command, self.path, body=body, headers=headers)
                response = connection.getresponse()
                payload = response.read()
                if mode == 'delay_after':
                    event(self.command, path, mode, response.status)
                    time.sleep(min(rule.get('delay_ms', 17000), 35000) / 1000)
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in hop_headers | {'content-length'}:
                        self.send_header(key, value)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                connection.close()

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = handle_request

    args.control.parent.mkdir(parents=True, exist_ok=True)
    args.events.parent.mkdir(parents=True, exist_ok=True)
    print(f'Fault proxy 127.0.0.1:{args.port} -> 127.0.0.1:{args.upstream_port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()

"""Offline protocol smoke check: never calls database tools or reads .mysql_conf."""
import json
import selectors
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent
process = subprocess.Popen(
    [sys.executable, '-B', str(root / 'server.py')], cwd=root,
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)


def send(message):
    process.stdin.write(json.dumps(message).encode() + b'\n')
    process.stdin.flush()


def receive(request_id):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if not selector.select(max(0, deadline - time.monotonic())):
            break
        line = process.stdout.readline()
        if not line:
            raise RuntimeError('MCP exited before responding')
        message = json.loads(line)
        if message.get('id') == request_id:
            if 'error' in message:
                raise RuntimeError('MCP returned a protocol error')
            return message['result']
    raise RuntimeError('MCP response timeout')


try:
    send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
        'protocolVersion': '2024-11-05', 'capabilities': {},
        'clientInfo': {'name': 'offline-handshake-check', 'version': '1.0'},
    }})
    receive(1)
    send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    result = receive(2)
    names = {tool['name'] for tool in result['tools']}
    if names != {'list_tables', 'describe_table', 'query_readonly'}:
        raise RuntimeError('Unexpected tool list')
    process.stdin.close()
    if process.wait(timeout=10) != 0:
        raise RuntimeError('Nonzero exit on stdin EOF')
    if process.stderr.read():
        raise RuntimeError('Unexpected stderr output')
    print('PASS: initialize, three tools, clean stdin EOF exit; no database calls.')
finally:
    selector.close()
    if process.poll() is None:
        process.kill()
        process.wait(timeout=5)
    for stream in (process.stdin, process.stdout, process.stderr):
        if not stream.closed:
            stream.close()

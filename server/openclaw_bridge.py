"""
OpenClaw Bridge — Host-side HTTP proxy for Docker container access
Listens on port 18800, forwards messages to OpenClaw Gateway via CLI
Uses: openclaw agent --session-id <id> --message <text> --json

Endpoints:
  POST /chat     — Send message to agent
  GET  /status   — Gateway status
  GET  /history  — Session conversation history (for web/telegram sync)
"""
import subprocess
import json
import os
import glob
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SESSION_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")


def _parse_user_text(raw_text: str) -> str:
    """Extract the actual user message from OpenClaw user turn (strips Telegram metadata)"""
    # User messages from Telegram look like:
    # Conversation info (untrusted metadata):
    # ```json
    # {"message_id":"...","sender":"..."}
    # ```
    # 
    # Actual message here
    # 
    # Try to extract after the metadata block
    lines = raw_text.split("\n")
    in_meta = False
    msg_lines = []
    skip_until_end = False
    for line in lines:
        if "Conversation info (untrusted metadata)" in line:
            skip_until_end = True
            continue
        if skip_until_end:
            if line.strip().startswith("```") and in_meta:
                skip_until_end = False
                in_meta = False
                continue
            if line.strip().startswith("```"):
                in_meta = True
            continue
        msg_lines.append(line)
    
    result = "\n".join(msg_lines).strip()
    return result if result else raw_text.strip()


def _parse_assistant_text(raw_text: str) -> str:
    """Clean up assistant response (remove [[reply_to_current]] etc.)"""
    text = raw_text.strip()
    text = re.sub(r'\[\[reply_to_current\]\]\s*', '', text)
    text = re.sub(r'\[\[reply_to_\d+\]\]\s*', '', text)
    return text.strip()


def get_session_history(session_id: str = "agent:main:main", after_ts: str = None, limit: int = 50):
    """Read session JSONL files and return user/assistant message pairs"""
    # Find all session JSONL files (telegram session + web sessions that share this session)
    all_files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl")))
    
    messages = []
    
    for filepath in all_files:
        fname = os.path.basename(filepath)
        # Determine source (telegram vs web)
        if fname.startswith("web-"):
            source = "web"
        else:
            source = "telegram"
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except:
                    continue
                
                if obj.get("type") != "message":
                    continue
                
                msg_data = obj.get("message", {})
                role = msg_data.get("role") if msg_data else obj.get("role")
                if not role:
                    # Older format might have role at top level
                    role = obj.get("role", "")
                
                if role not in ("user", "assistant"):
                    continue
                
                ts = obj.get("timestamp", "")
                
                # Filter by after_ts if provided
                if after_ts and ts <= after_ts:
                    continue
                
                # Extract content text
                content = msg_data.get("content", "") if msg_data else obj.get("content", "")
                if isinstance(content, list):
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            texts.append(item.get("text", ""))
                    raw_text = "\n".join(texts)
                elif isinstance(content, str):
                    raw_text = content
                else:
                    continue
                
                if not raw_text.strip():
                    continue
                
                # Parse and clean text
                if role == "user":
                    text = _parse_user_text(raw_text)
                else:
                    text = _parse_assistant_text(raw_text)
                
                if not text:
                    continue
                
                messages.append({
                    "role": role,
                    "text": text,
                    "timestamp": ts,
                    "source": source,
                })
    
    # Sort by timestamp
    messages.sort(key=lambda m: m.get("timestamp", ""))
    
    # Limit
    if limit and len(messages) > limit:
        messages = messages[-limit:]
    
    return messages


class OpenClawBridge(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/chat':
            content_len = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_len)) if content_len else {}
            message = body.get('message', '')
            session_id = body.get('session_id', 'web-main')

            try:
                result = subprocess.run(
                    ['openclaw', 'agent',
                     '--session-id', session_id,
                     '--message', message,
                     '--json',
                     '--timeout', '80'],
                    capture_output=True, text=True, timeout=90,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    payloads = data.get('result', {}).get('payloads', [])
                    response_text = payloads[0]['text'] if payloads else '(응답 없음)'
                    meta = data.get('result', {}).get('meta', {}).get('agentMeta', {})
                    self._respond(200, {
                        'response': response_text,
                        'source': 'openclaw',
                        'session_id': meta.get('sessionId', session_id),
                        'model': meta.get('model', ''),
                    })
                else:
                    self._respond(502, {
                        'error': result.stderr.strip()[:500],
                        'stdout': result.stdout.strip()[:500],
                        'source': 'error',
                    })
            except subprocess.TimeoutExpired:
                self._respond(504, {'error': 'timeout (90s)', 'source': 'timeout'})
            except FileNotFoundError:
                self._respond(503, {'error': 'openclaw CLI not found', 'source': 'not_installed'})
            except json.JSONDecodeError as e:
                self._respond(502, {
                    'error': f'JSON parse error: {str(e)[:100]}',
                    'raw': result.stdout[:500] if 'result' in dir() else '',
                    'source': 'parse_error',
                })
            except Exception as e:
                self._respond(500, {'error': str(e)[:300], 'source': 'error'})
        elif self.path == '/status':
            self.do_GET()
        else:
            self._respond(404, {'error': 'not found'})

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/status':
            try:
                result = subprocess.run(
                    ['openclaw', 'gateway', 'status'],
                    capture_output=True, text=True, timeout=10,
                )
                self._respond(200, {
                    'status': 'online' if result.returncode == 0 else 'offline',
                    'output': result.stdout.strip()[:500],
                })
            except FileNotFoundError:
                self._respond(200, {'status': 'not_installed'})
            except Exception as e:
                self._respond(200, {'status': 'error', 'error': str(e)[:200]})
        
        elif parsed.path == '/history':
            params = parse_qs(parsed.query)
            after_ts = params.get('after', [None])[0]
            limit = int(params.get('limit', ['50'])[0])
            
            try:
                messages = get_session_history(after_ts=after_ts, limit=limit)
                self._respond(200, {
                    'messages': messages,
                    'count': len(messages),
                })
            except Exception as e:
                self._respond(500, {'error': str(e)[:300]})
        
        else:
            self._respond(404, {'error': 'not found'})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        print(f"[Bridge] {args[0]}")


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 18800), OpenClawBridge)
    print("OpenClaw Bridge running on :18800")
    server.serve_forever()

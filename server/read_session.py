import json, os

session_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
# Read the main Telegram session
f = os.path.join(session_dir, "b5c4d9e1-a2d7-4aeb-9dc6-b884f86971fb.jsonl")
with open(f) as fp:
    lines = fp.readlines()

print(f"Total lines: {len(lines)}")
print()
for i, line in enumerate(lines):
    obj = json.loads(line)
    t = obj.get("type", "?")
    ts = obj.get("timestamp", "")
    # For message types, show content
    if t == "message":
        role = obj.get("message", {}).get("role", "?")
        content = obj.get("message", {}).get("content", "")
        if isinstance(content, str):
            txt = content[:150]
        elif isinstance(content, list):
            texts = [x.get("text", "")[:100] for x in content if isinstance(x, dict) and x.get("type") == "text"]
            txt = " | ".join(texts)[:150]
        else:
            txt = str(content)[:150]
        print(f"Line {i}: type={t} role={role} ts={ts}")
        print(f"  text: {txt}")
    elif t in ("summary", "result"):
        text = obj.get("text", obj.get("summary", ""))
        print(f"Line {i}: type={t} ts={ts}")
        print(f"  text: {str(text)[:150]}")
    else:
        print(f"Line {i}: type={t} ts={ts} keys={list(obj.keys())[:6]}")
    print()

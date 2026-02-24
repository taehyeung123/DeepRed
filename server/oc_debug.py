#!/usr/bin/env python3
import json, os, subprocess

config_path = os.path.expanduser("~/.openclaw/openclaw.json")
with open(config_path) as f:
    config = json.load(f)

# Channels
print("CHANNELS:")
ch = config.get("channels", {})
print(json.dumps(ch, indent=2, ensure_ascii=False))

# Agents (just dump raw)
print("\nAGENTS:")
ag = config.get("agents", [])
print(json.dumps(ag, indent=2, ensure_ascii=False))

# Help output
print("\nHELP:")
r = subprocess.run(["openclaw", "message", "send", "--help"],
                    capture_output=True, text=True, timeout=10)
print(r.stdout)
print(r.stderr)

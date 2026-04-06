import subprocess

# Test what happens with invalid regex pattern
cmd = ["rg", "-n", "[invalid", "."]
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(f"returncode: {result.returncode}")
    print(f"stdout: {result.stdout[:100]}")
    print(f"stderr: {result.stderr[:100]}")
except FileNotFoundError:
    print("rg not installed")
except Exception as e:
    print(f"Exception: {e}")
# mcp-pyrunner

MCP server for executing Python scripts from Claude Desktop.

Automatically detects the nearest virtual environment by walking up the directory tree — no manual activation needed.

## Tools

| Tool | Description |
|---|---|
| `run_script` | Runs a `.py` file by path |
| `run_code` | Runs an inline Python snippet |

Both tools support:
- **venv auto-detection** — walks up to 8 levels from the script's directory looking for `venv/` or `.venv/`
- **venv override** — explicit `venv_path` parameter when the venv is in a non-standard location
- **timeout** — configurable execution limit (default: 30s)
- **args** — pass command-line arguments to scripts

## Installation

```bash
git clone https://github.com/your-username/mcp-pyrunner
cd mcp-pyrunner
pip install -r requirements.txt
```

## Claude Desktop configuration

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "python-runner": {
      "command": "python",
      "args": ["C:\\Users\\panta\\mcp-pyrunner\\server.py"]
    }
  }
}
```

## Venv resolution order

```
1. venv_path parameter (explicit override)
2. script_dir/venv/Scripts/python.exe
3. script_dir/.venv/Scripts/python.exe
4. parent_dir/venv/Scripts/python.exe  (walks up to 8 levels)
5. sys.executable (Python running the MCP server itself)
```

## Usage examples

**Run a script (venv auto-detected):**
```
run_script("C:\\Users\\panta\\rotman\\main.py")
```

**Run a script with args:**
```
run_script("C:\\Users\\panta\\conduler\\watch.py", args=["--dry-run"])
```

**Run inline code in a project context:**
```
run_code("import pandas as pd; print(pd.__version__)", working_dir="C:\\Users\\panta\\myproject")
```

**Force a specific venv:**
```
run_script("C:\\Users\\panta\\script.py", venv_path="C:\\Users\\panta\\shared-venv")
```

## Requirements

- Python 3.10+
- Windows (uses `Scripts/python.exe` path convention)

"""
mcp-pyrunner — MCP server for executing Python scripts from Claude Desktop.

Tools:
  run_script  — runs a .py file, auto-detecting the nearest venv
  run_code    — runs an inline Python snippet in a temp file
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-pyrunner")

# ── venv resolution ───────────────────────────────────────────────────────────

def find_venv_python(start_path: Path, override: str | None = None) -> str:
    """
    Return the Python executable to use for a given script path.

    Priority:
      1. override (explicit venv_path from caller)
      2. auto-detect: walk up from start_path looking for venv/Scripts/python.exe
      3. fallback: sys.executable (Python running this server)
    """
    if override:
        candidate = Path(override) / "Scripts" / "python.exe"
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"No Python found at venv_path: {override}")

    current = start_path if start_path.is_dir() else start_path.parent
    for _ in range(8):
        for venv_name in ("venv", ".venv"):
            candidate = current / venv_name / "Scripts" / "python.exe"
            if candidate.exists():
                return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent

    return sys.executable


# ── subprocess runner ─────────────────────────────────────────────────────────

def run(python: str, args: list[str], cwd: str | None = None, timeout: int = 30) -> dict:
    try:
        result = subprocess.run(
            [python] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Timeout: script exceeded {timeout}s limit.", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


def format_output(result: dict, python_used: str) -> str:
    lines = [f"Python: {python_used}", f"Exit code: {result['exit_code']}"]
    if result["stdout"]:
        lines += ["", "── stdout ──", result["stdout"].rstrip()]
    if result["stderr"]:
        lines += ["", "── stderr ──", result["stderr"].rstrip()]
    if not result["stdout"] and not result["stderr"]:
        lines.append("(no output)")
    return "\n".join(lines)


# ── tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def run_script(
    script_path: str,
    args: list[str] = [],
    venv_path: str = "",
    timeout: int = 30,
) -> str:
    """
    Run a Python script file. Auto-detects the nearest venv by walking up
    the directory tree. Accepts optional script arguments, a venv override
    path, and a timeout.

    Args:
        script_path: Absolute path to the .py script to run.
        args: Optional list of arguments to pass to the script.
        venv_path: Optional absolute path to a venv folder. If omitted, the nearest venv is auto-detected.
        timeout: Max execution time in seconds (default: 30).
    """
    path = Path(script_path)
    if not path.exists():
        return f"Error: file not found — {path}"

    python = find_venv_python(path, venv_path or None)
    result = run(python, [str(path)] + args, cwd=str(path.parent), timeout=timeout)
    return format_output(result, python)


@mcp.tool()
def run_code(
    code: str,
    working_dir: str = "",
    venv_path: str = "",
    timeout: int = 30,
) -> str:
    """
    Run an inline Python code snippet. Writes the snippet to a temp file
    and executes it. Accepts an optional working directory for venv
    auto-detection.

    Args:
        code: Python source code to execute.
        working_dir: Optional directory to use as cwd and for venv auto-detection. Defaults to user home.
        venv_path: Optional explicit venv folder path.
        timeout: Max execution time in seconds (default: 30).
    """
    cwd = working_dir or str(Path.home())
    python = find_venv_python(Path(cwd), venv_path or None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = run(python, [tmp_path], cwd=cwd, timeout=timeout)
    finally:
        os.unlink(tmp_path)

    return format_output(result, python)


# ── entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")

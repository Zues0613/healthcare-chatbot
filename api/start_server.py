import os
import subprocess
import sys
from pathlib import Path


def _venv_python(api_dir: Path) -> Path:
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    python_exe = "python.exe" if os.name == "nt" else "python"
    return api_dir / ".venv" / scripts_dir / python_exe


def main() -> None:
    api_dir = Path(__file__).resolve().parent
    project_root = api_dir.parent
    venv_python = _venv_python(api_dir)

    if not venv_python.exists():
        print("Virtual environment not found. Please create it at api/.venv before running the server.")
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault("UVICORN_HOST", "0.0.0.0")
    env.setdefault("UVICORN_PORT", "8000")

    command = [
        str(venv_python),
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        env["UVICORN_HOST"],
        "--port",
        env["UVICORN_PORT"],
        "--reload",
    ]

    existing_path = env.get("PYTHONPATH")
    if existing_path:
        env["PYTHONPATH"] = os.pathsep.join([existing_path, str(project_root)])
    else:
        env["PYTHONPATH"] = str(project_root)

    subprocess.run(command, cwd=str(project_root), env=env, check=True)


if __name__ == "__main__":
    main()


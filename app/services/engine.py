from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


class EngineError(Exception):
    pass


def run_engine(request_id: str, content: list[str]) -> dict:
    payload = {
        "id": request_id,
        "content": content,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / "input.json"
        output_base = tmp / "output"

        input_path.write_text(json.dumps(payload), encoding="utf-8")

        result = subprocess.run(
            [
                "engine",
                "compute",
                "--input",
                str(input_path),
                "--output",
                str(output_base),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise EngineError(
                f"Engine failed with code {result.returncode}: {result.stderr.strip()}"
            )

        output_json = Path(f"{output_base}.json")
        if not output_json.exists():
            raise EngineError("Engine did not produce output JSON")

        return json.loads(output_json.read_text(encoding="utf-8"))
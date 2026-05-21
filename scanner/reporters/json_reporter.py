from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from scanner.models import AddressRiskReport


class JsonReporter:
    def __init__(self, console: Console):
        self.console = console

    def render(self, report: AddressRiskReport, output: str | None = None) -> None:
        data = report.model_dump()

        if output:
            filepath = Path(output)
            filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.console.print(f"[green]JSON report saved to: {filepath}[/green]")
        else:
            self.console.print_json(json.dumps(data, ensure_ascii=False))

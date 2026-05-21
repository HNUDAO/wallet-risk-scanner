from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scanner.models import AddressRiskReport, RiskLevel
from scanner.utils.address import shorten_address
from scanner.utils.constants import RISK_COLORS


class ConsoleReporter:
    def __init__(self, console: Console):
        self.console = console

    def render(self, report: AddressRiskReport) -> None:
        self._render_header(report)
        self._render_score(report)
        self._render_blacklist(report)
        self._render_contracts(report)
        self._render_fund_sources(report)
        self._render_recommendation(report)

    def _render_header(self, report: AddressRiskReport) -> None:
        header = Text()
        header.append("Wallet Risk Scanner\n\n", style="bold")
        header.append(f"Address: ", style="bold")
        header.append(f"{report.address}\n")
        header.append(f"Chain:   ", style="bold")
        header.append(f"{report.chain} ({report.chain_id})\n")
        self.console.print(Panel(header, border_style="blue"))

    def _render_score(self, report: AddressRiskReport) -> None:
        if report.risk_score is None:
            return

        score = report.risk_score.score
        level = report.risk_score.level
        color = RISK_COLORS.get(level.value, "white")

        bar_len = 40
        filled = int(bar_len * score / 100)
        bar = "█" * filled + "░" * (bar_len - filled)

        score_text = Text()
        score_text.append(f"  RISK SCORE: {score} / 100\n", style=f"bold {color}")
        score_text.append(f"  {bar}  ", style=color)
        score_text.append(f"{level.value}\n", style=f"bold {color}")
        score_text.append(f"\n  Breakdown: {report.risk_score.breakdown}\n", style="dim")

        self.console.print(Panel(score_text, border_style=color))

    def _render_blacklist(self, report: AddressRiskReport) -> None:
        if not report.blacklist_hits:
            self.console.print("[green]✓ No blacklist hits found.[/green]\n")
            return

        table = Table(title=f"⚠ Blacklist Hits ({len(report.blacklist_hits)})", show_lines=True)
        table.add_column("Source", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Risk Level", style="white")
        table.add_column("Description", style="dim")

        for hit in report.blacklist_hits:
            color = RISK_COLORS.get(hit.risk_level.value, "white")
            table.add_row(
                hit.source,
                hit.hit_type,
                f"[{color}]{hit.risk_level.value}[/{color}]",
                hit.description,
            )

        self.console.print(table)
        self.console.print()

    def _render_contracts(self, report: AddressRiskReport) -> None:
        if not report.contract_risks:
            self.console.print("[green]✓ No high-risk contract interactions found.[/green]\n")
            return

        table = Table(title=f"⚠ High-Risk Contracts ({len(report.contract_risks)})", show_lines=True)
        table.add_column("Contract", style="cyan")
        table.add_column("Risk Type", style="white")
        table.add_column("Risk Level", style="white")
        table.add_column("Source", style="dim")
        table.add_column("Detail", style="dim")

        for risk in report.contract_risks:
            color = RISK_COLORS.get(risk.risk_level.value, "white")
            table.add_row(
                shorten_address(risk.address),
                risk.risk_type,
                f"[{color}]{risk.risk_level.value}[/{color}]",
                risk.source,
                risk.detail,
            )

        self.console.print(table)
        self.console.print()

    def _render_fund_sources(self, report: AddressRiskReport) -> None:
        if not report.fund_source_risks:
            self.console.print("[green]✓ No risky fund sources detected.[/green]\n")
            return

        table = Table(title=f"⚠ Fund Source Risks ({len(report.fund_source_risks)})", show_lines=True)
        table.add_column("Source Address", style="cyan")
        table.add_column("Risk Type", style="white")
        table.add_column("Risk Level", style="white")
        table.add_column("Amount", style="white")
        table.add_column("Tx Hash", style="dim")

        for risk in report.fund_source_risks:
            color = RISK_COLORS.get(risk.risk_level.value, "white")
            tx_short = shorten_address(risk.tx_hash, 8) if risk.tx_hash else "N/A"
            table.add_row(
                shorten_address(risk.source_address),
                risk.risk_type,
                f"[{color}]{risk.risk_level.value}[/{color}]",
                risk.amount,
                tx_short,
            )

        self.console.print(table)
        self.console.print()

    def _render_recommendation(self, report: AddressRiskReport) -> None:
        if report.risk_score is None:
            return

        score = report.risk_score.score
        level = report.risk_score.level
        color = RISK_COLORS.get(level.value, "white")

        if level == RiskLevel.LOW:
            msg = "This address appears to be LOW RISK. No significant threats detected."
        elif level == RiskLevel.MEDIUM:
            msg = "This address shows MEDIUM RISK. Exercise caution when interacting."
        elif level == RiskLevel.HIGH:
            msg = "This address shows HIGH RISK. Avoid transacting with this address."
        else:
            msg = "This address shows CRITICAL RISK. Strongly advised to avoid any interaction."

        self.console.print(Panel(
            f"[bold]💡 Recommendation:[/bold] {msg}",
            border_style=color,
        ))

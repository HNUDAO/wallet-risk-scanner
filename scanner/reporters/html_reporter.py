from __future__ import annotations

from pathlib import Path

from rich.console import Console

from scanner.models import AddressRiskReport, RiskLevel
from scanner.utils.address import shorten_address
from scanner.utils.constants import RISK_COLORS


class HtmlReporter:
    def __init__(self, console: Console):
        self.console = console

    def render(self, report: AddressRiskReport, output: str | None = None) -> None:
        html = self._generate_html(report)

        if output:
            filepath = Path(output)
            filepath.write_text(html, encoding="utf-8")
            self.console.print(f"[green]HTML report saved to: {filepath}[/green]")
        else:
            filepath = Path("wallet_risk_report.html")
            filepath.write_text(html, encoding="utf-8")
            self.console.print(f"[green]HTML report saved to: {filepath}[/green]")

    def _generate_html(self, report: AddressRiskReport) -> str:
        score = report.risk_score.score if report.risk_score else 0
        level = report.risk_score.level.value if report.risk_score else "UNKNOWN"
        color = RISK_COLORS.get(level, "gray")

        blacklist_rows = self._blacklist_rows(report)
        contract_rows = self._contract_rows(report)
        fund_rows = self._fund_rows(report)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wallet Risk Scanner Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #0d1117; color: #c9d1d9; }}
  h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 12px; }}
  .score-panel {{ background: #161b22; border: 2px solid {color}; border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0; }}
  .score-value {{ font-size: 48px; font-weight: bold; color: {color}; }}
  .score-bar {{ background: #21262d; border-radius: 8px; height: 24px; margin: 16px 0; overflow: hidden; }}
  .score-fill {{ height: 100%; background: {color}; border-radius: 8px; width: {score}%; transition: width 0.5s; }}
  .score-level {{ font-size: 20px; font-weight: bold; color: {color}; text-transform: uppercase; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  th {{ background: #161b22; color: #58a6ff; padding: 12px; text-align: left; border: 1px solid #30363d; }}
  td {{ padding: 10px 12px; border: 1px solid #30363d; }}
  tr:nth-child(even) {{ background: #161b22; }}
  .section {{ margin: 24px 0; }}
  .section h2 {{ color: #f0883e; }}
  .risk-LOW {{ color: #3fb950; }}
  .risk-MEDIUM {{ color: #d29922; }}
  .risk-HIGH {{ color: #f85149; }}
  .risk-CRITICAL {{ color: #ff4444; font-weight: bold; }}
  .info {{ color: #8b949e; font-size: 14px; }}
  .recommendation {{ background: #161b22; border-left: 4px solid {color}; padding: 16px; margin: 20px 0; border-radius: 4px; }}
</style>
</head>
<body>
  <h1>🔍 Wallet Risk Scanner Report</h1>
  <p class="info">Address: <strong>{report.address}</strong></p>
  <p class="info">Chain: <strong>{report.chain} ({report.chain_id})</strong></p>

  <div class="score-panel">
    <div class="score-value">{score} / 100</div>
    <div class="score-bar"><div class="score-fill"></div></div>
    <div class="score-level">{level} RISK</div>
    <p class="info">{report.risk_score.breakdown if report.risk_score else ''}</p>
  </div>

  <div class="section">
    <h2>⚠️ Blacklist Hits ({len(report.blacklist_hits)})</h2>
    {"<p class='risk-LOW'>✓ No blacklist hits found.</p>" if not report.blacklist_hits else f"""
    <table>
      <tr><th>Source</th><th>Type</th><th>Risk Level</th><th>Description</th></tr>
      {blacklist_rows}
    </table>"""}
  </div>

  <div class="section">
    <h2>⚠️ High-Risk Contracts ({len(report.contract_risks)})</h2>
    {"<p class='risk-LOW'>✓ No high-risk contract interactions found.</p>" if not report.contract_risks else f"""
    <table>
      <tr><th>Contract</th><th>Risk Type</th><th>Risk Level</th><th>Source</th><th>Detail</th></tr>
      {contract_rows}
    </table>"""}
  </div>

  <div class="section">
    <h2>⚠️ Fund Source Risks ({len(report.fund_source_risks)})</h2>
    {"<p class='risk-LOW'>✓ No risky fund sources detected.</p>" if not report.fund_source_risks else f"""
    <table>
      <tr><th>Source Address</th><th>Risk Type</th><th>Risk Level</th><th>Amount</th><th>Tx Hash</th></tr>
      {fund_rows}
    </table>"""}
  </div>

  <div class="recommendation">
    <strong>💡 Recommendation:</strong> {self._get_recommendation(level)}
  </div>
</body>
</html>"""

    def _blacklist_rows(self, report: AddressRiskReport) -> str:
        rows = []
        for hit in report.blacklist_hits:
            rows.append(
                f"<tr><td>{hit.source}</td><td>{hit.hit_type}</td>"
                f"<td class='risk-{hit.risk_level.value}'>{hit.risk_level.value}</td>"
                f"<td>{hit.description}</td></tr>"
            )
        return "".join(rows)

    def _contract_rows(self, report: AddressRiskReport) -> str:
        rows = []
        for risk in report.contract_risks:
            rows.append(
                f"<tr><td>{shorten_address(risk.address)}</td><td>{risk.risk_type}</td>"
                f"<td class='risk-{risk.risk_level.value}'>{risk.risk_level.value}</td>"
                f"<td>{risk.source}</td><td>{risk.detail}</td></tr>"
            )
        return "".join(rows)

    def _fund_rows(self, report: AddressRiskReport) -> str:
        rows = []
        for risk in report.fund_source_risks:
            tx_short = shorten_address(risk.tx_hash, 8) if risk.tx_hash else "N/A"
            rows.append(
                f"<tr><td>{shorten_address(risk.source_address)}</td><td>{risk.risk_type}</td>"
                f"<td class='risk-{risk.risk_level.value}'>{risk.risk_level.value}</td>"
                f"<td>{risk.amount}</td><td>{tx_short}</td></tr>"
            )
        return "".join(rows)

    def _get_recommendation(self, level: str) -> str:
        recommendations = {
            "LOW": "This address appears to be LOW RISK. No significant threats detected.",
            "MEDIUM": "This address shows MEDIUM RISK. Exercise caution when interacting.",
            "HIGH": "This address shows HIGH RISK. Avoid transacting with this address.",
            "CRITICAL": "This address shows CRITICAL RISK. Strongly advised to avoid any interaction.",
        }
        return recommendations.get(level, "Unable to determine risk level.")

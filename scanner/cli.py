import typer
from rich.console import Console
from rich.table import Table

from scanner.config import CHAINS, DEFAULT_CHAIN, ETHERSCAN_API_KEY, BSCSCAN_API_KEY, CHAINABUSE_API_KEY, ETHERSCAN_V2_API_URL
from scanner.utils.address import is_valid_eth_address, normalize_address

app = typer.Typer(
    name="wallet-risk-scanner",
    help="Wallet Risk Scanner - Analyze Ethereum/BSC addresses for risk factors",
)
console = Console()


@app.command()
def scan(
    address: str = typer.Argument(..., help="Wallet address to scan (0x...)"),
    chain: str = typer.Option(DEFAULT_CHAIN, "--chain", "-c", help="Blockchain to scan"),
    format: str = typer.Option("console", "--format", "-f", help="Output format: console, json, html"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path (for json/html)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed API call logs"),
):
    if verbose:
        from scanner.utils.log import enable_verbose
        enable_verbose()

    if not is_valid_eth_address(address):
        console.print(f"[red]Invalid address: {address}[/red]")
        raise typer.Exit(1)

    if chain not in CHAINS:
        console.print(f"[red]Unsupported chain: {chain}. Supported: {', '.join(CHAINS.keys())}[/red]")
        raise typer.Exit(1)

    address = normalize_address(address)
    chain_info = CHAINS[chain]

    console.print(f"[bold]Scanning address:[/bold] {address}")
    console.print(f"[bold]Chain:[/bold] {chain_info['name']} ({chain_info['chain_id']})")
    console.print()

    from scanner.apis.etherscan import EtherscanClient
    from scanner.engines.blacklist import BlacklistEngine
    from scanner.engines.contract_risk import ContractRiskEngine
    from scanner.engines.fund_tracing import FundTracingEngine
    from scanner.engines.risk_scorer import RiskScorer
    from scanner.models import AddressRiskReport

    blacklist_engine = BlacklistEngine()
    shared_etherscan = EtherscanClient(chain)
    contract_engine = ContractRiskEngine(chain, etherscan=shared_etherscan)
    fund_engine = FundTracingEngine(chain, etherscan=shared_etherscan)
    scorer = RiskScorer()

    with console.status("[bold green]Checking blacklists...") as status:
        blacklist_hits = blacklist_engine.check(address)

    with console.status("[bold green]Analyzing contract interactions...") as status:
        contract_risks = contract_engine.check(address)

    with console.status("[bold green]Tracing fund sources...") as status:
        fund_risks = fund_engine.check(address)

    risk_score = scorer.calculate(
        blacklist_hits=blacklist_hits,
        contract_risks=contract_risks,
        fund_source_risks=fund_risks,
    )

    report = AddressRiskReport(
        address=address,
        chain=chain,
        chain_id=chain_info["chain_id"],
        blacklist_hits=blacklist_hits,
        contract_risks=contract_risks,
        fund_source_risks=fund_risks,
        risk_score=risk_score,
    )

    if format == "json":
        from scanner.reporters.json_reporter import JsonReporter
        JsonReporter(console).render(report, output)
    elif format == "html":
        from scanner.reporters.html_reporter import HtmlReporter
        HtmlReporter(console).render(report, output)
    else:
        from scanner.reporters.console import ConsoleReporter
        ConsoleReporter(console).render(report)


@app.command(name="check-api")
def check_api():
    import requests

    console.print("[bold]API Configuration Diagnostic[/bold]\n")

    table = Table(show_lines=True)
    table.add_column("API", style="cyan")
    table.add_column("Key Configured", style="white")
    table.add_column("Key Suffix", style="dim")
    table.add_column("Test Result", style="white")

    goplus_ok = False
    try:
        from goplus.address import Address
        res = Address().address_security(address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", chain_id="1")
        goplus_ok = res.code == 1
    except Exception:
        pass
    table.add_row(
        "GoPlus Security",
        "[green]N/A (no key needed)[/green]",
        "-",
        "[green]OK[/green]" if goplus_ok else "[red]FAILED[/red]",
    )

    etherscan_ok = False
    etherscan_key_status = "NOT SET"
    etherscan_suffix = "-"
    if ETHERSCAN_API_KEY:
        etherscan_key_status = "YES"
        etherscan_suffix = f"***{ETHERSCAN_API_KEY[-4:]}"
        try:
            resp = requests.get(
                ETHERSCAN_V2_API_URL,
                params={
                    "chainid": 1,
                    "module": "account",
                    "action": "txlist",
                    "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                    "page": 1,
                    "offset": 1,
                    "apikey": ETHERSCAN_API_KEY,
                },
                timeout=15,
            )
            data = resp.json()
            etherscan_ok = data.get("status") == "1"
        except Exception:
            pass
    table.add_row(
        "Etherscan V2 (ETH/Polygon/Arbitrum)",
        f"[{'green' if ETHERSCAN_API_KEY else 'red'}]{etherscan_key_status}[/{'green' if ETHERSCAN_API_KEY else 'red'}]",
        etherscan_suffix,
        "[green]OK[/green]" if etherscan_ok else "[red]FAILED[/red]",
    )

    bscscan_ok = False
    bscscan_key_status = "NOT SET"
    bscscan_suffix = "-"
    if BSCSCAN_API_KEY:
        bscscan_key_status = "YES"
        bscscan_suffix = f"***{BSCSCAN_API_KEY[-4:]}"
        try:
            resp = requests.get(
                "https://api.bscscan.com/api",
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                    "page": 1,
                    "offset": 1,
                    "apikey": BSCSCAN_API_KEY,
                },
                timeout=15,
            )
            data = resp.json()
            bscscan_ok = data.get("status") == "1"
        except Exception:
            pass
    table.add_row(
        "BscScan (BSC V1 fallback)",
        f"[{'green' if BSCSCAN_API_KEY else 'yellow'}]{bscscan_key_status}[/{'green' if BSCSCAN_API_KEY else 'yellow'}]",
        bscscan_suffix,
        "[green]OK[/green]" if bscscan_ok else ("[red]FAILED[/red]" if BSCSCAN_API_KEY else "[yellow]NOT SET (BSC scan limited)[/yellow]"),
    )

    chainabuse_ok = False
    chainabuse_key_status = "NOT SET"
    chainabuse_suffix = "-"
    if CHAINABUSE_API_KEY:
        chainabuse_key_status = "YES"
        chainabuse_suffix = f"***{CHAINABUSE_API_KEY[-4:]}"
        try:
            resp = requests.get(
                "https://api.chainabuse.com/v1/reports",
                params={"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"},
                headers={"Authorization": f"Bearer {CHAINABUSE_API_KEY}"},
                timeout=15,
            )
            chainabuse_ok = resp.status_code == 200
        except Exception:
            pass
    table.add_row(
        "ChainAbuse",
        f"[{'green' if CHAINABUSE_API_KEY else 'yellow'}]{chainabuse_key_status}[/{'green' if CHAINABUSE_API_KEY else 'yellow'}]",
        chainabuse_suffix,
        "[green]OK[/green]" if chainabuse_ok else ("[red]FAILED[/red]" if CHAINABUSE_API_KEY else "[yellow]SKIPPED (no key)[/yellow]"),
    )

    scamsniffer_ok = False
    try:
        resp = requests.get(
            "https://raw.githubusercontent.com/scamsniffer/scam-database/main/blacklist/address.json",
            timeout=15,
        )
        scamsniffer_ok = resp.status_code == 200 and len(resp.json()) > 0
    except Exception:
        pass
    table.add_row(
        "ScamSniffer",
        "[green]N/A (auto-fetch)[/green]",
        "-",
        "[green]OK[/green]" if scamsniffer_ok else "[red]FAILED[/red]",
    )

    ofac_ok = False
    try:
        resp = requests.get(
            "https://www.treasury.gov/ofac/downloads/sdn.csv",
            timeout=15,
        )
        ofac_ok = resp.status_code == 200 and len(resp.text) > 0
    except Exception:
        pass
    table.add_row(
        "OFAC SDN",
        "[green]N/A (auto-fetch)[/green]",
        "-",
        "[green]OK[/green]" if ofac_ok else "[red]FAILED[/red]",
    )

    console.print(table)

    console.print("\n[bold]Summary:[/bold]")
    if ETHERSCAN_API_KEY and etherscan_ok:
        console.print("  [green]✓[/green] Etherscan V2 API key works (Ethereum/Polygon/Arbitrum free)")
    elif ETHERSCAN_API_KEY and not etherscan_ok:
        console.print("  [red]✗[/red] Etherscan V2 API key is set but [bold]not working[/bold] - check your key")
    else:
        console.print("  [yellow]![/yellow] Etherscan API key is [bold]not configured[/bold] - contract interaction and fund tracing will not work")

    if BSCSCAN_API_KEY and bscscan_ok:
        console.print("  [green]✓[/green] BscScan API key works (BSC chain supported)")
    elif BSCSCAN_API_KEY and not bscscan_ok:
        console.print("  [red]✗[/red] BscScan API key is set but [bold]not working[/bold] - check your key")
    else:
        console.print("  [yellow]![/yellow] BscScan API key is [bold]not configured[/bold] - BSC chain scanning will be limited (V2 free tier does not support BSC)")

    if CHAINABUSE_API_KEY and chainabuse_ok:
        console.print("  [green]✓[/green] ChainAbuse API key is configured and working")
    elif CHAINABUSE_API_KEY and not chainabuse_ok:
        console.print("  [red]✗[/red] ChainAbuse API key is set but [bold]not working[/bold] - check your key")
    else:
        console.print("  [yellow]![/yellow] ChainAbuse API key is [bold]not configured[/bold] - community reports will be skipped (optional)")


@app.command()
def update_blacklist():
    from scanner.data.blacklist_loader import BlacklistLoader
    loader = BlacklistLoader()
    with console.status("[bold green]Updating blacklists..."):
        loader.update_all()
    console.print("[bold green]Blacklists updated successfully![/bold green]")


@app.command()
def chains():
    console.print("[bold]Supported Chains:[/bold]\n")
    for key, info in CHAINS.items():
        console.print(f"  [cyan]{key}[/cyan] - {info['name']} (Chain ID: {info['chain_id']})")


if __name__ == "__main__":
    app()

#!/usr/bin/env python3
"""
WebexTools CLI - A unified command-line interface for managing Cisco Webex devices and resources.
"""
import os
import sys
from typing import Optional

import rich_click as click
from rich.console import Console
from rich.panel import Panel

from webex_tools import __version__

# Initialize console for rich output
console = Console()

# Configure rich_click settings
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.ERRORS_SUGGESTION = "Try 'webex --help' for help."
click.rich_click.STYLE_OPTION = "green"
click.rich_click.STYLE_ARGUMENT = "blue"
click.rich_click.STYLE_COMMAND = "cyan"

# Create the main CLI group
@click.group(
    help="[bold]WebexTools[/bold] - CLI tool for managing Cisco Webex devices and resources."
)
@click.version_option(version=__version__, prog_name="WebexTools")
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode for verbose output.",
    show_default=True,
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Main CLI entry point for WebexTools."""
    # Initialize context object to share data between commands
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    
    # Load environment variables if .env file exists
    if os.path.exists(".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            if debug:
                console.print("[yellow]Warning: python-dotenv not installed. Environment variables from .env file will not be loaded.[/yellow]")
    
    # Check for API token
    if not os.environ.get("WEBEX_ACCESS_TOKEN"):
        console.print(
            Panel(
                "[bold red]Error: WEBEX_ACCESS_TOKEN environment variable is not set.[/bold red]\n\n"
                "Please set this variable in your environment or in a .env file:\n"
                "  WEBEX_ACCESS_TOKEN=your_token_here",
                title="Authentication Error",
                border_style="red",
            )
        )
        if not ctx.invoked_subcommand or ctx.invoked_subcommand not in ["help", "version"]:
            sys.exit(1)


# Import command groups
from webex_tools.commands.devices import devices_group
# These will be added as we implement them
# from webex_tools.commands import workspaces, users

# Register command groups
cli.add_command(devices_group)


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

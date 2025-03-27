"""
Formatting utilities for CLI output.
"""
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

def format_error(message: str, title: str = "Error") -> Panel:
    """
    Format an error message as a rich panel.
    
    Args:
        message: The error message.
        title: The panel title.
        
    Returns:
        A rich Panel object.
    """
    return Panel(
        f"[bold red]{message}[/bold red]",
        title=title,
        border_style="red"
    )

def format_success(message: str, title: str = "Success") -> Panel:
    """
    Format a success message as a rich panel.
    
    Args:
        message: The success message.
        title: The panel title.
        
    Returns:
        A rich Panel object.
    """
    return Panel(
        f"[bold green]{message}[/bold green]",
        title=title,
        border_style="green"
    )

def format_info(message: str, title: str = "Info") -> Panel:
    """
    Format an info message as a rich panel.
    
    Args:
        message: The info message.
        title: The panel title.
        
    Returns:
        A rich Panel object.
    """
    return Panel(
        f"[bold blue]{message}[/bold blue]",
        title=title,
        border_style="blue"
    )

def format_warning(message: str, title: str = "Warning") -> Panel:
    """
    Format a warning message as a rich panel.
    
    Args:
        message: The warning message.
        title: The panel title.
        
    Returns:
        A rich Panel object.
    """
    return Panel(
        f"[bold yellow]{message}[/bold yellow]",
        title=title,
        border_style="yellow"
    )

def create_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    caption: Optional[str] = None
) -> Table:
    """
    Create a rich table with the given data.
    
    Args:
        title: The table title.
        columns: The column headers.
        rows: The table data as a list of rows.
        caption: Optional table caption.
        
    Returns:
        A rich Table object.
    """
    table = Table(title=title, caption=caption)
    
    # Add columns
    for column in columns:
        table.add_column(column)
    
    # Add rows
    for row in rows:
        # Convert all values to strings
        str_row = [str(cell) for cell in row]
        table.add_row(*str_row)
    
    return table

def format_dict_as_table(
    data: Dict[str, Any],
    title: str = "Data",
    caption: Optional[str] = None
) -> Table:
    """
    Format a dictionary as a two-column table.
    
    Args:
        data: The dictionary to format.
        title: The table title.
        caption: Optional table caption.
        
    Returns:
        A rich Table object.
    """
    table = Table(title=title, caption=caption)
    table.add_column("Key")
    table.add_column("Value")
    
    for key, value in data.items():
        # Handle nested dictionaries and lists
        if isinstance(value, dict):
            value = str(value)
        elif isinstance(value, list):
            value = str(value)
        else:
            value = str(value)
        
        table.add_row(str(key), value)
    
    return table

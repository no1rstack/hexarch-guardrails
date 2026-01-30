"""Output formatting for hexarch-ctl commands."""

import json
from typing import Any, List, Dict, Optional
from io import StringIO
from tabulate import tabulate
from hexarch_cli.output.colors import ColorScheme


class OutputFormatter:
    """Format command output in multiple formats."""
    
    def __init__(self, format: str = "table", colors: bool = True):
        """Initialize formatter.
        
        Args:
            format: Output format (json, table, csv)
            colors: Enable colored output
        """
        self.format = format
        self.colors = colors
    
    def format_output(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data according to selected format.
        
        Args:
            data: Data to format (list of dicts or list of lists)
            headers: Column headers for table format
        
        Returns:
            Formatted output string
        """
        if self.format == "json":
            return self._format_json(data)
        elif self.format == "csv":
            return self._format_csv(data, headers)
        else:  # table (default)
            return self._format_table(data, headers)
    
    def _format_json(self, data: Any) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)
    
    def _format_csv(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format as CSV."""
        if not data:
            return ""
        
        # Handle list of dicts
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if not headers:
                headers = list(data[0].keys())
            
            output = StringIO()
            # Write header
            output.write(",".join(f'"{h}"' for h in headers) + "\n")
            
            # Write rows
            for row in data:
                values = [str(row.get(h, "")) for h in headers]
                output.write(",".join(f'"{v}"' for v in values) + "\n")
            
            return output.getvalue()
        
        # Handle list of lists
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            output = StringIO()
            
            if headers:
                output.write(",".join(f'"{h}"' for h in headers) + "\n")
            
            for row in data:
                values = [str(v) for v in row]
                output.write(",".join(f'"{v}"' for v in values) + "\n")
            
            return output.getvalue()
        
        # Fallback to JSON
        return self._format_json(data)
    
    def _format_table(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format as human-readable table."""
        if not data:
            return "(no results)"
        
        # Handle list of dicts
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if not headers:
                headers = list(data[0].keys())
            
            # Convert dicts to lists
            rows = []
            for item in data:
                row = [item.get(h, "") for h in headers]
                rows.append(row)
            
            table = tabulate(rows, headers=headers, tablefmt="plain")
            
            # Color headers if enabled
            if self.colors:
                lines = table.split("\n")
                if len(lines) >= 2:
                    # Color first line (header)
                    lines[0] = ColorScheme.format(lines[0], ColorScheme.HEADER)
                    # Color separator
                    if len(lines[1].strip()):
                        lines[1] = ColorScheme.muted(lines[1])
                    table = "\n".join(lines)
            
            return table
        
        # Handle list of lists
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            table = tabulate(data, headers=headers, tablefmt="plain")
            
            if self.colors and headers:
                lines = table.split("\n")
                if len(lines) >= 2:
                    lines[0] = ColorScheme.format(lines[0], ColorScheme.HEADER)
                    if len(lines[1].strip()):
                        lines[1] = ColorScheme.muted(lines[1])
                    table = "\n".join(lines)
            
            return table
        
        # Single value
        return str(data)
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        if self.colors:
            print(ColorScheme.success(message))
        else:
            print(f"✓ {message}")
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        if self.colors:
            print(ColorScheme.error(message))
        else:
            print(f"✗ {message}")
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        if self.colors:
            print(ColorScheme.warning(message))
        else:
            print(f"⚠ {message}")
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        if self.colors:
            print(ColorScheme.info(message))
        else:
            print(f"ℹ {message}")
    
    def print_header(self, text: str) -> None:
        """Print section header."""
        if self.colors:
            print(ColorScheme.header(text))
        else:
            print(text)
    
    def print_muted(self, text: str) -> None:
        """Print muted text."""
        if self.colors:
            print(ColorScheme.muted(text))
        else:
            print(text)


__all__ = ["OutputFormatter"]

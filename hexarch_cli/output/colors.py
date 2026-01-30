"""Color scheme for terminal output."""

from enum import Enum


class Color(str, Enum):
    """ANSI color codes."""
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class ColorScheme:
    """Terminal color scheme for hexarch-ctl."""
    
    # Success states
    SUCCESS = Color.BRIGHT_GREEN
    ERROR = Color.BRIGHT_RED
    WARNING = Color.BRIGHT_YELLOW
    INFO = Color.BRIGHT_CYAN
    
    # Data types
    HEADER = Color.BOLD + Color.CYAN
    KEY = Color.BOLD + Color.WHITE
    VALUE = Color.WHITE
    MUTED = Color.BRIGHT_BLACK
    
    # Status indicators
    ACTIVE = Color.BRIGHT_GREEN
    INACTIVE = Color.BRIGHT_RED
    PENDING = Color.BRIGHT_YELLOW
    
    # Command output
    COMMAND = Color.BRIGHT_BLUE
    OUTPUT = Color.WHITE
    
    @staticmethod
    def format(text: str, color) -> str:
        """Apply color to text."""
        if isinstance(color, Color):
            return f"{color.value}{text}{Color.RESET.value}"
        else:
            # Already a string (e.g., concatenated colors)
            return f"{color}{text}{Color.RESET.value}"
    
    @staticmethod
    def success(text: str) -> str:
        """Format as success message."""
        return ColorScheme.format(f"✓ {text}", ColorScheme.SUCCESS)
    
    @staticmethod
    def error(text: str) -> str:
        """Format as error message."""
        return ColorScheme.format(f"✗ {text}", ColorScheme.ERROR)
    
    @staticmethod
    def warning(text: str) -> str:
        """Format as warning message."""
        return ColorScheme.format(f"⚠ {text}", ColorScheme.WARNING)
    
    @staticmethod
    def info(text: str) -> str:
        """Format as info message."""
        return ColorScheme.format(f"ℹ {text}", ColorScheme.INFO)
    
    @staticmethod
    def header(text: str) -> str:
        """Format as header."""
        return ColorScheme.format(text, ColorScheme.HEADER)
    
    @staticmethod
    def muted(text: str) -> str:
        """Format as muted text."""
        return ColorScheme.format(text, ColorScheme.MUTED)


__all__ = ["Color", "ColorScheme"]

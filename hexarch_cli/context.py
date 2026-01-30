"""CLI context object for hexarch-ctl."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hexarch_cli.config.config import ConfigManager
    from hexarch_cli.api.client import HexarchAPIClient
    from hexarch_cli.output.formatter import OutputFormatter
    from hexarch_cli.logging.audit import AuditLogger


class HexarchContext:
    """Context passed to all CLI commands."""
    
    def __init__(
        self,
        config_manager: "ConfigManager",
        api_client: "HexarchAPIClient",
        formatter: "OutputFormatter",
        audit_logger: "AuditLogger"
    ):
        self.config_manager = config_manager
        self.api_client = api_client
        self.formatter = formatter
        self.audit_logger = audit_logger


__all__ = ["HexarchContext"]

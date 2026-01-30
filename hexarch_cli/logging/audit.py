"""Audit logging for hexarch-ctl commands."""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Any, Dict
from datetime import datetime
from hexarch_cli.config.schemas import AuditConfig


class AuditLogger:
    """Audit logging for CLI commands."""
    
    def __init__(self, config: AuditConfig):
        """Initialize audit logger.
        
        Args:
            config: Audit configuration
        """
        self.config = config
        self.logger: Optional[logging.Logger] = None
        
        if config.enabled:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Set up rotating file logger."""
        log_path = Path(self.config.log_path).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("hexarch_audit")
        self.logger.setLevel(self._get_log_level())
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.config.max_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count
        )
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-5s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def _get_log_level(self) -> int:
        """Get logging level from config."""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR
        }
        return level_map.get(self.config.log_level, logging.INFO)
    
    def log_command(
        self,
        command: str,
        args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        user: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Log command execution.
        
        Args:
            command: Command name (e.g., "policy list")
            args: Command arguments
            result: Result summary
            user: Username (from token if available)
            error: Error message if command failed
        """
        if not self.logger:
            return
        
        # Build log message
        parts = [command]
        
        if args:
            arg_str = " ".join(f"--{k}={v}" for k, v in args.items())
            parts.append(arg_str)
        
        if result:
            parts.append(f"-> {result}")
        
        if user:
            parts.append(f"({user})")
        
        message = " ".join(parts)
        
        if error:
            self.logger.error(f"{message} ERROR: {error}")
        else:
            self.logger.info(message)
    
    def log_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        status: int = 200,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log API call.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status: Response status code
            duration_ms: Request duration in milliseconds
        """
        if not self.logger:
            return
        
        parts = [f"{method} {endpoint} -> {status}"]
        if duration_ms:
            parts.append(f"({duration_ms}ms)")
        
        message = " ".join(parts)
        
        if status >= 400:
            self.logger.error(message)
        else:
            self.logger.info(message)


__all__ = ["AuditLogger"]

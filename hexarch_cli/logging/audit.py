"""Audit logging for hexarch-ctl commands."""

import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Any, Dict
from datetime import datetime, timezone
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
        
        # Structured JSON output (one event per line)
        formatter = logging.Formatter("%(message)s")
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

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _emit_event(self, event: Dict[str, Any], *, level: str = "info") -> None:
        """Emit a single structured trace event as JSON."""
        if not self.logger:
            return

        payload = dict(event)
        payload.setdefault("timestamp", self._utc_now_iso())

        line = json.dumps(payload, default=str, separators=(",", ":"))
        if level == "error":
            self.logger.error(line)
        else:
            self.logger.info(line)
    
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
        
        event = {
            "event_type": "cli.command",
            "input": {
                "command": command,
                "args": args or {},
                "user": user,
            },
            "decision": "ERROR" if error else "SUCCESS",
            "output": {
                "result": result,
                "error": error,
            },
        }
        self._emit_event(event, level="error" if error else "info")
    
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
        
        event = {
            "event_type": "api.call",
            "input": {
                "endpoint": endpoint,
                "method": method,
            },
            "decision": "FAIL" if status >= 400 else "PASS",
            "output": {
                "status": status,
                "duration_ms": duration_ms,
            },
        }
        self._emit_event(event, level="error" if status >= 400 else "info")


__all__ = ["AuditLogger"]

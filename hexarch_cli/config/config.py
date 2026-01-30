"""Configuration loading and management."""

import os
import sys
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
from hexarch_cli.config.schemas import HexarchConfig


class ConfigManager:
    """Load and manage hexarch-ctl configuration."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".hexarch"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yml"
    DEFAULT_CACHE_DIR = DEFAULT_CONFIG_DIR / "cache"
    DEFAULT_LOG_FILE = DEFAULT_CONFIG_DIR / "cli.log"
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager."""
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_FILE)
        self.config: Optional[HexarchConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from multiple sources."""
        # 1. Load environment variables (.env file if present)
        load_dotenv()
        
        # 2. Load config file if it exists
        file_config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_path}: {e}", file=sys.stderr)
        
        # 3. Merge with environment variable overrides
        merged_config = self._merge_with_env(file_config)
        
        # 4. Validate with Pydantic
        try:
            self.config = HexarchConfig(**merged_config)
        except Exception as e:
            print(f"Error: Invalid configuration: {e}", file=sys.stderr)
            sys.exit(1)
        
        # 5. Ensure directories exist
        self._ensure_directories()
    
    def _merge_with_env(self, file_config: dict) -> dict:
        """Merge file config with environment variables."""
        merged = file_config.copy()
        
        # Override API settings from env
        if os.getenv("HEXARCH_API_URL"):
            if "api" not in merged:
                merged["api"] = {}
            merged["api"]["url"] = os.getenv("HEXARCH_API_URL")
        
        if os.getenv("HEXARCH_API_TOKEN"):
            if "api" not in merged:
                merged["api"] = {}
            merged["api"]["token"] = os.getenv("HEXARCH_API_TOKEN")
        
        # Override output format
        if os.getenv("HEXARCH_FORMAT"):
            if "output" not in merged:
                merged["output"] = {}
            merged["output"]["format"] = os.getenv("HEXARCH_FORMAT")
        
        # Override log path
        if os.getenv("HEXARCH_AUDIT_LOG"):
            if "audit" not in merged:
                merged["audit"] = {}
            merged["audit"]["log_path"] = os.getenv("HEXARCH_AUDIT_LOG")

        # Override database settings
        if os.getenv("HEXARCH_DB_URL"):
            if "db" not in merged:
                merged["db"] = {}
            merged["db"]["url"] = os.getenv("HEXARCH_DB_URL")

        if os.getenv("HEXARCH_DB_PROVIDER"):
            if "db" not in merged:
                merged["db"] = {}
            merged["db"]["provider"] = os.getenv("HEXARCH_DB_PROVIDER")

        if os.getenv("HEXARCH_DB_PATH"):
            if "db" not in merged:
                merged["db"] = {}
            merged["db"]["path"] = os.getenv("HEXARCH_DB_PATH")

        if os.getenv("HEXARCH_DB_ECHO"):
            if "db" not in merged:
                merged["db"] = {}
            merged["db"]["echo_sql"] = os.getenv("HEXARCH_DB_ECHO").lower() == "true"
        
        return merged
    
    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        self.DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create parent of log file
        log_path = Path(self.config.audit.log_path).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create parent directory for SQLite path (if configured)
        if self.config.db.provider == "sqlite" and self.config.db.path:
            db_path = Path(self.config.db.path).expanduser()
            if db_path.parent:
                db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> HexarchConfig:
        """Get loaded configuration."""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def save_config(self, config: HexarchConfig, path: Optional[str] = None) -> None:
        """Save configuration to YAML file."""
        output_path = Path(path or self.config_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
    
    def validate_connectivity(self) -> tuple[bool, str]:
        """Test API connectivity."""
        if not self.config:
            return False, "Configuration not loaded"
        
        import requests
        
        try:
            headers = {}
            if self.config.api.token:
                headers["Authorization"] = f"Bearer {self.config.api.token}"
            
            response = requests.get(
                f"{self.config.api.url}/health",
                headers=headers,
                timeout=self.config.api.timeout_seconds,
                verify=self.config.api.verify_ssl
            )
            
            if response.status_code == 200:
                return True, "API is reachable and healthy"
            else:
                return False, f"API returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to {self.config.api.url}"
        except requests.exceptions.Timeout:
            return False, f"API request timed out ({self.config.api.timeout_seconds}s)"
        except Exception as e:
            return False, str(e)


__all__ = ["ConfigManager"]

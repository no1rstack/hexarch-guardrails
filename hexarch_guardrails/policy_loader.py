"""
Policy Loader - Loads and manages policy configurations
"""
import yaml
import os
from typing import Dict, Any, Optional
from .exceptions import PolicyConfigError


class PolicyLoader:
    """Loads YAML-based policy configurations"""
    
    DEFAULT_POLICY_FILENAMES = [
        "hexarch.yaml",
        "hexarch.yml",
        ".hexarch.yaml",
        ".hexarch.yml",
    ]
    
    @staticmethod
    def find_policy_file(start_path: str = ".") -> Optional[str]:
        """
        Find policy file starting from start_path and walking up directory tree
        
        Args:
            start_path: Directory to start searching from
        
        Returns:
            Path to policy file if found, None otherwise
        """
        current = os.path.abspath(start_path)
        
        while True:
            for filename in PolicyLoader.DEFAULT_POLICY_FILENAMES:
                path = os.path.join(current, filename)
                if os.path.isfile(path):
                    return path
            
            parent = os.path.dirname(current)
            if parent == current:  # Reached root
                break
            current = parent
        
        return None
    
    @staticmethod
    def load(policy_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load policy configuration from YAML file
        
        Args:
            policy_file: Path to policy file. If None, auto-discovers.
        
        Returns:
            Parsed policy configuration
        
        Raises:
            PolicyConfigError: If file not found or invalid YAML
        """
        if policy_file is None:
            policy_file = PolicyLoader.find_policy_file()
        
        if policy_file is None:
            raise PolicyConfigError(
                "No policy file found. Create hexarch.yaml in your project root."
            )
        
        if not os.path.isfile(policy_file):
            raise PolicyConfigError(f"Policy file not found: {policy_file}")
        
        try:
            with open(policy_file, "r") as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise PolicyConfigError(f"Policy file is empty: {policy_file}")
            
            return config
        except yaml.YAMLError as e:
            raise PolicyConfigError(f"Invalid YAML in {policy_file}: {e}")
        except IOError as e:
            raise PolicyConfigError(f"Cannot read {policy_file}: {e}")
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """
        Validate policy configuration structure
        
        Args:
            config: Policy configuration dict
        
        Returns:
            True if valid
        
        Raises:
            PolicyConfigError: If invalid structure
        """
        if not isinstance(config, dict):
            raise PolicyConfigError("Policy must be a YAML dict")
        
        if "policies" not in config:
            raise PolicyConfigError("Policy must have 'policies' section")
        
        policies = config["policies"]
        if not isinstance(policies, list):
            raise PolicyConfigError("'policies' must be a list")
        
        for i, policy in enumerate(policies):
            if not isinstance(policy, dict):
                raise PolicyConfigError(f"Policy {i} must be a dict")
            
            if "id" not in policy:
                raise PolicyConfigError(f"Policy {i} must have an 'id'")
            
            if "rules" not in policy:
                raise PolicyConfigError(f"Policy {i} ({policy['id']}) must have 'rules'")
        
        return True

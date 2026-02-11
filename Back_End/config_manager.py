"""
Configuration Manager for Buddy Local Agent
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages local agent configuration."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Load configuration."""
        if self._config is None:
            try:
                self.reload()
            except FileNotFoundError:
                # Initialize with defaults if file not found
                logger.warning("Config file not found, using minimal defaults")
                self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'task_settings': {
                'timeout': 30,
                'max_retries': 3
            },
            'browser_settings': {
                'max_browsers': 25
            }
        }
    
    def reload(self):
        """Reload configuration from file."""
        # Look for config file - try multiple paths
        possible_paths = [
            Path(__file__).parent.parent / 'config' / 'buddy_local_config.yaml',  # Normal case
            Path(__file__).parent / 'config' / 'buddy_local_config.yaml',  # If running from Back_End
            Path.cwd() / 'config' / 'buddy_local_config.yaml',  # Current working directory
        ]
        
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            raise FileNotFoundError(f"Config file not found in any of: {possible_paths}")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value (in memory only)."""
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self._config.copy()


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return ConfigManager().get(key, default)


def set_config(key: str, value: Any):
    """Set configuration value."""
    ConfigManager().set(key, value)

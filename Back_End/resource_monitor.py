"""
Resource Monitor for Buddy Local Agent
Phase 2: Real-time system monitoring and throttling

Tracks:
- RAM usage
- CPU usage
- Safe browser count calculation
- Auto-throttling at high resource usage
- Metrics storage in SQLite
"""

import os
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import sqlite3

# Setup logging
logger = logging.getLogger('ResourceMonitor')

# Get config
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config_manager import get_config


class ResourceMonitor:
    """Monitor system resources and calculate safe limits."""
    
    # RAM per browser (MB) - from Phase 0 testing
    RAM_PER_BROWSER_MB = 141
    
    def __init__(self):
        """Initialize resource monitor."""
        self.ram_warning_threshold = get_config('ram_warning_threshold_percent', 85)
        self.ram_shutdown_threshold = get_config('ram_shutdown_threshold_percent', 90)
        self.cpu_warning_threshold = get_config('cpu_warning_threshold_percent', 80)
        self.throttle_at_ram_percent = get_config('throttle_at_ram_percent', 75)
        self.pause_tasks_at_ram_percent = get_config('pause_new_tasks_at_ram_percent', 85)
        self.emergency_stop_at_ram_percent = get_config('emergency_stop_at_ram_percent', 95)
        
        # Max browsers from config (or from Phase 0)
        self.max_browsers_configured = get_config('max_browsers', 25)
        
        # Thresholds for different modes
        self.safe_ram_percent = 70     # Conservative: 70% RAM
        self.comfortable_ram_percent = 80  # Comfortable: 80% RAM
        self.aggressive_ram_percent = 85   # Aggressive: 85% RAM
        
        # Tracking
        self.metrics_history: List[Dict[str, Any]] = []
        self.last_alert = None
        self.alert_cooldown_seconds = 300  # Don't spam alerts
        self.throttling = False
        self.paused = False
        
        logger.info("ResourceMonitor initialized")
        logger.info(f"  Safe browser limit: {self.safe_ram_percent}% RAM")
        logger.info(f"  Throttle at: {self.throttle_at_ram_percent}% RAM")
        logger.info(f"  Pause at: {self.pause_tasks_at_ram_percent}% RAM")
        logger.info(f"  Emergency stop at: {self.emergency_stop_at_ram_percent}% RAM")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system resource status."""
        try:
            # Get memory info
            mem = psutil.virtual_memory()
            ram_used_gb = mem.used / (1024 ** 3)
            ram_total_gb = mem.total / (1024 ** 3)
            ram_available_gb = mem.available / (1024 ** 3)
            ram_percent = mem.percent
            
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Calculate browser limits
            safe_browser_count = self.get_safe_browser_count('safe')
            comfortable_browser_count = self.get_safe_browser_count('comfortable')
            aggressive_browser_count = self.get_safe_browser_count('aggressive')
            
            # Determine current mode
            mode = self._get_current_mode(ram_percent)
            
            # Check thresholds
            approaching_limit = self.is_approaching_limit()
            should_throttle = self.should_throttle()
            should_pause = self.should_pause_tasks()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'ram_used_gb': round(ram_used_gb, 2),
                'ram_total_gb': round(ram_total_gb, 2),
                'ram_available_gb': round(ram_available_gb, 2),
                'ram_percent': round(ram_percent, 1),
                'cpu_percent': round(cpu_percent, 1),
                'cpu_count': cpu_count,
                'mode': mode,
                'browser_count_safe': safe_browser_count,
                'browser_count_comfortable': comfortable_browser_count,
                'browser_count_aggressive': aggressive_browser_count,
                'approaching_limit': approaching_limit,
                'throttling': should_throttle,
                'paused': should_pause,
                'healthy': not approaching_limit
            }
            
            return status
        
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return self._get_default_status()
    
    def get_safe_browser_count(self, mode: str = 'safe') -> int:
        """
        Calculate safe number of browsers based on RAM.
        
        Args:
            mode: 'safe' (70%), 'comfortable' (80%), 'aggressive' (85%)
        
        Returns:
            Number of browsers that can safely run
        """
        try:
            mem = psutil.virtual_memory()
            
            if mode == 'safe':
                percent = self.safe_ram_percent
            elif mode == 'comfortable':
                percent = self.comfortable_ram_percent
            elif mode == 'aggressive':
                percent = self.aggressive_ram_percent
            else:
                percent = self.safe_ram_percent
            
            # Available RAM we can use
            available_mb = (mem.total / (1024 ** 2)) * (percent / 100)
            
            # Browsers that fit
            browser_count = int(available_mb / self.RAM_PER_BROWSER_MB)
            
            # Cap at configured maximum
            browser_count = min(browser_count, self.max_browsers_configured * 2)
            
            # Minimum 1
            browser_count = max(browser_count, 1)
            
            return browser_count
        
        except Exception as e:
            logger.error(f"Error calculating browser count: {e}")
            return 1
    
    def is_approaching_limit(self) -> bool:
        """Check if RAM usage is approaching warning threshold."""
        mem = psutil.virtual_memory()
        return mem.percent >= self.ram_warning_threshold
    
    def should_throttle(self) -> bool:
        """Check if we should throttle task acceptance."""
        mem = psutil.virtual_memory()
        if mem.percent >= self.throttle_at_ram_percent:
            if not self.throttling:
                logger.warning(f"Starting throttle (RAM: {mem.percent:.1f}%)")
            self.throttling = True
            return True
        else:
            if self.throttling:
                logger.info(f"Stopping throttle (RAM: {mem.percent:.1f}%)")
            self.throttling = False
            return False
    
    def should_pause_tasks(self) -> bool:
        """Check if we should pause new task acceptance."""
        mem = psutil.virtual_memory()
        if mem.percent >= self.pause_tasks_at_ram_percent:
            if not self.paused:
                logger.error(f"PAUSING TASKS (RAM: {mem.percent:.1f}%)")
            self.paused = True
            return True
        else:
            if self.paused:
                logger.info(f"Resuming tasks (RAM: {mem.percent:.1f}%)")
            self.paused = False
            return False
    
    def get_alerts(self) -> List[Dict[str, str]]:
        """Get current alerts if thresholds exceeded."""
        alerts = []
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        # RAM alerts
        if mem.percent >= self.emergency_stop_at_ram_percent:
            alerts.append({
                'level': 'CRITICAL',
                'message': f'EMERGENCY: RAM at {mem.percent:.1f}%! Consider stopping tasks.'
            })
        elif mem.percent >= self.pause_tasks_at_ram_percent:
            alerts.append({
                'level': 'ERROR',
                'message': f'WARNING: RAM at {mem.percent:.1f}%. Pausing new tasks.'
            })
        elif mem.percent >= self.ram_warning_threshold:
            alerts.append({
                'level': 'WARNING',
                'message': f'RAM usage high: {mem.percent:.1f}%. Approaching limit.'
            })
        
        # CPU alerts
        if cpu >= self.cpu_warning_threshold:
            alerts.append({
                'level': 'WARNING',
                'message': f'CPU usage high: {cpu:.1f}%'
            })
        
        return alerts
    
    def update_metrics(self, db: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        """
        Update metrics and store in database.
        
        Args:
            db: SQLite connection (optional for storing metrics)
        
        Returns:
            Current metrics
        """
        try:
            status = self.get_system_status()
            
            # Add to history
            self.metrics_history.append(status)
            
            # Keep only last 144 data points (24 hours at 10-second intervals)
            if len(self.metrics_history) > 144:
                self.metrics_history = self.metrics_history[-144:]
            
            # Store in database if provided
            if db:
                try:
                    cursor = db.cursor()
                    cursor.execute('''
                        INSERT INTO agent_metrics 
                        (timestamp, browsers_active, ram_used_gb, ram_percent, cpu_percent)
                        VALUES (datetime('now'), 0, ?, ?, ?)
                    ''', (status['ram_used_gb'], status['ram_percent'], status['cpu_percent']))
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to store metrics: {e}")
            
            # Check for alerts
            alerts = self.get_alerts()
            if alerts and self._should_alert():
                for alert in alerts:
                    logger.log(
                        logging.CRITICAL if alert['level'] == 'CRITICAL' else logging.WARNING,
                        f"[{alert['level']}] {alert['message']}"
                    )
                self.last_alert = datetime.now()
            
            return status
        
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            return self._get_default_status()
    
    def _should_alert(self) -> bool:
        """Check if enough time has passed since last alert."""
        if self.last_alert is None:
            return True
        
        time_since_alert = (datetime.now() - self.last_alert).total_seconds()
        return time_since_alert >= self.alert_cooldown_seconds
    
    def _get_current_mode(self, ram_percent: float) -> str:
        """Get current operational mode based on RAM usage."""
        if ram_percent < self.throttle_at_ram_percent:
            return 'optimal'
        elif ram_percent < self.pause_tasks_at_ram_percent:
            return 'throttled'
        elif ram_percent < self.emergency_stop_at_ram_percent:
            return 'paused'
        else:
            return 'critical'
    
    def get_historical_metrics(self, minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical metrics from buffer."""
        if minutes:
            # Filter by time
            cutoff = datetime.now() - timedelta(minutes=minutes)
            return [m for m in self.metrics_history 
                    if datetime.fromisoformat(m['timestamp']) >= cutoff]
        
        return self.metrics_history.copy()
    
    def get_resource_forecast(self, minutes_ahead: int = 5) -> Dict[str, Any]:
        """
        Forecast resource usage based on historical trend.
        
        Args:
            minutes_ahead: How many minutes ahead to forecast
        
        Returns:
            Forecasted RAM and CPU usage
        """
        if len(self.metrics_history) < 2:
            return {'ram_percent_forecast': None, 'cpu_percent_forecast': None}
        
        try:
            # Get last 10 measurements
            recent = self.metrics_history[-10:]
            
            # Calculate trends
            ram_values = [m['ram_percent'] for m in recent]
            cpu_values = [m['cpu_percent'] for m in recent]
            
            ram_trend = (ram_values[-1] - ram_values[0]) / len(ram_values)
            cpu_trend = (cpu_values[-1] - cpu_values[0]) / len(cpu_values)
            
            # Project forward
            forecast_steps = minutes_ahead * 6  # 6 measurements per minute (10-second interval)
            ram_forecast = ram_values[-1] + (ram_trend * forecast_steps)
            cpu_forecast = cpu_values[-1] + (cpu_trend * forecast_steps)
            
            return {
                'ram_percent_forecast': round(max(0, min(100, ram_forecast)), 1),
                'cpu_percent_forecast': round(max(0, min(100, cpu_forecast)), 1),
                'ram_trend': round(ram_trend, 3),
                'cpu_trend': round(cpu_trend, 3),
                'forecast_minutes': minutes_ahead
            }
        
        except Exception as e:
            logger.warning(f"Error forecasting: {e}")
            return {'ram_percent_forecast': None, 'cpu_percent_forecast': None}
    
    def _get_default_status(self) -> Dict[str, Any]:
        """Return default status when error occurs."""
        return {
            'timestamp': datetime.now().isoformat(),
            'ram_used_gb': 0,
            'ram_total_gb': 0,
            'ram_available_gb': 0,
            'ram_percent': 0,
            'cpu_percent': 0,
            'cpu_count': 0,
            'mode': 'error',
            'browser_count_safe': 1,
            'browser_count_comfortable': 1,
            'browser_count_aggressive': 1,
            'approaching_limit': False,
            'throttling': False,
            'paused': False,
            'healthy': False
        }
    
    def health_check(self) -> bool:
        """Quick health check - is system in good state?"""
        mem = psutil.virtual_memory()
        return mem.percent < self.pause_tasks_at_ram_percent
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        status = self.get_system_status()
        
        return f"""
╔═══════════════════════════════════════════════════════════╗
║           BUDDY LOCAL AGENT - SYSTEM STATUS               ║
╠═══════════════════════════════════════════════════════════╣
║ RAM Usage:     {status['ram_used_gb']:5.1f} GB / {status['ram_total_gb']:5.1f} GB ({status['ram_percent']:5.1f}%)
║ CPU Usage:     {status['cpu_percent']:5.1f}% ({status['cpu_count']} cores)
║ Mode:          {status['mode'].upper():20}
║ Browsers:      Safe: {status['browser_count_safe']:2d}  Comfortable: {status['browser_count_comfortable']:2d}  Aggressive: {status['browser_count_aggressive']:2d}
║ Status:        {'🟢 HEALTHY' if status['healthy'] else '🔴 WARNING'}
║ Throttling:    {'Yes' if status['throttling'] else 'No'}
║ Paused:        {'Yes' if status['paused'] else 'No'}
╚═══════════════════════════════════════════════════════════╝
"""

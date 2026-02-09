"""
Mployer Automation Scheduler

Schedules automated searches on Mployer for hands-off contact collection.
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import schedule
import time

from backend.mployer_scraper import run_mployer_automation
from backend.credential_manager import CredentialManager

logger = logging.getLogger(__name__)

BUDDY_ROOT = Path(__file__).parent.parent
CONFIG_FILE = BUDDY_ROOT / "mployer_config.json"


class MployerScheduler:
    """Schedule and manage Mployer automation runs"""
    
    def __init__(self):
        self.config = self.load_config()
        self.is_running = False
    
    @staticmethod
    def load_config() -> Dict:
        """Load Mployer automation configuration"""
        default_config = {
            "enabled": True,
            "schedule": "daily",  # daily, weekly, custom
            "run_time": "08:00",  # 8 AM by default
            "job_title": "Human Resources",
            "location": "Baltimore, Maryland",
            "company_size_min": 10,
            "company_size_max": 500,
            "exclude_keywords": ["government", "union", "federal", "military"],
            "max_contacts": 50,
            "workflow_id": None,  # Optional GHL workflow to trigger
            "last_run": None,
            "next_run": None
        }
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"✓ Config saved to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def run_automation(self) -> Dict:
        """Execute Mployer automation once"""
        try:
            logger.info("="*60)
            logger.info("Starting Mployer Automation Run")
            logger.info("="*60)
            
            # Get credentials
            creds = CredentialManager.get_credentials()
            
            # Run the automation
            result = run_mployer_automation(
                username=creds["username"],
                password=creds["password"],
                config=self.config
            )
            
            # Update config
            self.config["last_run"] = datetime.now().isoformat()
            self.save_config()
            
            logger.info("="*60)
            logger.info(f"Run complete: {result}")
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            logger.error(f"Automation run failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def schedule_daily(self, run_time: str = "08:00"):
        """
        Schedule daily automation run.
        
        Args:
            run_time: Time to run in HH:MM format (24-hour)
        """
        schedule.every().day.at(run_time).do(self.run_automation)
        logger.info(f"✓ Scheduled daily run at {run_time}")
    
    def schedule_weekly(self, day: str = "monday", run_time: str = "08:00"):
        """
        Schedule weekly automation run.
        
        Args:
            day: Day of week (monday, tuesday, etc)
            run_time: Time to run in HH:MM format
        """
        getattr(schedule.every(), day).at(run_time).do(self.run_automation)
        logger.info(f"✓ Scheduled weekly run on {day} at {run_time}")
    
    def schedule_hourly(self):
        """Schedule hourly automation run"""
        schedule.every().hour.do(self.run_automation)
        logger.info("✓ Scheduled hourly runs")
    
    def start_scheduler(self):
        """Start the scheduler (runs in foreground)"""
        try:
            if not self.config.get("enabled"):
                logger.info("Mployer automation is disabled in config")
                return
            
            logger.info("Starting Mployer Scheduler...")
            
            # Set up schedule based on config
            schedule_type = self.config.get("schedule", "daily").lower()
            
            if schedule_type == "daily":
                self.schedule_daily(self.config.get("run_time", "08:00"))
            elif schedule_type == "weekly":
                self.schedule_weekly(run_time=self.config.get("run_time", "08:00"))
            elif schedule_type == "hourly":
                self.schedule_hourly()
            
            self.is_running = True
            
            # Keep scheduler running
            logger.info("Scheduler is running. Press Ctrl+C to stop.")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.is_running = False
    
    def run_once_now(self) -> Dict:
        """Run automation immediately (don't wait for schedule)"""
        logger.info("Running Mployer automation immediately...")
        return self.run_automation()
    
    def update_search_criteria(self, **kwargs):
        """Update search configuration"""
        valid_keys = [
            "job_title", "location", "company_size_min", "company_size_max",
            "exclude_keywords", "max_contacts", "workflow_id"
        ]
        
        for key, value in kwargs.items():
            if key in valid_keys:
                self.config[key] = value
                logger.info(f"Updated {key} = {value}")
        
        self.save_config()


def interactive_setup():
    """Interactive setup for Mployer automation"""
    print("\n" + "="*60)
    print("BUDDY - Mployer Automation Setup")
    print("="*60)
    
    scheduler = MployerScheduler()
    
    print("\nCurrent Configuration:")
    print(json.dumps(scheduler.config, indent=2))
    
    print("\nOptions:")
    print("1. Update search criteria")
    print("2. Change schedule")
    print("3. Run automation now")
    print("4. Save and exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        job_title = input("Job title (default: Head of HR): ").strip() or "Head of HR"
        location = input("Location (default: Baltimore, Maryland): ").strip() or "Baltimore, Maryland"
        size_min = int(input("Min company size (default: 10): ").strip() or "10")
        size_max = int(input("Max company size (default: 500): ").strip() or "500")
        max_contacts = int(input("Max contacts per run (default: 50): ").strip() or "50")
        
        scheduler.update_search_criteria(
            job_title=job_title,
            location=location,
            company_size_min=size_min,
            company_size_max=size_max,
            max_contacts=max_contacts
        )
        
        print("✓ Configuration updated!")
    
    elif choice == "2":
        print("\nSchedule options:")
        print("1. Daily (default 8 AM)")
        print("2. Weekly (Mondays at 8 AM)")
        print("3. Hourly")
        
        sched_choice = input("Select (1-3): ").strip()
        if sched_choice == "1":
            scheduler.config["schedule"] = "daily"
        elif sched_choice == "2":
            scheduler.config["schedule"] = "weekly"
        elif sched_choice == "3":
            scheduler.config["schedule"] = "hourly"
        
        scheduler.save_config()
        print("✓ Schedule updated!")
    
    elif choice == "3":
        result = scheduler.run_once_now()
        print("\nResult:")
        print(json.dumps(result, indent=2))
    
    scheduler.save_config()
    print("\n✓ Setup complete!")

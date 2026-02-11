"""
Browser Capacity Test - Phase 0
Tests how many Chrome browsers your laptop can handle simultaneously.

Usage:
    python scripts/test_browser_capacity.py

This will:
1. Launch browsers in batches of 5
2. Monitor RAM/CPU usage
3. Determine safe maximum
4. Generate report
"""

import time
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import os

# Add Back_End to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Back_End'))

class BrowserCapacityTester:
    def __init__(self):
        self.browsers = []
        self.initial_ram = psutil.virtual_memory().used / (1024 ** 3)  # GB
        self.results = []
        
    def get_system_stats(self):
        """Get current system resource usage."""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        return {
            'ram_used_gb': mem.used / (1024 ** 3),
            'ram_percent': mem.percent,
            'ram_available_gb': mem.available / (1024 ** 3),
            'cpu_percent': cpu
        }
    
    def create_optimized_chrome_options(self):
        """Create Chrome options optimized for low memory usage."""
        options = Options()
        
        # Performance optimizations
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Save bandwidth and memory
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-breakpad')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-sync')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--window-size=800,600')  # Smaller window = less RAM
        
        # Optional: Headless mode (saves more RAM)
        # options.add_argument('--headless')  # Uncomment to test headless
        
        # Logging
        options.add_argument('--log-level=3')  # Only fatal errors
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        return options
    
    def launch_browser(self):
        """Launch a single Chrome browser."""
        try:
            options = self.create_optimized_chrome_options()
            driver = webdriver.Chrome(options=options)
            driver.get('about:blank')  # Navigate to blank page
            return driver
        except Exception as e:
            print(f"❌ Failed to launch browser: {e}")
            return None
    
    def test_capacity(self, max_browsers=50, batch_size=5):
        """Test browser capacity by launching in batches."""
        print("=" * 70)
        print("🧪 BROWSER CAPACITY TEST")
        print("=" * 70)
        print(f"\n📊 Initial System Stats:")
        initial_stats = self.get_system_stats()
        print(f"   RAM: {initial_stats['ram_used_gb']:.2f} GB used ({initial_stats['ram_percent']:.1f}%)")
        print(f"   CPU: {initial_stats['cpu_percent']:.1f}%")
        print(f"   Available RAM: {initial_stats['ram_available_gb']:.2f} GB")
        print(f"\n🚀 Starting browser launches (batch size: {batch_size})...")
        print("-" * 70)
        
        browser_count = 0
        ram_per_browser_estimates = []
        
        try:
            while browser_count < max_browsers:
                # Launch batch
                batch_start_time = time.time()
                batch_browsers = []
                
                for i in range(batch_size):
                    browser = self.launch_browser()
                    if browser:
                        batch_browsers.append(browser)
                        browser_count += 1
                        time.sleep(0.5)  # Small delay between launches
                    else:
                        break
                
                batch_time = time.time() - batch_start_time
                
                if not batch_browsers:
                    print(f"\n❌ Failed to launch browsers. Stopping test.")
                    break
                
                self.browsers.extend(batch_browsers)
                
                # Wait for browsers to stabilize
                time.sleep(2)
                
                # Get stats
                stats = self.get_system_stats()
                ram_increase = stats['ram_used_gb'] - self.initial_ram
                ram_per_browser = ram_increase / browser_count if browser_count > 0 else 0
                ram_per_browser_estimates.append(ram_per_browser)
                
                # Calculate safe estimates
                safe_80 = int((initial_stats['ram_available_gb'] * 0.8) / ram_per_browser) if ram_per_browser > 0 else 0
                safe_70 = int((initial_stats['ram_available_gb'] * 0.7) / ram_per_browser) if ram_per_browser > 0 else 0
                
                print(f"\n✅ Batch {browser_count // batch_size}: {len(batch_browsers)} browsers launched ({batch_time:.1f}s)")
                print(f"   Total Browsers: {browser_count}")
                print(f"   RAM: {stats['ram_used_gb']:.2f} GB ({stats['ram_percent']:.1f}%)")
                print(f"   CPU: {stats['cpu_percent']:.1f}%")
                print(f"   RAM/Browser: ~{ram_per_browser * 1024:.0f} MB")
                print(f"   Estimated Safe Max (80%): ~{safe_80} browsers")
                print(f"   Estimated Safe Max (70%): ~{safe_70} browsers")
                
                # Store result
                self.results.append({
                    'browser_count': browser_count,
                    'ram_used_gb': stats['ram_used_gb'],
                    'ram_percent': stats['ram_percent'],
                    'cpu_percent': stats['cpu_percent'],
                    'ram_per_browser_mb': ram_per_browser * 1024
                })
                
                # Safety checks
                if stats['ram_percent'] > 85:
                    print(f"\n⚠️  RAM usage > 85%. Stopping for safety.")
                    break
                
                if stats['ram_percent'] > 75:
                    print(f"\n⚠️  RAM usage > 75%. Approaching limit.")
                
                # Ask to continue if getting high
                if browser_count >= 10 and browser_count % 10 == 0:
                    response = input(f"\n   Continue to {browser_count + batch_size} browsers? (y/n): ")
                    if response.lower() != 'y':
                        break
        
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Test interrupted by user.")
        
        except Exception as e:
            print(f"\n\n❌ Error during test: {e}")
        
        finally:
            # Cleanup
            print(f"\n🧹 Cleaning up {len(self.browsers)} browsers...")
            for browser in self.browsers:
                try:
                    browser.quit()
                except:
                    pass
            
            time.sleep(2)
            final_stats = self.get_system_stats()
            
            # Generate report
            self.generate_report(initial_stats, final_stats, ram_per_browser_estimates)
    
    def generate_report(self, initial_stats, final_stats, ram_estimates):
        """Generate final capacity report."""
        print("\n" + "=" * 70)
        print("📋 CAPACITY TEST REPORT")
        print("=" * 70)
        
        if not self.results:
            print("\n❌ No data collected.")
            return
        
        max_browsers = max(r['browser_count'] for r in self.results)
        max_ram = max(r['ram_percent'] for r in self.results)
        avg_ram_per_browser = sum(ram_estimates) / len(ram_estimates) if ram_estimates else 0
        
        print(f"\n📊 Test Results:")
        print(f"   Maximum browsers tested: {max_browsers}")
        print(f"   Peak RAM usage: {max_ram:.1f}%")
        print(f"   Average RAM per browser: ~{avg_ram_per_browser * 1024:.0f} MB")
        
        print(f"\n💻 Your Laptop Specs:")
        total_ram = psutil.virtual_memory().total / (1024 ** 3)
        cpu_count = psutil.cpu_count()
        print(f"   Total RAM: {total_ram:.1f} GB")
        print(f"   CPU Cores: {cpu_count}")
        
        print(f"\n✅ Recommended Browser Limits:")
        if avg_ram_per_browser > 0:
            conservative = int((total_ram * 0.6) / avg_ram_per_browser)
            optimal = int((total_ram * 0.7) / avg_ram_per_browser)
            comfortable = int((total_ram * 0.8) / avg_ram_per_browser)
            maximum = int((total_ram * 0.85) / avg_ram_per_browser)
            
            print(f"   Conservative (60% RAM): {conservative} browsers")
            print(f"   Optimal (70% RAM): {optimal} browsers")
            print(f"   Comfortable (80% RAM): {comfortable} browsers")
            print(f"   Maximum (85% RAM): {maximum} browsers")
            
            print(f"\n🎯 Recommendation for Buddy Local Agent:")
            print(f"   Set max_browsers = {optimal}")
            print(f"   This leaves {100 - 70:.0f}% RAM for your other work")
        
        print(f"\n💾 RAM Recovery:")
        print(f"   After cleanup: {final_stats['ram_used_gb']:.2f} GB ({final_stats['ram_percent']:.1f}%)")
        
        # Save to file
        report_path = os.path.join(os.path.dirname(__file__), '..', 'PHASE0_BROWSER_CAPACITY_REPORT.txt')
        with open(report_path, 'w') as f:
            f.write("BROWSER CAPACITY TEST REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Maximum browsers tested: {max_browsers}\n")
            f.write(f"Peak RAM usage: {max_ram:.1f}%\n")
            f.write(f"Average RAM per browser: ~{avg_ram_per_browser * 1024:.0f} MB\n\n")
            f.write(f"Laptop Specs:\n")
            f.write(f"  Total RAM: {total_ram:.1f} GB\n")
            f.write(f"  CPU Cores: {cpu_count}\n\n")
            if avg_ram_per_browser > 0:
                f.write(f"Recommended Limits:\n")
                f.write(f"  Conservative (60%): {conservative} browsers\n")
                f.write(f"  Optimal (70%): {optimal} browsers\n")
                f.write(f"  Comfortable (80%): {comfortable} browsers\n")
                f.write(f"  Maximum (85%): {maximum} browsers\n\n")
                f.write(f"RECOMMENDATION: Set max_browsers = {optimal}\n")
        
        print(f"\n📄 Report saved to: {os.path.basename(report_path)}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n🔧 Configuration:")
    print("   - Chrome options: Optimized (images disabled, small window)")
    print("   - Headless mode: Disabled (easier to see)")
    print("   - Safety limit: Stops at 85% RAM\n")
    
    response = input("Ready to start browser capacity test? (y/n): ")
    if response.lower() == 'y':
        tester = BrowserCapacityTester()
        tester.test_capacity(max_browsers=50, batch_size=5)
    else:
        print("Test cancelled.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update All - Master script to run the entire pipeline
"""

import os, sys, subprocess, time, argparse
from datetime import datetime

# Script execution order
SCRIPTS = [
    # PART 1: Data Collection
    ("create_us_daily_prices.py", "[1/12] Data Collection", 600, False),
    ("analyze_volume.py", "[2/12] Volume Analysis", 300, False),
    ("analyze_13f.py", "[3/12] Institutional Analysis", 600, False),
    ("analyze_etf_flows.py", "[4/12] ETF Flows", 300, False),
    
    # PART 2: Screening
    ("smart_money_screener_v2.py", "[5/12] Smart Money Screening", 600, False),
    ("sector_heatmap.py", "[6/12] Sector Heatmap", 120, False),
    ("options_flow.py", "[7/12] Options Flow", 120, False),
    ("insider_tracker.py", "[8/12] Insider Tracker", 120, False),
    
    # PART 3: AI Analysis
    ("ai_summary_generator.py", "[9/12] AI Summaries", 900, True),
    ("final_report_generator.py", "[10/12] Final Report", 60, False),
    ("macro_analyzer.py", "[11/12] Macro Analysis", 300, True),
    ("economic_calendar.py", "[12/12] Economic Calendar", 120, True),
]


def run_script(name: str, desc: str, timeout: int) -> bool:
    """Run a single script with timeout"""
    print(f"\n{'='*50}")
    print(f"{desc}: {name}")
    print('='*50)
    
    try:
        result = subprocess.run(
            [sys.executable, name],
            timeout=timeout,
            check=True,
            capture_output=False
        )
        print(f"[OK] {name} completed successfully")
        return True
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name} timed out after {timeout}s")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {name} failed with code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"[FAIL] {name} not found")
        return False
    except Exception as e:
        print(f"[FAIL] {name} error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='US Market Backend Pipeline')
    parser.add_argument('--quick', action='store_true', help='Skip AI-related scripts')
    parser.add_argument('--data-only', action='store_true', help='Only run data collection')
    parser.add_argument('--ai-only', action='store_true', help='Only run AI analysis')
    parser.add_argument('--script', type=str, help='Run specific script')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("US MARKET BACKEND PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    start_time = time.time()
    success_count = 0
    fail_count = 0
    
    # Filter scripts based on arguments
    scripts_to_run = SCRIPTS.copy()
    
    if args.script:
        scripts_to_run = [(s, d, t, ai) for s, d, t, ai in SCRIPTS if s == args.script]
        if not scripts_to_run:
            print(f"[FAIL] Script '{args.script}' not found")
            return
    elif args.quick:
        scripts_to_run = [(s, d, t, ai) for s, d, t, ai in SCRIPTS if not ai]
    elif args.data_only:
        scripts_to_run = SCRIPTS[:4]  # Only PART 1
    elif args.ai_only:
        scripts_to_run = SCRIPTS[8:]  # Only PART 3
    
    # Run scripts
    for script, desc, timeout, is_ai in scripts_to_run:
        success = run_script(script, desc, timeout)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if fail_count > 0:
        print("\nSome scripts failed. Check logs above.")
        sys.exit(1)
    else:
        print("\nAll scripts completed successfully!")


if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()

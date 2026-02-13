#!/usr/bin/env python3
"""
LightRAG File Processing Timing Report Generator
Analyzes file_processing_timings.jsonl and generates reports
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

TIMING_LOG_FILE = Path("/root/lightRAG/lightrag-vietnamese-package/logs/file_processing_timings.jsonl")


def load_timings():
    """Load all timing entries from log file"""
    timings = []
    if not TIMING_LOG_FILE.exists():
        print(f"⚠️  Timing log file not found: {TIMING_LOG_FILE}")
        return timings
    
    with open(TIMING_LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    timings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return timings


def generate_report():
    """Generate timing report"""
    timings = load_timings()
    
    if not timings:
        print("❌ No timing data available")
        return
    
    # Group by filename
    by_file = defaultdict(list)
    for entry in timings:
        by_file[entry['filename']].append(entry)
    
    print("\n" + "="*80)
    print("📊 LIGHT RAG FILE PROCESSING TIMING REPORT")
    print("="*80)
    print(f"\nTotal files processed: {len(by_file)}")
    print(f"Total timing events: {len(timings)}")
    
    # Calculate statistics per event type
    event_stats = defaultdict(lambda: {'count': 0, 'total_duration': 0, 'durations': []})
    for entry in timings:
        event = entry['event']
        event_stats[event]['count'] += 1
        if 'duration_seconds' in entry:
            duration = entry['duration_seconds']
            event_stats[event]['total_duration'] += duration
            event_stats[event]['durations'].append(duration)
    
    print("\n" + "-"*80)
    print("⏱️  TIMING STATISTICS BY EVENT TYPE")
    print("-"*80)
    print(f"{'Event':<30} {'Count':<8} {'Total(s)':<12} {'Avg(s)':<12} {'Min(s)':<12} {'Max(s)':<12}")
    print("-"*80)
    
    for event, stats in sorted(event_stats.items()):
        count = stats['count']
        total = stats['total_duration']
        durations = stats['durations']
        avg = total / count if count > 0 else 0
        min_dur = min(durations) if durations else 0
        max_dur = max(durations) if durations else 0
        print(f"{event:<30} {count:<8} {total:<12.2f} {avg:<12.2f} {min_dur:<12.2f} {max_dur:<12.2f}")
    
    # Per-file detailed report
    print("\n" + "-"*80)
    print("📁 DETAILED REPORT BY FILE")
    print("-"*80)
    
    for filename, entries in sorted(by_file.items()):
        print(f"\n📄 {filename}")
        print("-" * 40)
        
        # Create timeline
        timeline = sorted(entries, key=lambda x: x['unix_time'])
        start_time = None
        end_time = None
        
        for entry in timeline:
            event = entry['event']
            timestamp = entry['timestamp']
            duration = entry.get('duration_seconds', '-')
            dur_str = f"{duration:.2f}s" if isinstance(duration, (int, float)) else duration
            print(f"  {timestamp} | {event:<25} | {dur_str}")
            
            if 'start' in event.lower() or event == 'processing_start':
                if start_time is None:
                    start_time = entry['unix_time']
            if 'complete' in event.lower() or event == 'processing_complete':
                end_time = entry['unix_time']
        
        if start_time and end_time:
            total_duration = end_time - start_time
            print(f"  {'':12} Total processing time: {total_duration:.2f}s")
    
    print("\n" + "="*80)


def watch_live():
    """Watch timing log in real-time"""
    print("👀 Watching timing log in real-time (Press Ctrl+C to stop)...")
    print("-"*80)
    
    last_position = 0
    try:
        while True:
            if TIMING_LOG_FILE.exists():
                with open(TIMING_LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                filename = entry['filename']
                                event = entry['event']
                                duration = entry.get('duration_seconds', '-')
                                dur_str = f" ⏱️  {duration:.2f}s" if isinstance(duration, (int, float)) else ""
                                timestamp = entry['timestamp'].split('T')[1].split('.')[0]
                                print(f"[{timestamp}] {filename:<30} | {event:<25}{dur_str}")
                            except json.JSONDecodeError:
                                continue
            
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n✋ Stopped watching")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch_live()
    else:
        generate_report()
        print("\n💡 Tip: Run with 'watch' argument to monitor in real-time")
        print("   python3 timing_report.py watch")

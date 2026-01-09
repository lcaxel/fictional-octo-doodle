#!/usr/bin/env python3
"""
Step 2: Explore what's inside a CS2 demo file.

This script shows you all available data in a demo file:
- Available events
- Available player properties
- Basic match info
"""
import os
import sys
from demoparser2 import DemoParser

def find_demo_file(demos_dir: str) -> str | None:
    """Find any .dem file in the demos directory."""
    if not os.path.exists(demos_dir):
        return None
    for f in os.listdir(demos_dir):
        if f.endswith('.dem'):
            return os.path.join(demos_dir, f)
    return None

def explore_demo(demo_path: str):
    """Explore contents of a demo file."""
    print("=" * 70)
    print(f"EXPLORING DEMO: {os.path.basename(demo_path)}")
    print("=" * 70)
    print(f"File size: {os.path.getsize(demo_path) / (1024*1024):.2f} MB")
    print()

    # Initialize parser
    parser = DemoParser(demo_path)

    # 1. Get header info
    print("-" * 70)
    print("1. MATCH HEADER (Basic Info)")
    print("-" * 70)
    header = parser.parse_header()
    for key, value in header.items():
        print(f"  {key}: {value}")
    print()

    # 2. List all available game events
    print("-" * 70)
    print("2. AVAILABLE GAME EVENTS")
    print("-" * 70)
    events = parser.list_game_events()
    print(f"  Total events available: {len(events)}")
    print()

    # Categorize events
    categories = {
        'player': [],
        'weapon': [],
        'grenade': [],
        'bomb': [],
        'round': [],
        'other': []
    }

    for event in events:
        if event.startswith('player_'):
            categories['player'].append(event)
        elif event.startswith('weapon_'):
            categories['weapon'].append(event)
        elif any(g in event for g in ['grenade', 'flash', 'smoke', 'inferno', 'decoy']):
            categories['grenade'].append(event)
        elif 'bomb' in event:
            categories['bomb'].append(event)
        elif 'round' in event:
            categories['round'].append(event)
        else:
            categories['other'].append(event)

    for cat_name, cat_events in categories.items():
        if cat_events:
            print(f"  [{cat_name.upper()}] ({len(cat_events)} events)")
            for e in sorted(cat_events)[:10]:  # Show first 10
                print(f"    - {e}")
            if len(cat_events) > 10:
                print(f"    ... and {len(cat_events) - 10} more")
            print()

    # 3. Sample some key events
    print("-" * 70)
    print("3. SAMPLE DATA FROM KEY EVENTS")
    print("-" * 70)

    # Player deaths (kills)
    print()
    print("  [KILLS - player_death event]")
    try:
        kills_df = parser.parse_event("player_death")
        print(f"  Total kills in match: {len(kills_df)}")
        if len(kills_df) > 0:
            print(f"  Columns available: {list(kills_df.columns)}")
            print()
            print("  First 3 kills:")
            for idx, row in kills_df.head(3).iterrows():
                attacker = row.get('attacker_name', 'Unknown')
                victim = row.get('user_name', row.get('victim_name', 'Unknown'))
                weapon = row.get('weapon', 'Unknown')
                headshot = row.get('headshot', False)
                hs_str = " (HS)" if headshot else ""
                print(f"    {attacker} killed {victim} with {weapon}{hs_str}")
    except Exception as e:
        print(f"  Error parsing kills: {e}")

    # Damage events
    print()
    print("  [DAMAGE - player_hurt event]")
    try:
        damage_df = parser.parse_event("player_hurt")
        print(f"  Total damage events: {len(damage_df)}")
        if len(damage_df) > 0:
            print(f"  Columns available: {list(damage_df.columns)}")
    except Exception as e:
        print(f"  Error parsing damage: {e}")

    # Round events
    print()
    print("  [ROUNDS - round_end event]")
    try:
        rounds_df = parser.parse_event("round_end")
        print(f"  Total rounds: {len(rounds_df)}")
        if len(rounds_df) > 0:
            print(f"  Columns available: {list(rounds_df.columns)}")
    except Exception as e:
        print(f"  Error parsing rounds: {e}")

    # Grenade events
    print()
    print("  [GRENADES - smokegrenade_detonate event]")
    try:
        grenades_df = parser.parse_event("smokegrenade_detonate")
        print(f"  Total smoke grenades: {len(grenades_df)}")
        if len(grenades_df) > 0:
            print(f"  Columns available: {list(grenades_df.columns)}")
    except Exception as e:
        print(f"  Error parsing grenades: {e}")

    # 4. Tick-level data exploration
    print()
    print("-" * 70)
    print("4. TICK-LEVEL DATA (Player Properties)")
    print("-" * 70)

    # Sample tick data with key properties
    key_properties = [
        "X", "Y", "Z",                    # Position
        "pitch", "yaw",                   # View angles
        "health", "armor_value",          # Health
        "active_weapon_name",             # Weapon
        "team_name",                      # Team
        "is_alive",                       # Status
    ]

    print(f"  Sampling tick data with properties: {key_properties}")
    try:
        # Only parse first 1000 ticks to show structure
        tick_df = parser.parse_ticks(key_properties, ticks=list(range(0, 1000, 100)))
        print(f"  Sampled {len(tick_df)} rows")
        print(f"  Columns: {list(tick_df.columns)}")
        print()
        print("  Sample row:")
        if len(tick_df) > 0:
            sample = tick_df.iloc[0]
            for col in tick_df.columns:
                print(f"    {col}: {sample[col]}")
    except Exception as e:
        print(f"  Error parsing ticks: {e}")

    print()
    print("=" * 70)
    print("EXPLORATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run 03_extract_data.py to extract all relevant data")
    print("2. Data will be saved to /data folder as JSON/CSV")

def main():
    demos_dir = os.path.join(os.path.dirname(__file__), '..', 'demos')

    demo_path = find_demo_file(demos_dir)

    if not demo_path:
        print("ERROR: No .dem file found!")
        print()
        print(f"Please place a CS2 demo file in: {os.path.abspath(demos_dir)}")
        print()
        print("You can download demos from:")
        print("- HLTV.org (pro matches)")
        print("- Your CS2 match history")
        print("- FACEIT/ESEA")
        sys.exit(1)

    explore_demo(demo_path)

if __name__ == "__main__":
    main()

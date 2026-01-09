#!/usr/bin/env python3
"""
Step 4: Analyze extracted data and show statistics.

This script demonstrates what kind of analytics you can do
with the extracted data.
"""
import os
import sys
import json
from collections import Counter


def load_data(json_path: str) -> dict:
    """Load extracted data from JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_match(data: dict):
    """Perform comprehensive match analysis."""

    print("=" * 70)
    print("MATCH ANALYSIS REPORT")
    print("=" * 70)

    # 1. Match Overview
    meta = data.get("metadata", {})
    print()
    print("[1] MATCH OVERVIEW")
    print("-" * 40)
    print(f"  Map: {meta.get('map_name', 'Unknown')}")
    print(f"  Duration: {meta.get('playback_time', 0):.0f} seconds")
    print(f"  Tickrate: {meta.get('tickrate', 64)}")
    print(f"  Total ticks: {meta.get('playback_ticks', 0):,}")

    # 2. Team Analysis
    players = data.get("players", [])
    kills = data.get("kills", [])
    rounds = data.get("rounds", [])

    print()
    print("[2] TEAM COMPOSITION")
    print("-" * 40)

    teams = {}
    for player in players:
        team = player.get("team", "Unknown")
        if team not in teams:
            teams[team] = []
        teams[team].append(player.get("name", "Unknown"))

    for team_name, team_players in teams.items():
        print(f"  {team_name}:")
        for p in team_players:
            print(f"    - {p}")

    # 3. Round Analysis
    print()
    print("[3] ROUND RESULTS")
    print("-" * 40)
    print(f"  Total rounds: {len(rounds)}")

    round_winners = Counter(r.get("winner") for r in rounds)
    for winner, count in round_winners.most_common():
        print(f"    {winner}: {count} rounds")

    win_reasons = Counter(r.get("reason") for r in rounds)
    print()
    print("  Win reasons:")
    for reason, count in win_reasons.most_common():
        print(f"    {reason}: {count}")

    # 4. Kill Analysis
    print()
    print("[4] KILL STATISTICS")
    print("-" * 40)
    print(f"  Total kills: {len(kills)}")

    # Kills by player
    player_kills = Counter(k.get("attacker_name") for k in kills if k.get("attacker_name"))
    print()
    print("  Top fraggers:")
    for player, kill_count in player_kills.most_common(5):
        print(f"    {player}: {kill_count} kills")

    # Deaths by player
    player_deaths = Counter(k.get("victim_name") for k in kills)
    print()
    print("  Most deaths:")
    for player, death_count in player_deaths.most_common(5):
        print(f"    {player}: {death_count} deaths")

    # K/D ratio
    print()
    print("  K/D Ratios:")
    all_players = set(player_kills.keys()) | set(player_deaths.keys())
    kd_ratios = []
    for player in all_players:
        k = player_kills.get(player, 0)
        d = player_deaths.get(player, 0)
        kd = k / d if d > 0 else k
        kd_ratios.append((player, k, d, kd))

    kd_ratios.sort(key=lambda x: x[3], reverse=True)
    for player, k, d, kd in kd_ratios[:10]:
        print(f"    {player}: {k}/{d} ({kd:.2f})")

    # Headshot percentage
    headshots = sum(1 for k in kills if k.get("headshot"))
    hs_pct = (headshots / len(kills) * 100) if kills else 0
    print()
    print(f"  Headshot kills: {headshots} ({hs_pct:.1f}%)")

    # Weapon usage
    weapons = Counter(k.get("weapon") for k in kills)
    print()
    print("  Most used weapons (for kills):")
    for weapon, count in weapons.most_common(10):
        print(f"    {weapon}: {count}")

    # Special kills
    wallbangs = sum(1 for k in kills if k.get("penetrated"))
    noscopes = sum(1 for k in kills if k.get("noscope"))
    thrusmoke = sum(1 for k in kills if k.get("thrusmoke"))
    blind_kills = sum(1 for k in kills if k.get("attackerblind"))

    print()
    print("  Special kills:")
    print(f"    Wallbangs: {wallbangs}")
    print(f"    Noscopes: {noscopes}")
    print(f"    Through smoke: {thrusmoke}")
    print(f"    While blind: {blind_kills}")

    # 5. Damage Analysis
    damages = data.get("damages", [])
    print()
    print("[5] DAMAGE STATISTICS")
    print("-" * 40)
    print(f"  Total damage events: {len(damages)}")

    total_damage = sum(d.get("damage_health", 0) for d in damages)
    print(f"  Total damage dealt: {total_damage}")

    # Damage by player
    player_damage = {}
    for d in damages:
        attacker = d.get("attacker_name", "Unknown")
        dmg = d.get("damage_health", 0)
        player_damage[attacker] = player_damage.get(attacker, 0) + dmg

    print()
    print("  Top damage dealers:")
    for player, dmg in sorted(player_damage.items(), key=lambda x: -x[1])[:5]:
        adr = dmg / len(rounds) if rounds else dmg
        print(f"    {player}: {dmg} total ({adr:.1f} ADR)")

    # Hitgroup distribution
    hitgroups = {
        0: "Generic",
        1: "Head",
        2: "Chest",
        3: "Stomach",
        4: "Left Arm",
        5: "Right Arm",
        6: "Left Leg",
        7: "Right Leg",
    }
    hitgroup_counts = Counter(d.get("hitgroup", 0) for d in damages)
    print()
    print("  Hitgroup distribution:")
    for hg_id, count in hitgroup_counts.most_common():
        hg_name = hitgroups.get(hg_id, f"Unknown ({hg_id})")
        pct = count / len(damages) * 100 if damages else 0
        print(f"    {hg_name}: {count} ({pct:.1f}%)")

    # 6. Grenade Analysis
    grenades = data.get("grenades", [])
    print()
    print("[6] GRENADE USAGE")
    print("-" * 40)

    grenade_types = Counter(g.get("type") for g in grenades)
    for g_type, count in grenade_types.most_common():
        per_round = count / len(rounds) if rounds else 0
        print(f"  {g_type}: {count} ({per_round:.1f} per round)")

    # 7. Bomb Analysis
    bomb_events = data.get("bomb_events", [])
    print()
    print("[7] BOMB EVENTS")
    print("-" * 40)

    bomb_types = Counter(b.get("event_type") for b in bomb_events)
    for event_type, count in bomb_types.most_common():
        print(f"  {event_type}: {count}")

    # 8. Economy Analysis
    economy = data.get("economy", [])
    print()
    print("[8] ECONOMY ANALYSIS")
    print("-" * 40)

    if economy:
        # Average money per round by team
        team_money = {}
        for e in economy:
            team = e.get("team", "Unknown")
            money = e.get("money", 0)
            if team not in team_money:
                team_money[team] = []
            team_money[team].append(money)

        print("  Average starting money by team:")
        for team, money_list in team_money.items():
            avg = sum(money_list) / len(money_list) if money_list else 0
            print(f"    {team}: ${avg:.0f}")

    # 9. Advanced Metrics
    print()
    print("[9] ADVANCED METRICS")
    print("-" * 40)

    # First kills
    first_kills = {}
    for k in kills:
        round_num = k.get("round_num", 0)
        if round_num not in first_kills:
            first_kills[round_num] = k

    fk_players = Counter(fk.get("attacker_name") for fk in first_kills.values())
    print("  First kill leaders:")
    for player, count in fk_players.most_common(5):
        print(f"    {player}: {count} opening kills")

    # Kill distances
    distances = [k.get("distance") for k in kills if k.get("distance")]
    if distances:
        avg_dist = sum(distances) / len(distances)
        max_dist = max(distances)
        min_dist = min(distances)
        print()
        print(f"  Kill distances:")
        print(f"    Average: {avg_dist:.0f} units")
        print(f"    Longest: {max_dist:.0f} units")
        print(f"    Shortest: {min_dist:.0f} units")

    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    # Find JSON file
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]

    if not json_files:
        print("ERROR: No extracted data found!")
        print("Please run 03_extract_data.py first")
        sys.exit(1)

    json_path = os.path.join(data_dir, json_files[0])
    print(f"Loading data from: {json_path}")
    print()

    data = load_data(json_path)
    analyze_match(data)


if __name__ == "__main__":
    main()

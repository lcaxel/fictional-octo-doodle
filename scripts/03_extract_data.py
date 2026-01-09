#!/usr/bin/env python3
"""
Step 3: Extract all relevant data from CS2 demo.

This is the main extraction script that pulls out all data needed
for our Big Data analytics platform.
"""
import os
import sys
import json
from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np
from demoparser2 import DemoParser


class CS2DemoExtractor:
    """Extract comprehensive data from CS2 demo files."""

    def __init__(self, demo_path: str):
        self.demo_path = demo_path
        self.parser = DemoParser(demo_path)
        self.header = self.parser.parse_header()

    def extract_all(self) -> dict[str, Any]:
        """Extract all data from demo."""
        print(f"Extracting data from: {os.path.basename(self.demo_path)}")
        print("-" * 60)

        data = {
            "metadata": self._extract_metadata(),
            "players": self._extract_players(),
            "rounds": self._extract_rounds(),
            "kills": self._extract_kills(),
            "damages": self._extract_damages(),
            "grenades": self._extract_grenades(),
            "bomb_events": self._extract_bomb_events(),
            "economy": self._extract_economy(),
        }

        print("-" * 60)
        print("Extraction complete!")
        return data

    def _extract_metadata(self) -> dict:
        """Extract match metadata."""
        print("  [1/8] Extracting metadata...")

        metadata = {
            "demo_file": os.path.basename(self.demo_path),
            "map_name": self.header.get("map_name", "unknown"),
            "server_name": self.header.get("server_name", ""),
            "playback_time": self.header.get("playback_time", 0),
            "playback_ticks": self.header.get("playback_ticks", 0),
            "playback_frames": self.header.get("playback_frames", 0),
            "tickrate": self._calculate_tickrate(),
            "extracted_at": datetime.now().isoformat(),
        }

        return metadata

    def _calculate_tickrate(self) -> int:
        """Calculate server tickrate from header."""
        ticks = self.header.get("playback_ticks", 0)
        time = self.header.get("playback_time", 1)
        if time > 0:
            return round(ticks / time)
        return 64  # Default

    def _extract_players(self) -> list[dict]:
        """Extract player information."""
        print("  [2/8] Extracting players...")

        try:
            # Get player info from tick data
            tick_df = self.parser.parse_ticks(
                ["steamid", "name", "team_name"],
                ticks=[1000]  # Sample from early in match
            )

            players = []
            seen_steamids = set()

            for _, row in tick_df.iterrows():
                steamid = str(row.get("steamid", ""))
                if steamid and steamid not in seen_steamids:
                    seen_steamids.add(steamid)
                    players.append({
                        "steamid": steamid,
                        "name": row.get("name", "Unknown"),
                        "team": row.get("team_name", "Unknown"),
                    })

            return players
        except Exception as e:
            print(f"    Warning: Error extracting players: {e}")
            return []

    def _extract_rounds(self) -> list[dict]:
        """Extract round information."""
        print("  [3/8] Extracting rounds...")

        rounds = []
        try:
            # Round start events
            round_start_df = self.parser.parse_event("round_start")
            # Round end events
            round_end_df = self.parser.parse_event("round_end")

            for idx, row in round_end_df.iterrows():
                round_data = {
                    "round_num": idx + 1,
                    "tick": int(row.get("tick", 0)),
                    "winner": row.get("winner", None),
                    "reason": row.get("reason", None),
                    "message": row.get("message", ""),
                }
                rounds.append(round_data)

            print(f"    Found {len(rounds)} rounds")
        except Exception as e:
            print(f"    Warning: Error extracting rounds: {e}")

        return rounds

    def _extract_kills(self) -> list[dict]:
        """Extract kill events with full context."""
        print("  [4/8] Extracting kills...")

        kills = []
        try:
            # Parse kills with player data
            kills_df = self.parser.parse_event(
                "player_death",
                player=["X", "Y", "Z", "pitch", "yaw", "health", "team_name"],
                other=["total_rounds_played"]
            )

            for _, row in kills_df.iterrows():
                kill_data = {
                    "tick": int(row.get("tick", 0)),
                    "round_num": int(row.get("total_rounds_played", 0)) + 1,

                    # Attacker info
                    "attacker_steamid": str(row.get("attacker_steamid", "")),
                    "attacker_name": row.get("attacker_name", "World"),
                    "attacker_team": row.get("attacker_team_name", ""),
                    "attacker_x": _safe_float(row.get("attacker_X")),
                    "attacker_y": _safe_float(row.get("attacker_Y")),
                    "attacker_z": _safe_float(row.get("attacker_Z")),
                    "attacker_pitch": _safe_float(row.get("attacker_pitch")),
                    "attacker_yaw": _safe_float(row.get("attacker_yaw")),

                    # Victim info
                    "victim_steamid": str(row.get("user_steamid", "")),
                    "victim_name": row.get("user_name", "Unknown"),
                    "victim_team": row.get("user_team_name", ""),
                    "victim_x": _safe_float(row.get("user_X")),
                    "victim_y": _safe_float(row.get("user_Y")),
                    "victim_z": _safe_float(row.get("user_Z")),

                    # Kill details
                    "weapon": row.get("weapon", "unknown"),
                    "headshot": bool(row.get("headshot", False)),
                    "penetrated": int(row.get("penetrated", 0)) > 0,
                    "noscope": bool(row.get("noscope", False)),
                    "thrusmoke": bool(row.get("thrusmoke", False)),
                    "attackerblind": bool(row.get("attackerblind", False)),

                    # Assister
                    "assister_steamid": str(row.get("assister_steamid", "")),
                    "assister_name": row.get("assister_name", None),
                }

                # Calculate distance
                if all(kill_data[k] is not None for k in ["attacker_x", "attacker_y", "attacker_z",
                                                          "victim_x", "victim_y", "victim_z"]):
                    kill_data["distance"] = _calculate_distance(
                        kill_data["attacker_x"], kill_data["attacker_y"], kill_data["attacker_z"],
                        kill_data["victim_x"], kill_data["victim_y"], kill_data["victim_z"]
                    )
                else:
                    kill_data["distance"] = None

                kills.append(kill_data)

            print(f"    Found {len(kills)} kills")
        except Exception as e:
            print(f"    Warning: Error extracting kills: {e}")

        return kills

    def _extract_damages(self) -> list[dict]:
        """Extract damage events."""
        print("  [5/8] Extracting damages...")

        damages = []
        try:
            damage_df = self.parser.parse_event(
                "player_hurt",
                other=["total_rounds_played"]
            )

            for _, row in damage_df.iterrows():
                damage_data = {
                    "tick": int(row.get("tick", 0)),
                    "round_num": int(row.get("total_rounds_played", 0)) + 1,

                    "attacker_steamid": str(row.get("attacker_steamid", "")),
                    "attacker_name": row.get("attacker_name", "World"),
                    "victim_steamid": str(row.get("user_steamid", "")),
                    "victim_name": row.get("user_name", "Unknown"),

                    "weapon": row.get("weapon", "unknown"),
                    "damage_health": int(row.get("dmg_health", 0)),
                    "damage_armor": int(row.get("dmg_armor", 0)),
                    "hitgroup": int(row.get("hitgroup", 0)),
                    "health_remaining": int(row.get("health", 0)),
                }
                damages.append(damage_data)

            print(f"    Found {len(damages)} damage events")
        except Exception as e:
            print(f"    Warning: Error extracting damages: {e}")

        return damages

    def _extract_grenades(self) -> list[dict]:
        """Extract grenade events."""
        print("  [6/8] Extracting grenades...")

        grenades = []
        grenade_events = [
            ("hegrenade_detonate", "he"),
            ("flashbang_detonate", "flash"),
            ("smokegrenade_detonate", "smoke"),
            ("inferno_startburn", "molotov"),
            ("decoy_started", "decoy"),
        ]

        for event_name, grenade_type in grenade_events:
            try:
                df = self.parser.parse_event(
                    event_name,
                    other=["total_rounds_played"]
                )

                for _, row in df.iterrows():
                    grenade_data = {
                        "tick": int(row.get("tick", 0)),
                        "round_num": int(row.get("total_rounds_played", 0)) + 1,
                        "type": grenade_type,
                        "thrower_steamid": str(row.get("user_steamid", row.get("steamid", ""))),
                        "thrower_name": row.get("user_name", row.get("name", "Unknown")),
                        "x": _safe_float(row.get("x")),
                        "y": _safe_float(row.get("y")),
                        "z": _safe_float(row.get("z")),
                    }
                    grenades.append(grenade_data)
            except Exception:
                pass  # Event might not exist in this demo

        print(f"    Found {len(grenades)} grenade events")
        return grenades

    def _extract_bomb_events(self) -> list[dict]:
        """Extract bomb-related events."""
        print("  [7/8] Extracting bomb events...")

        bomb_events = []
        event_types = [
            ("bomb_planted", "plant"),
            ("bomb_defused", "defuse"),
            ("bomb_exploded", "explode"),
            ("bomb_dropped", "drop"),
            ("bomb_pickup", "pickup"),
        ]

        for event_name, event_type in event_types:
            try:
                df = self.parser.parse_event(
                    event_name,
                    other=["total_rounds_played"]
                )

                for _, row in df.iterrows():
                    bomb_data = {
                        "tick": int(row.get("tick", 0)),
                        "round_num": int(row.get("total_rounds_played", 0)) + 1,
                        "event_type": event_type,
                        "player_steamid": str(row.get("user_steamid", row.get("steamid", ""))),
                        "player_name": row.get("user_name", row.get("name", "Unknown")),
                        "x": _safe_float(row.get("x")),
                        "y": _safe_float(row.get("y")),
                        "site": row.get("site", None),
                    }
                    bomb_events.append(bomb_data)
            except Exception:
                pass

        print(f"    Found {len(bomb_events)} bomb events")
        return bomb_events

    def _extract_economy(self) -> list[dict]:
        """Extract economy snapshots at round starts."""
        print("  [8/8] Extracting economy...")

        economy = []
        try:
            # Get round start ticks
            round_start_df = self.parser.parse_event("round_freeze_end")

            if len(round_start_df) == 0:
                round_start_df = self.parser.parse_event("round_start")

            for idx, row in round_start_df.iterrows():
                tick = int(row.get("tick", 0))
                round_num = idx + 1

                # Get player economy at this tick
                try:
                    tick_df = self.parser.parse_ticks(
                        ["steamid", "name", "team_name", "money", "armor_value",
                         "has_helmet", "has_defuser", "active_weapon_name"],
                        ticks=[tick + 10]  # Slightly after round start
                    )

                    for _, player_row in tick_df.iterrows():
                        economy.append({
                            "round_num": round_num,
                            "tick": tick,
                            "steamid": str(player_row.get("steamid", "")),
                            "name": player_row.get("name", "Unknown"),
                            "team": player_row.get("team_name", "Unknown"),
                            "money": int(player_row.get("money", 0)),
                            "armor": int(player_row.get("armor_value", 0)),
                            "has_helmet": bool(player_row.get("has_helmet", False)),
                            "has_defuser": bool(player_row.get("has_defuser", False)),
                            "weapon": player_row.get("active_weapon_name", ""),
                        })
                except Exception:
                    pass

            print(f"    Found {len(economy)} economy snapshots")
        except Exception as e:
            print(f"    Warning: Error extracting economy: {e}")

        return economy


def _safe_float(value) -> float | None:
    """Safely convert value to float."""
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _calculate_distance(x1, y1, z1, x2, y2, z2) -> float:
    """Calculate 3D distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5


def find_demo_file(demos_dir: str) -> str | None:
    """Find any .dem file in the demos directory."""
    if not os.path.exists(demos_dir):
        return None
    for f in os.listdir(demos_dir):
        if f.endswith('.dem'):
            return os.path.join(demos_dir, f)
    return None


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demos_dir = os.path.join(base_dir, 'demos')
    data_dir = os.path.join(base_dir, 'data')

    # Find demo
    demo_path = find_demo_file(demos_dir)
    if not demo_path:
        print("ERROR: No .dem file found!")
        print(f"Please place a CS2 demo in: {os.path.abspath(demos_dir)}")
        sys.exit(1)

    # Extract data
    extractor = CS2DemoExtractor(demo_path)
    data = extractor.extract_all()

    # Create output directory
    os.makedirs(data_dir, exist_ok=True)

    # Save as JSON
    demo_name = os.path.splitext(os.path.basename(demo_path))[0]
    json_path = os.path.join(data_dir, f"{demo_name}.json")

    print()
    print(f"Saving to: {json_path}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Also save individual CSV files for easy viewing
    csv_dir = os.path.join(data_dir, demo_name)
    os.makedirs(csv_dir, exist_ok=True)

    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            df = pd.DataFrame(value)
            csv_path = os.path.join(csv_dir, f"{key}.csv")
            df.to_csv(csv_path, index=False)
            print(f"  Saved {key}.csv ({len(df)} rows)")

    print()
    print("=" * 60)
    print("DATA EXTRACTION COMPLETE!")
    print("=" * 60)
    print()
    print("Output files:")
    print(f"  JSON: {json_path}")
    print(f"  CSVs: {csv_dir}/")
    print()
    print("Next step: Run 04_analyze_data.py to see statistics")


if __name__ == "__main__":
    main()

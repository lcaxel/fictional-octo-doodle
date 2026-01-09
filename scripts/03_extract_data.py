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


# Constants
TRADE_KILL_WINDOW_TICKS = 320  # ~5 seconds at 64 tick
TICKRATE = 64


class CS2DemoExtractor:
    """Extract comprehensive data from CS2 demo files."""

    def __init__(self, demo_path: str):
        self.demo_path = demo_path
        self.parser = DemoParser(demo_path)
        self.header = self.parser.parse_header()
        self.tickrate = self._calculate_tickrate()

    def extract_all(self) -> dict[str, Any]:
        """Extract all data from demo."""
        print(f"Extracting data from: {os.path.basename(self.demo_path)}")
        print("-" * 60)

        # Extract raw data
        metadata = self._extract_metadata()
        players = self._extract_players()
        rounds = self._extract_rounds()
        kills = self._extract_kills()
        damages = self._extract_damages()
        grenades = self._extract_grenades()
        bomb_events = self._extract_bomb_events()
        economy = self._extract_economy()

        # Calculate advanced metrics
        print("  [9/12] Calculating trade kills...")
        kills = self._add_trade_kills(kills)
        print(f"    Found {sum(1 for k in kills if k.get('is_trade'))} trade kills")

        print("  [10/12] Calculating first kills per round...")
        round_stats = self._calculate_round_stats(kills, rounds)
        print(f"    Calculated stats for {len(round_stats)} rounds")

        print("  [11/12] Detecting clutch situations...")
        clutches = self._detect_clutches(kills, rounds)
        print(f"    Found {len(clutches)} clutch situations")

        print("  [12/12] Calculating player stats (ADR, KAST)...")
        player_stats = self._calculate_player_stats(players, kills, damages, rounds, clutches)

        print("-" * 60)
        print("Extraction complete!")

        return {
            "metadata": metadata,
            "players": players,
            "player_stats": player_stats,
            "rounds": rounds,
            "round_stats": round_stats,
            "kills": kills,
            "damages": damages,
            "grenades": grenades,
            "bomb_events": bomb_events,
            "economy": economy,
            "clutches": clutches,
        }

    def _extract_metadata(self) -> dict:
        """Extract match metadata."""
        print("  [1/12] Extracting metadata...")

        # Get last tick to calculate duration
        try:
            round_end_df = self.parser.parse_event("round_end")
            last_tick = int(round_end_df['tick'].max()) if len(round_end_df) > 0 else 0
            duration_seconds = last_tick / self.tickrate if self.tickrate > 0 else 0
        except:
            last_tick = 0
            duration_seconds = 0

        metadata = {
            "demo_file": os.path.basename(self.demo_path),
            "map_name": self.header.get("map_name", "unknown"),
            "server_name": self.header.get("server_name", ""),
            "duration_seconds": round(duration_seconds),
            "duration_formatted": f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}",
            "total_ticks": last_tick,
            "tickrate": self.tickrate,
            "extracted_at": datetime.now().isoformat(),
        }

        return metadata

    def _calculate_tickrate(self) -> int:
        """Calculate server tickrate."""
        # CS2 uses 64 tick for demos (sub-tick is internal)
        return 64

    def _extract_players(self) -> list[dict]:
        """Extract player information."""
        print("  [2/12] Extracting players...")

        try:
            # Get player info from multiple ticks to ensure we catch everyone
            tick_df = self.parser.parse_ticks(
                ["steamid", "name", "team_name"],
                ticks=[5000, 10000, 20000]
            )

            players = []
            seen_steamids = set()

            for _, row in tick_df.iterrows():
                steamid = str(row.get("steamid", ""))
                if steamid and steamid not in seen_steamids and steamid != "0":
                    seen_steamids.add(steamid)
                    players.append({
                        "steamid": steamid,
                        "name": row.get("name", "Unknown"),
                        "team": row.get("team_name", "Unknown"),
                    })

            print(f"    Found {len(players)} players")
            return players
        except Exception as e:
            print(f"    Warning: Error extracting players: {e}")
            return []

    def _extract_rounds(self) -> list[dict]:
        """Extract round information."""
        print("  [3/12] Extracting rounds...")

        rounds = []
        try:
            round_end_df = self.parser.parse_event("round_end")
            round_start_df = self.parser.parse_event("round_freeze_end")

            for idx, row in round_end_df.iterrows():
                start_tick = int(round_start_df.iloc[idx]['tick']) if idx < len(round_start_df) else 0
                end_tick = int(row.get("tick", 0))

                round_data = {
                    "round_num": idx + 1,
                    "start_tick": start_tick,
                    "end_tick": end_tick,
                    "duration_seconds": round((end_tick - start_tick) / self.tickrate, 1),
                    "winner": row.get("winner", None),
                    "reason": row.get("reason", None),
                }
                rounds.append(round_data)

            print(f"    Found {len(rounds)} rounds")
        except Exception as e:
            print(f"    Warning: Error extracting rounds: {e}")

        return rounds

    def _extract_kills(self) -> list[dict]:
        """Extract kill events with full context."""
        print("  [4/12] Extracting kills...")

        kills = []
        try:
            kills_df = self.parser.parse_event(
                "player_death",
                player=["X", "Y", "Z", "pitch", "yaw", "health", "team_name"],
                other=["total_rounds_played"]
            )

            for idx, row in kills_df.iterrows():
                kill_data = {
                    "kill_id": idx,
                    "tick": int(row.get("tick", 0)),
                    "round_num": int(row.get("total_rounds_played", 0)) + 1,

                    # Attacker info
                    "attacker_steamid": str(row.get("attacker_steamid", "")),
                    "attacker_name": row.get("attacker_name", "World"),
                    "attacker_team": row.get("attacker_team_name", ""),
                    "attacker_x": _safe_float(row.get("attacker_X")),
                    "attacker_y": _safe_float(row.get("attacker_Y")),
                    "attacker_z": _safe_float(row.get("attacker_Z")),

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
                    "assistedflash": bool(row.get("assistedflash", False)),

                    # Assister
                    "assister_steamid": str(row.get("assister_steamid", "") or ""),
                    "assister_name": row.get("assister_name", None),

                    # Will be calculated later
                    "is_first_kill": False,
                    "is_trade": False,
                    "traded_kill_id": None,
                }

                # Calculate distance
                if all(kill_data[k] is not None for k in ["attacker_x", "attacker_y", "attacker_z",
                                                          "victim_x", "victim_y", "victim_z"]):
                    kill_data["distance"] = round(_calculate_distance(
                        kill_data["attacker_x"], kill_data["attacker_y"], kill_data["attacker_z"],
                        kill_data["victim_x"], kill_data["victim_y"], kill_data["victim_z"]
                    ), 1)
                else:
                    kill_data["distance"] = None

                kills.append(kill_data)

            print(f"    Found {len(kills)} kills")
        except Exception as e:
            print(f"    Warning: Error extracting kills: {e}")

        return kills

    def _extract_damages(self) -> list[dict]:
        """Extract damage events."""
        print("  [5/12] Extracting damages...")

        damages = []
        try:
            damage_df = self.parser.parse_event(
                "player_hurt",
                other=["total_rounds_played"]
            )

            for _, row in damage_df.iterrows():
                # hitgroup is a string in CS2, not int
                hitgroup = row.get("hitgroup", "generic")
                if not isinstance(hitgroup, str):
                    hitgroup = str(hitgroup)

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
                    "hitgroup": hitgroup,
                    "health_remaining": int(row.get("health", 0)),
                    "armor_remaining": int(row.get("armor", 0)),
                }
                damages.append(damage_data)

            print(f"    Found {len(damages)} damage events")
        except Exception as e:
            print(f"    Warning: Error extracting damages: {e}")

        return damages

    def _extract_grenades(self) -> list[dict]:
        """Extract grenade events."""
        print("  [6/12] Extracting grenades...")

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
                pass

        print(f"    Found {len(grenades)} grenade events")
        return grenades

    def _extract_bomb_events(self) -> list[dict]:
        """Extract bomb-related events."""
        print("  [7/12] Extracting bomb events...")

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
        print("  [8/12] Extracting economy...")

        economy = []
        try:
            round_freeze_end = self.parser.parse_event("round_freeze_end")

            for idx, row in round_freeze_end.iterrows():
                tick = int(row.get("tick", 0))
                round_num = idx + 1

                try:
                    tick_df = self.parser.parse_ticks(
                        ["steamid", "name", "team_name", "current_equip_value",
                         "total_cash_spent", "cash_spent_this_round"],
                        ticks=[tick]
                    )

                    for _, player_row in tick_df.iterrows():
                        steamid = str(player_row.get("steamid", ""))
                        if steamid and steamid != "0":
                            economy.append({
                                "round_num": round_num,
                                "tick": tick,
                                "steamid": steamid,
                                "name": player_row.get("name", "Unknown"),
                                "team": player_row.get("team_name", "Unknown"),
                                "equipment_value": int(player_row.get("current_equip_value", 0)),
                                "cash_spent_round": int(player_row.get("cash_spent_this_round", 0)),
                                "total_cash_spent": int(player_row.get("total_cash_spent", 0)),
                            })
                except Exception:
                    pass

            print(f"    Found {len(economy)} economy snapshots")
        except Exception as e:
            print(f"    Warning: Error extracting economy: {e}")

        return economy

    def _add_trade_kills(self, kills: list[dict]) -> list[dict]:
        """Identify trade kills (killing enemy within 5 sec of teammate death)."""
        for i, kill in enumerate(kills):
            kill_tick = kill["tick"]
            kill_round = kill["round_num"]
            attacker_team = kill["attacker_team"]
            victim_team = kill["victim_team"]

            # Look back for teammate deaths in the same round
            for j in range(i - 1, -1, -1):
                prev_kill = kills[j]
                if prev_kill["round_num"] != kill_round:
                    break

                tick_diff = kill_tick - prev_kill["tick"]
                if tick_diff > TRADE_KILL_WINDOW_TICKS:
                    break

                # Check if previous kill was a teammate dying
                # (enemy killed our teammate, now we kill the enemy)
                if (prev_kill["victim_team"] == attacker_team and
                    prev_kill["attacker_steamid"] == kill["victim_steamid"]):
                    kill["is_trade"] = True
                    kill["traded_kill_id"] = prev_kill["kill_id"]
                    kill["trade_time_ticks"] = tick_diff
                    break

        return kills

    def _calculate_round_stats(self, kills: list[dict], rounds: list[dict]) -> list[dict]:
        """Calculate first kill, first death, etc. per round."""
        round_stats = []

        for rnd in rounds:
            round_num = rnd["round_num"]
            round_kills = [k for k in kills if k["round_num"] == round_num]

            if round_kills:
                first_kill = round_kills[0]

                # Mark first kill in the kills list
                for k in kills:
                    if k["kill_id"] == first_kill["kill_id"]:
                        k["is_first_kill"] = True
                        break

                round_stats.append({
                    "round_num": round_num,
                    "winner": rnd["winner"],
                    "reason": rnd["reason"],
                    "duration_seconds": rnd["duration_seconds"],
                    "total_kills": len(round_kills),
                    "first_kill_tick": first_kill["tick"],
                    "first_kill_attacker": first_kill["attacker_name"],
                    "first_kill_attacker_steamid": first_kill["attacker_steamid"],
                    "first_kill_attacker_team": first_kill["attacker_team"],
                    "first_kill_victim": first_kill["victim_name"],
                    "first_kill_victim_steamid": first_kill["victim_steamid"],
                    "first_kill_weapon": first_kill["weapon"],
                    "first_kill_team_won": first_kill["attacker_team"] == rnd["winner"],
                })
            else:
                round_stats.append({
                    "round_num": round_num,
                    "winner": rnd["winner"],
                    "reason": rnd["reason"],
                    "duration_seconds": rnd["duration_seconds"],
                    "total_kills": 0,
                    "first_kill_tick": None,
                    "first_kill_attacker": None,
                    "first_kill_attacker_steamid": None,
                    "first_kill_attacker_team": None,
                    "first_kill_victim": None,
                    "first_kill_victim_steamid": None,
                    "first_kill_weapon": None,
                    "first_kill_team_won": None,
                })

        return round_stats

    def _detect_clutches(self, kills: list[dict], rounds: list[dict]) -> list[dict]:
        """Detect clutch situations (1vX)."""
        clutches = []

        for rnd in rounds:
            round_num = rnd["round_num"]
            round_kills = sorted([k for k in kills if k["round_num"] == round_num],
                                key=lambda x: x["tick"])

            if len(round_kills) < 2:
                continue

            # Track alive players
            ct_alive = set()
            t_alive = set()

            # Initialize teams from first kill
            for k in round_kills:
                if k["attacker_team"] == "CT":
                    ct_alive.add(k["attacker_steamid"])
                elif k["attacker_team"] == "TERRORIST":
                    t_alive.add(k["attacker_steamid"])
                if k["victim_team"] == "CT":
                    ct_alive.add(k["victim_steamid"])
                elif k["victim_team"] == "TERRORIST":
                    t_alive.add(k["victim_steamid"])

            # Reset and simulate round
            ct_alive_count = 5
            t_alive_count = 5
            clutch_started = False
            clutch_player = None
            clutch_team = None
            clutch_vs = 0
            clutch_start_tick = 0

            for k in round_kills:
                if k["victim_team"] == "CT":
                    ct_alive_count -= 1
                elif k["victim_team"] == "TERRORIST":
                    t_alive_count -= 1

                # Check for 1vX situation
                if not clutch_started:
                    if ct_alive_count == 1 and t_alive_count >= 1:
                        clutch_started = True
                        clutch_team = "CT"
                        clutch_vs = t_alive_count
                        clutch_start_tick = k["tick"]
                        # Find the remaining CT player
                        for kill in round_kills:
                            if kill["attacker_team"] == "CT" and kill["tick"] >= k["tick"]:
                                clutch_player = kill["attacker_steamid"]
                                clutch_player_name = kill["attacker_name"]
                                break
                    elif t_alive_count == 1 and ct_alive_count >= 1:
                        clutch_started = True
                        clutch_team = "TERRORIST"
                        clutch_vs = ct_alive_count
                        clutch_start_tick = k["tick"]
                        for kill in round_kills:
                            if kill["attacker_team"] == "TERRORIST" and kill["tick"] >= k["tick"]:
                                clutch_player = kill["attacker_steamid"]
                                clutch_player_name = kill["attacker_name"]
                                break

            if clutch_started and clutch_player and clutch_vs >= 2:
                clutch_won = rnd["winner"] == clutch_team
                clutches.append({
                    "round_num": round_num,
                    "player_steamid": clutch_player,
                    "player_name": clutch_player_name,
                    "player_team": clutch_team,
                    "clutch_type": f"1v{clutch_vs}",
                    "opponents": clutch_vs,
                    "won": clutch_won,
                    "start_tick": clutch_start_tick,
                })

        return clutches

    def _calculate_player_stats(self, players: list[dict], kills: list[dict],
                                damages: list[dict], rounds: list[dict],
                                clutches: list[dict]) -> list[dict]:
        """Calculate comprehensive player statistics."""
        num_rounds = len(rounds)
        if num_rounds == 0:
            return []

        player_stats = []

        for player in players:
            steamid = player["steamid"]
            name = player["name"]
            team = player["team"]

            # Basic stats
            player_kills = [k for k in kills if k["attacker_steamid"] == steamid]
            player_deaths = [k for k in kills if k["victim_steamid"] == steamid]
            player_assists = [k for k in kills if k.get("assister_steamid") == steamid]

            k = len(player_kills)
            d = len(player_deaths)
            a = len(player_assists)

            # Damage stats
            player_damage = [dmg for dmg in damages if dmg["attacker_steamid"] == steamid]
            total_damage = sum(dmg["damage_health"] for dmg in player_damage)
            adr = round(total_damage / num_rounds, 1) if num_rounds > 0 else 0

            # Headshots
            headshots = sum(1 for kill in player_kills if kill["headshot"])
            hs_pct = round(headshots / k * 100, 1) if k > 0 else 0

            # Trade kills
            trade_kills = sum(1 for kill in player_kills if kill["is_trade"])

            # First kills / First deaths
            first_kills = sum(1 for kill in player_kills if kill["is_first_kill"])
            first_deaths = sum(1 for kill in player_deaths if kill["is_first_kill"])

            # Clutches
            player_clutches = [c for c in clutches if c["player_steamid"] == steamid]
            clutch_attempts = len(player_clutches)
            clutch_wins = sum(1 for c in player_clutches if c["won"])

            # KAST calculation (simplified)
            # K = round with kill, A = round with assist, S = survived, T = traded
            rounds_with_contribution = set()

            for kill in player_kills:
                rounds_with_contribution.add(kill["round_num"])
            for kill in player_assists:
                rounds_with_contribution.add(kill["round_num"])

            # Survived rounds (not killed)
            death_rounds = set(kill["round_num"] for kill in player_deaths)
            for rnd in rounds:
                if rnd["round_num"] not in death_rounds:
                    rounds_with_contribution.add(rnd["round_num"])

            # Traded deaths
            for death in player_deaths:
                # Check if death was traded
                death_tick = death["tick"]
                death_round = death["round_num"]
                for kill in kills:
                    if (kill["round_num"] == death_round and
                        kill["tick"] > death_tick and
                        kill["tick"] - death_tick <= TRADE_KILL_WINDOW_TICKS and
                        kill["attacker_team"] == team):
                        rounds_with_contribution.add(death_round)
                        break

            kast = round(len(rounds_with_contribution) / num_rounds * 100, 1) if num_rounds > 0 else 0

            # K/D ratio
            kd_ratio = round(k / d, 2) if d > 0 else float(k)

            # Flash assists
            flash_assists = sum(1 for kill in kills if kill.get("assister_steamid") == steamid and kill.get("assistedflash"))

            player_stats.append({
                "steamid": steamid,
                "name": name,
                "team": team,
                "kills": k,
                "deaths": d,
                "assists": a,
                "kd_ratio": kd_ratio,
                "adr": adr,
                "kast": kast,
                "headshots": headshots,
                "hs_percentage": hs_pct,
                "first_kills": first_kills,
                "first_deaths": first_deaths,
                "fk_fd_diff": first_kills - first_deaths,
                "trade_kills": trade_kills,
                "flash_assists": flash_assists,
                "clutch_attempts": clutch_attempts,
                "clutch_wins": clutch_wins,
                "clutch_rate": round(clutch_wins / clutch_attempts * 100, 1) if clutch_attempts > 0 else 0,
                "total_damage": total_damage,
            })

        # Sort by ADR
        player_stats.sort(key=lambda x: x["adr"], reverse=True)

        return player_stats


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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demos_dir = os.path.join(base_dir, 'demos')
    data_dir = os.path.join(base_dir, 'data')

    demo_path = find_demo_file(demos_dir)
    if not demo_path:
        print("ERROR: No .dem file found!")
        print(f"Please place a CS2 demo in: {os.path.abspath(demos_dir)}")
        sys.exit(1)

    extractor = CS2DemoExtractor(demo_path)
    data = extractor.extract_all()

    os.makedirs(data_dir, exist_ok=True)

    demo_name = os.path.splitext(os.path.basename(demo_path))[0]
    json_path = os.path.join(data_dir, f"{demo_name}.json")

    print()
    print(f"Saving to: {json_path}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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

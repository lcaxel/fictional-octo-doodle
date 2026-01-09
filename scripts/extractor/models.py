"""
Data models for CS2 Demo Extraction.
Defines all data structures for the Big Data platform.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class MatchMetadata:
    """Match-level metadata."""
    match_id: str
    demo_file: str
    map_name: str
    server_name: str
    duration_seconds: int
    duration_formatted: str
    total_ticks: int
    tickrate: int
    total_rounds: int
    score_team1: int
    score_team2: int
    team1_name: str
    team2_name: str
    team1_side_first: str  # CT or T
    winner: str
    extracted_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Player:
    """Player information."""
    steamid: str
    name: str
    team: str
    clan_name: str = ""
    crosshair_code: str = ""


@dataclass
class Kill:
    """Comprehensive kill event with 79 fields from demoparser2."""
    kill_id: int
    tick: int
    round_num: int

    # Attacker
    attacker_steamid: str
    attacker_name: str
    attacker_team: str
    attacker_x: Optional[float]
    attacker_y: Optional[float]
    attacker_z: Optional[float]
    attacker_pitch: Optional[float]
    attacker_yaw: Optional[float]
    attacker_health: int
    attacker_armor: int
    attacker_location: str  # last_place_name
    attacker_weapon: str  # active weapon at kill time
    attacker_is_scoped: bool
    attacker_is_walking: bool
    attacker_is_airborne: bool
    attacker_flash_duration: float
    attacker_accuracy_penalty: float
    attacker_shots_fired: int

    # Victim
    victim_steamid: str
    victim_name: str
    victim_team: str
    victim_x: Optional[float]
    victim_y: Optional[float]
    victim_z: Optional[float]
    victim_pitch: Optional[float]
    victim_yaw: Optional[float]
    victim_health: int  # Health before death (usually damage dealt)
    victim_armor: int
    victim_location: str
    victim_weapon: str
    victim_is_scoped: bool
    victim_is_walking: bool
    victim_is_airborne: bool
    victim_flash_duration: float  # Was victim flashed?
    victim_accuracy_penalty: float
    victim_shots_fired: int

    # Assister
    assister_steamid: Optional[str]
    assister_name: Optional[str]
    assister_flash_duration: float = 0.0  # Flash assist?

    # Kill details
    weapon: str
    headshot: bool
    penetrated: bool
    noscope: bool
    thrusmoke: bool
    attackerblind: bool
    assistedflash: bool
    dominated: bool
    revenge: bool
    wipe: bool  # Team wipe

    # Damage info
    dmg_health: int
    dmg_armor: int
    hitgroup: str
    distance: Optional[float]

    # Calculated fields
    is_first_kill: bool = False
    is_trade: bool = False
    trade_time_ms: Optional[int] = None
    is_entry: bool = False  # Entry frag (first contact)
    is_clutch_kill: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Damage:
    """Damage event."""
    tick: int
    round_num: int

    attacker_steamid: str
    attacker_name: str
    attacker_team: str

    victim_steamid: str
    victim_name: str
    victim_team: str

    weapon: str
    damage_health: int
    damage_armor: int
    hitgroup: str
    health_remaining: int
    armor_remaining: int

    # Source of damage
    is_grenade_damage: bool = False
    grenade_type: Optional[str] = None  # he, molotov, inferno


@dataclass
class Shot:
    """Weapon fire event for accuracy tracking."""
    tick: int
    round_num: int
    steamid: str
    player_name: str
    weapon: str
    silenced: bool

    # Position at shot time (if available)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    # Did this shot hit? (calculated by matching with damage events)
    hit: bool = False
    hit_steamid: Optional[str] = None
    hitgroup: Optional[str] = None


@dataclass
class Grenade:
    """Grenade event with full trajectory."""
    grenade_id: int
    round_num: int
    grenade_type: str  # smoke, flash, he, molotov, decoy

    thrower_steamid: str
    thrower_name: str
    thrower_team: str

    # Throw position
    throw_tick: int
    throw_x: Optional[float] = None
    throw_y: Optional[float] = None
    throw_z: Optional[float] = None

    # Detonate position
    detonate_tick: int = 0
    detonate_x: Optional[float] = None
    detonate_y: Optional[float] = None
    detonate_z: Optional[float] = None

    # Effect
    duration_ticks: int = 0

    # For flashes
    enemies_flashed: int = 0
    teammates_flashed: int = 0
    total_blind_duration: float = 0.0

    # For HE/Molotov
    damage_dealt: int = 0
    enemies_damaged: int = 0


@dataclass
class FlashEffect:
    """Individual flash blind effect on a player."""
    tick: int
    round_num: int

    thrower_steamid: str
    thrower_name: str
    thrower_team: str

    victim_steamid: str
    victim_name: str
    victim_team: str

    blind_duration: float
    is_teammate: bool

    # Did this lead to a kill?
    resulted_in_kill: bool = False
    kill_tick: Optional[int] = None


@dataclass
class BombEvent:
    """Bomb-related event."""
    tick: int
    round_num: int
    event_type: str  # plant, defuse, explode, drop, pickup

    player_steamid: str
    player_name: str
    player_team: str

    x: Optional[float]
    y: Optional[float]
    site: Optional[str]  # A or B

    # For defuse
    time_remaining_ms: Optional[int] = None
    had_kit: bool = False


@dataclass
class Round:
    """Round information."""
    round_num: int
    start_tick: int
    end_tick: int
    freeze_end_tick: int
    duration_seconds: float

    winner: str  # CT or T
    win_reason: str  # elimination, bomb_exploded, bomb_defused, time

    # Score after round
    ct_score: int
    t_score: int

    # Economy
    ct_equipment_value: int
    t_equipment_value: int
    ct_buy_type: str  # full, force, eco, half, pistol
    t_buy_type: str

    # First engagement
    first_kill_tick: Optional[int]
    first_kill_attacker_steamid: Optional[str]
    first_kill_attacker_team: Optional[str]
    first_kill_victim_steamid: Optional[str]
    first_kill_weapon: Optional[str]
    first_kill_won_round: Optional[bool]

    # Kills summary
    total_kills: int
    ct_kills: int
    t_kills: int

    # Special situations
    bomb_planted: bool = False
    bomb_plant_tick: Optional[int] = None
    bomb_site: Optional[str] = None

    clutch_player_steamid: Optional[str] = None
    clutch_type: Optional[str] = None  # 1v1, 1v2, etc.
    clutch_won: Optional[bool] = None


@dataclass
class Economy:
    """Economy snapshot per player per round."""
    round_num: int
    tick: int
    phase: str  # round_start, round_end

    steamid: str
    player_name: str
    team: str

    equipment_value: int
    cash_spent_this_round: int
    total_cash_spent: int

    # Loadout
    primary_weapon: Optional[str]
    secondary_weapon: Optional[str]
    has_armor: bool
    has_helmet: bool
    has_defuser: bool
    grenades: list = field(default_factory=list)

    # Calculated
    buy_type: str = ""  # full, force, eco, half


@dataclass
class PlayerRoundStats:
    """Per-player per-round statistics."""
    round_num: int
    steamid: str
    player_name: str
    team: str

    # Performance
    kills: int
    deaths: int
    assists: int
    damage: int

    # Special events
    headshots: int
    first_kill: bool
    first_death: bool
    clutch_attempt: bool
    clutch_won: bool

    # Multi-kills
    multi_kill: int  # 0, 2, 3, 4, 5

    # Survival
    survived: bool
    traded_death: bool  # If died, was it traded?

    # Entry
    entry_attempt: bool
    entry_success: bool

    # Utility
    enemies_flashed: int
    flash_assists: int
    utility_damage: int


@dataclass
class PlayerMatchStats:
    """Comprehensive player statistics for entire match."""
    steamid: str
    name: str
    team: str

    # Basic
    kills: int
    deaths: int
    assists: int
    kd_ratio: float

    # Damage
    total_damage: int
    adr: float
    utility_damage: int

    # Accuracy
    shots_fired: int
    shots_hit: int
    accuracy: float
    headshot_kills: int
    hs_percentage: float

    # Entry
    first_kills: int
    first_deaths: int
    fk_fd_diff: int
    entry_attempts: int
    entry_success_rate: float

    # Trading
    trade_kills: int
    traded_deaths: int  # Deaths that were traded by teammates

    # Clutches
    clutch_attempts: int
    clutch_wins: int
    clutch_rate: float

    # Multi-kills
    double_kills: int  # 2k
    triple_kills: int  # 3k
    quad_kills: int    # 4k
    aces: int          # 5k

    # Utility
    flashes_thrown: int
    enemies_flashed: int
    flash_assists: int
    avg_flash_duration: float
    teammates_flashed: int

    smokes_thrown: int
    molotovs_thrown: int
    he_thrown: int
    he_damage: int
    molotov_damage: int

    # Economy
    avg_equipment_value: float
    total_money_spent: int

    # KAST
    kast: float
    kast_rounds: int

    # Impact (calculated)
    impact_rating: float

    # Rounds played
    rounds_played: int
    rounds_won: int
    rounds_with_kill: int
    rounds_survived: int


@dataclass
class Clutch:
    """Clutch situation."""
    round_num: int

    player_steamid: str
    player_name: str
    player_team: str

    clutch_type: str  # 1v1, 1v2, 1v3, 1v4, 1v5
    opponents: int

    start_tick: int
    end_tick: int
    duration_seconds: float

    won: bool

    # How it ended
    kills_made: int
    bomb_planted: bool
    bomb_defused: bool

    # Health at start
    hp_at_start: int


@dataclass
class Duel:
    """Individual duel (1v1 engagement)."""
    round_num: int
    tick: int

    player1_steamid: str
    player1_name: str
    player1_team: str
    player1_weapon: str
    player1_hp_before: int

    player2_steamid: str
    player2_name: str
    player2_team: str
    player2_weapon: str
    player2_hp_before: int

    winner_steamid: str
    winner_hp_after: int

    # Context
    is_opening_duel: bool
    is_awp_duel: bool  # Both had AWP
    is_pistol_round: bool

    distance: float
    headshot: bool

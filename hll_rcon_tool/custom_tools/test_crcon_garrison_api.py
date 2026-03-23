"""
test_crcon_garrison_api.py

Diagnostic helper for CRCON's detailed player info payload.

Run this inside the CRCON environment to inspect the shape returned by
`get_detailed_player_info` and verify which key contains built garrisons.
"""

from pprint import pformat

from rcon.rcon import Rcon


def extract_garrisons_built(details: dict) -> int:
    """
    Returns the garrisons built count from detailed player info.
    """
    candidate_paths = [
        ("garrisons_built",),
        ("garrison_built",),
        ("built_garrisons",),
        ("num_garrisons_built",),
        ("statistics", "garrisons_built"),
        ("statistics", "garrison_built"),
        ("statistics", "built_garrisons"),
        ("stats", "garrisons_built"),
        ("stats", "garrison_built"),
        ("stats", "built_garrisons"),
        ("player", "garrisons_built"),
        ("player", "garrison_built"),
        ("player", "built_garrisons"),
    ]

    for path in candidate_paths:
        current = details
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current is not None:
            try:
                return int(current)
            except (TypeError, ValueError):
                return 0

    return 0


def flatten_keys(data, prefix=""):
    """
    Returns dotted keys for nested dict inspection.
    """
    keys = []
    if not isinstance(data, dict):
        return keys

    for key, value in data.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        keys.append(dotted)
        if isinstance(value, dict):
            keys.extend(flatten_keys(value, dotted))
    return keys


def collect_infantry_players(rcon: Rcon) -> list[dict]:
    """
    Collects infantry and recon players from team view.
    """
    team_view = rcon.get_team_view()
    players = []

    for team in ("allies", "axis"):
        if team not in team_view:
            continue

        for squad_name, squad_data in team_view[team]["squads"].items():
            if squad_data["type"] not in ("infantry", "recon"):
                continue

            for player in squad_data["players"]:
                players.append(
                    {
                        "team": team,
                        "squad": squad_name,
                        "name": player.get("name"),
                        "player_id": player.get("player_id"),
                    }
                )

    return players


def main():
    rcon = Rcon()
    players = collect_infantry_players(rcon)

    if not players:
        print("No infantry players found in current team view.")
        return

    print(f"Found {len(players)} infantry/recon players.")

    for player in players:
        player_id = player["player_id"]
        if not player_id:
            print(f"Skipping {player['name']} because player_id is missing.")
            continue

        print("=" * 80)
        print(f"Player: {player['name']} | Team: {player['team']} | Squad: {player['squad']}")
        print(f"Player ID: {player_id}")

        details = rcon.get_detailed_player_info(player_id=player_id)
        extracted_value = extract_garrisons_built(details)

        print(f"Extracted garrisons_built: {extracted_value}")
        print("Available nested keys:")
        for key in flatten_keys(details):
            if "garrison" in key.lower() or "build" in key.lower() or "stat" in key.lower():
                print(f"  - {key}")

        print("Raw payload:")
        print(pformat(details, sort_dicts=True, width=120))


if __name__ == "__main__":
    main()

from typing import List
from commands.utility.types import *

def calculate_metric(champion_positions, champions_by_position, punish):
    total = 0.0
    count = 0.0
    for position, champion in champions_by_position.items():
        val = champion_positions[champion][position]
        if val == 0:
            count += 1.0
            val = -1.0
        total += val
    total = total / len(champions_by_position)
    if punish:
        total -= count
        if count >= 2.0:
            total = 0.0
    return total


def get_optimal_roles_for_team(champion_positions, team_champion_ids: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    # Check the types in `team_champion_ids` and the other input types
    for i, champion in enumerate(team_champion_ids):
        if not isinstance(champion, int):
            raise ValueError("The team_champion_ids must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The team_champion_ids must be a list of champion IDs.")

    identified = {}
    if top is not None:
        identified["TOP"] = top
    if jungle is not None:
        identified["JUNGLE"] = jungle
    if middle is not None:
        identified["MIDDLE"] = middle
    if bottom is not None:
        identified["BOTTOM"] = bottom
    if utility is not None:
        identified["UTILITY"] = utility

    if len(identified) >= len(team_champion_ids):
        raise ValueError("The team_champion_ids was predefined by the kwargs.")

    positions = get_positions(champion_positions, team_champion_ids)
    return [i for i in positions.values()]


def get_positions(champion_ids_to_play_rates, team_champion_ids: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    for i, champion in enumerate(team_champion_ids):
        if not isinstance(champion, int):
            raise ValueError("The team_champion_ids must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The team_champion_ids must be a list of champion IDs.")

    if None not in (top, jungle, middle, bottom, utility):
        raise ValueError("The team_champion_ids was predefined by the kwargs.")

    comp_perm = quickperm(team_champion_ids)
    perms = []
    for perm in comp_perm:
        pos = {
            "TOP": perm[0],
            "JUNGLE": perm[1],
            "MIDDLE": perm[2],
            "BOTTOM": perm[3],
            "UTILITY": perm[4]
        }
        perms.append(pos)

    best_pos = {}
    best_metric = -float('inf')
    for punish in [True, False]:
        for perm in perms:
            metric = calculate_metric(champion_ids_to_play_rates, perm, punish)
            if metric > best_metric:
                best_pos = perm
                best_metric = metric
        if best_metric > 0.0:
            break
    return best_pos

def order_team(champion_ids_to_play_rates, teams: list[Team]):
    for team in teams:
        team_champion_ids = [player.champion_id for player in team.players]
        # [12, 34, 56, 78, 90] for example
        sorted_champ_ids = get_optimal_roles_for_team(champion_ids_to_play_rates, team_champion_ids)
        # print(f"Roles for team {team.team_id}: {sorted_champ_ids}")

        # In-place sort of team.players
        sorted_players = []
        for sorted_champ_id in sorted_champ_ids:
            for player in team.players:
                if player.champion_id == sorted_champ_id:
                    sorted_players.append(player)
                    break
        team.players[:] = sorted_players  # mutate in-place
    return teams

def quickperm(a):
    N = len(a)
    p = [*range(N+1)]
    i = 1
    while True:
        yield a
        if i >= N: break

        p[i] -= 1
        j = 0 if i % 2 == 0 else p[i]
        a[j], a[i] = a[i], a[j]

        i = 1
        while p[i] == 0:
            p[i] = i
            i += 1
from typing import List


def calculate_metric(champion_positions, champions_by_position):
    total = 0
    count = 0
    for position, champion in champions_by_position.items():
        val = champion_positions[champion][position]
        if val == 0:
            count += 1
            val = -1.0
        total += val
    total = total / len(champions_by_position)
    total -= count
    if count >= 2:
        total = 0
    return total


def calculate_confidence(best_metric, second_best_metric):
    confidence = (best_metric - second_best_metric) / best_metric * 100
    return confidence


def get_roles(champion_positions, composition: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    # Check the types in `composition` and the other input types
    for i, champion in enumerate(composition):
        if not isinstance(champion, int):
            raise ValueError("The composition must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The composition must be a list of champion IDs.")

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

    if len(identified) >= len(composition):
        raise ValueError("The composition was predefined by the kwargs.")

    positions = get_positions(champion_positions, composition)
    return [i for i in positions.values()]


def get_positions(champion_positions, composition: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    # Check the types in `composition` and the other input types
    for i, champion in enumerate(composition):
        if not isinstance(champion, int):
            raise ValueError("The composition must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The composition must be a list of champion IDs.")

    if None not in (top, jungle, middle, bottom, utility):
        raise ValueError("The composition was predefined by the kwargs.")

    comp_perm = quickperm(composition)
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
    for perm in perms:
        metric = calculate_metric(champion_positions, perm)
        if metric > best_metric:
            best_pos = perm
            best_metric = metric
    return best_pos

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
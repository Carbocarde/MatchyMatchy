from typing import List, Dict


def get_val_map(matrix: List[List[int]], labels: List[str]) -> Dict[str, Dict[str, int]]:
    """
    Convert the matrix and list of poll answers to a dict of dicts

    :param matrix: scores for specific pairings of answers
    :param labels: poll answers
    :return:
    """
    val_map = dict()

    for i, val in enumerate(labels):
        val_map[val] = dict()
        for j, val2 in enumerate(labels):
            val_map[val][val2] = matrix[i][j]

    return val_map


def poll_1() -> Dict[str, Dict[str, int]]:
    # Best place to go?

    camping = "Camping & Stargazing 🔭 🏕"
    fairground = "Go to the fairgrounds and play games 🎊🧸"
    hitchhike = "Hitchhike on a train to the next stop and explore 🚂"
    fancy = "Fancy Dinner 💃🕺"
    music = "Go to a concert and listen to music 🎶"

    arr = [camping, fairground, hitchhike, fancy, music]

    mappings = [
        [5, 4, 2, 2, 4],  # Camp
        [4, 5, 1, 3, 3],  # Hitchhike
        [2, 1, 5, 3, 2],  # Fancy Dinner
        [2, 3, 3, 5, 3],  # Fairgrounds
        [4, 3, 2, 3, 5]   # Music
    ]

    return get_val_map(mappings, arr)


def poll_2() -> Dict[str, Dict[str, int]]:
    # Do you like scary movies?

    yes = "Yes, I want to be scared!"
    no = "No! I hate scary movies"

    arr = [yes, no]

    mappings = [
        [5, 0],  # yes
        [0, 5]   # no
    ]

    return get_val_map(mappings, arr)


def poll_3() -> Dict[str, Dict[str, int]]:
    # Would you travel to a foreign country alone?

    yes_already = "Yes - I already have"
    yes_would = "Yes - I would"
    no = "No - I’d need to go with someone else"

    arr = [yes_already, yes_would, no]

    mappings = [
        [5, 4, 0],  # yes already
        [4, 5, 0],  # yes would
        [0, 0, 5],  # no
    ]

    return get_val_map(mappings, arr)

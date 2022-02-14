# MatchyMatchy

This script allows you to match users together given their answers to polls.
It uses the ["Blossom" method](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) invented by Jack Edmonds[^1] to find a maximum weight matching.

mappings.py contains the score mappings for each poll. Make sure you add new mappings to the "polls" array at the bottom of main.py.

[1] “Efficient Algorithms for Finding Maximum Matching in Graphs”, Zvi Galil, ACM Computing Surveys, 1986.

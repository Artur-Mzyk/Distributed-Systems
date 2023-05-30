#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import seaborn as sns

from matplotlib.patches import Rectangle, Circle

# PROJECT MODULES
from config import *


# FUNCTIONS
def draw_map(ax, canvas, map, locations = None, anomalies = None) -> None:
    ax.clear()
    sns.scatterplot(data=map, x='x_localization', y='y_localization', hue='object_id', ax=ax)

    if locations is not None:
        x1, y1, x2, y2 = SPACE_RANGE

        for loc in locations:
            (x, y), rng = loc
            ax.scatter([x], [y], marker="*")
            a = max(x - rng, x1)
            b = max(y - rng, y1)
            w = 2 * rng - max(0, a + 2 * rng - x2)
            h = 2 * rng - max(0, b + 2 * rng - y2)
            rect = Rectangle((a, b), w, h, fill=False)
            ax.add_patch(rect)

    if anomalies is not None:
        for object_id in anomalies:
            map_ = map[map['object_id'] == object_id]
            x = map_['x_localization'].to_numpy()
            y = map_['y_localization'].to_numpy()
            ax.scatter(x, y, color="red", marker='o')

    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.grid()
    canvas.draw()

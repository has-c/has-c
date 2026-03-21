from urllib.parse import urlencode
import os
import json

import yaml

with open('.github/data/canvas/settings.yaml', 'r') as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)

GRID_SIZE = settings['misc']['grid_size']
COLORS = settings['colors']

COLOR_IMAGES = {i: f"img/canvas/{c}.svg" for i, c in enumerate(COLORS)}


def create_link(text, url):
    return f"[{text}]({url})"


def canvas_to_markdown(canvas_data):
    canvas = canvas_data['canvas']
    md = ""

    # Header row (column numbers)
    md += "|   | " + " | ".join(str(c) for c in range(GRID_SIZE)) + " |\n"
    md += "| :-: | " + " | ".join([":-:"] * GRID_SIZE) + " |\n"

    for row in range(GRID_SIZE):
        md += f"| **{row}** | "
        for col in range(GRID_SIZE):
            color_idx = canvas[row][col]
            img = COLOR_IMAGES[color_idx]
            md += f'<img src="{img}" width=25px> | '
        md += "\n"

    return md


def generate_palette():
    md = "\n"
    md += "| "

    for color in COLORS:
        params = urlencode(settings['issues']['paint'], safe="{}")
        url = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=params)
        # Pre-fill with placeholder coords the user will edit
        url = url.format(row="__ROW__", col="__COL__", color=color)
        md += f'[<img src="img/canvas/{color}.svg" width=40px>]({url}) | '

    md += "\n"
    md += "| " + " | ".join([":-:"] * len(COLORS)) + " |\n"
    md += "\n"
    md += "_Click a color above, then edit the issue title to set your row & column (0-15)_\n"
    md += "\n"
    md += "**Format:** `Canvas: ROW COL COLOR` — e.g. `Canvas: 5 3 red`\n"

    return md


def generate_recent(recent_data):
    md = "\n"
    md += "| Pixel | Color | Artist |\n"
    md += "| :---: | :---: | :----- |\n"

    for entry in recent_data[:settings['misc']['max_recent']]:
        author = entry['author']
        md += "| ({}, {}) | {} | {} |\n".format(
            entry['row'], entry['col'],
            entry['color'],
            create_link(author, "https://github.com/" + author[1:]))

    return md + "\n"

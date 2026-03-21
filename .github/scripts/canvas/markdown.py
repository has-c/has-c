from urllib.parse import urlencode
import os
import json

import yaml

with open('.github/data/canvas/settings.yaml', 'r') as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)

GRID_SIZE = settings['misc']['grid_size']
COLORS = settings['colors']

COLOR_HEX = {
    'empty':  '#2d333b',
    'black':  '#1a1a2e',
    'white':  '#e6edf3',
    'red':    '#E63946',
    'blue':   '#2155CD',
    'green':  '#06D6A0',
    'yellow': '#FFB703',
    'purple': '#7B2D8E',
    'orange': '#FB5607',
}

COLOR_EMOJI = {
    'black':  '⬛', 'white':  '⬜', 'red':    '🟥',
    'blue':   '🟦', 'green':  '🟩', 'yellow': '🟨',
    'purple': '🟪', 'orange': '🟧',
}

PAINT_COLORS = [c for c in COLORS if c != 'empty']
CELL = 40
GAP = 2


def create_link(text, url):
    return f"[{text}]({url})"


def canvas_to_svg(canvas_data):
    canvas = canvas_data['canvas']
    size = GRID_SIZE * (CELL + GAP) + GAP
    header_h = 24
    label_w = 24
    total_w = label_w + size
    total_h = header_h + size

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}">\n'
    svg += f'  <rect width="{total_w}" height="{total_h}" rx="8" fill="#161b22"/>\n'

    # Column labels
    for col in range(GRID_SIZE):
        x = label_w + GAP + col * (CELL + GAP) + CELL // 2
        svg += f'  <text x="{x}" y="16" text-anchor="middle" fill="#848d97" font-family="monospace" font-size="11">{col}</text>\n'

    # Row labels + cells
    for row in range(GRID_SIZE):
        y = header_h + GAP + row * (CELL + GAP)
        svg += f'  <text x="12" y="{y + CELL // 2 + 4}" text-anchor="middle" fill="#848d97" font-family="monospace" font-size="11">{row}</text>\n'
        for col in range(GRID_SIZE):
            x = label_w + GAP + col * (CELL + GAP)
            color_name = COLORS[canvas[row][col]]
            hex_color = COLOR_HEX[color_name]
            svg += f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{hex_color}"/>\n'

    svg += '</svg>\n'
    return svg


def generate_palette():
    md = "\n"
    swatches = []
    for color in PAINT_COLORS:
        params = urlencode(settings['issues']['paint'], safe="{}")
        url = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=params)
        url = url.format(row="0", col="0", color=color)
        swatches.append(f"[{COLOR_EMOJI[color]} {color}]({url})")

    md += " | ".join(swatches) + "\n"
    md += "\n"
    md += "_Click a color, then edit the row & column in the issue title (0-7)_\n"
    return md


def generate_recent(recent_data):
    md = "\n"
    md += "| Pixel | Color | Artist |\n"
    md += "| :---: | :---: | :----- |\n"

    for entry in recent_data[:settings['misc']['max_recent']]:
        author = entry['author']
        color = entry['color']
        emoji = COLOR_EMOJI.get(color, '⬛')
        md += "| ({}, {}) | {} {} | {} |\n".format(
            entry['row'], entry['col'],
            emoji, color,
            create_link(author, "https://github.com/" + author[1:]))

    return md + "\n"

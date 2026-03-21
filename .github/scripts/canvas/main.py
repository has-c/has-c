import re
import os
import sys
import json
from enum import Enum

import yaml
from github import Github

sys.path.insert(0, os.path.dirname(__file__))
import markdown

DATA_DIR = '.github/data/canvas'


class Action(Enum):
    UNKNOWN = 0
    PAINT = 1


def parse_issue(title):
    match = re.match(r'Canvas:\s*(\d+)\s+(\d+)\s+(\w+)', title, re.I)
    if match:
        row = int(match.group(1))
        col = int(match.group(2))
        color = match.group(3).lower()
        return (Action.PAINT, row, col, color)
    return (Action.UNKNOWN, None, None, None)


def load_canvas():
    with open(os.path.join(DATA_DIR, 'canvas.json'), 'r') as f:
        return json.load(f)


def save_canvas(data):
    with open(os.path.join(DATA_DIR, 'canvas.json'), 'w') as f:
        json.dump(data, f, separators=(',', ':'))


def load_recent():
    path = os.path.join(DATA_DIR, 'recent.json')
    with open(path, 'r') as f:
        return json.load(f)


def save_recent(data):
    path = os.path.join(DATA_DIR, 'recent.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def replace_text_between(original_text, marker, replacement_text):
    delimiter_a = marker['begin']
    delimiter_b = marker['end']

    if original_text.find(delimiter_a) == -1 or original_text.find(delimiter_b) == -1:
        return original_text

    leading_text = original_text.split(delimiter_a)[0]
    trailing_text = original_text.split(delimiter_b)[1]

    return leading_text + delimiter_a + replacement_text + delimiter_b + trailing_text


def main(issue, issue_author, repo_owner):
    action, row, col, color = parse_issue(issue.title)

    with open(os.path.join(DATA_DIR, 'settings.yaml'), 'r') as f:
        settings = yaml.load(f, Loader=yaml.FullLoader)

    grid_size = settings['misc']['grid_size']
    valid_colors = settings['colors']

    if action == Action.UNKNOWN:
        issue.create_comment(settings['comments']['unknown_command'].format(author=issue_author))
        issue.edit(state='closed', labels=['Invalid'])
        return False, 'ERROR: Unknown command'

    if not (0 <= row < grid_size and 0 <= col < grid_size):
        issue.create_comment(settings['comments']['invalid_coords'].format(author=issue_author))
        issue.edit(state='closed', labels=['Invalid'])
        return False, 'ERROR: Invalid coordinates'

    if color not in valid_colors:
        issue.create_comment(settings['comments']['invalid_color'].format(author=issue_author))
        issue.edit(state='closed', labels=['Invalid'])
        return False, 'ERROR: Invalid color'

    # Paint the pixel
    canvas_data = load_canvas()
    color_idx = valid_colors.index(color)
    canvas_data['canvas'][row][col] = color_idx

    # Track painter
    key = f"{row},{col}"
    canvas_data['painters'][key] = issue_author

    save_canvas(canvas_data)

    # Update recent
    recent = load_recent()
    recent.insert(0, {
        'row': row,
        'col': col,
        'color': color,
        'author': issue_author
    })
    recent = recent[:settings['misc']['max_recent']]
    save_recent(recent)

    # Comment and close
    issue.create_comment(settings['comments']['success'].format(
        author=issue_author, row=row, col=col, color=color))
    issue.edit(state='closed', labels=[color.capitalize()])

    # Write canvas SVG
    svg = markdown.canvas_to_svg(canvas_data)
    with open('img/canvas/canvas.svg', 'w') as f:
        f.write(svg)

    # Update README
    with open('README.md', 'r') as f:
        readme = f.read()
        readme = replace_text_between(readme, settings['markers']['palette'], '{palette}')
        readme = replace_text_between(readme, settings['markers']['recent'], '{recent}')

    with open('README.md', 'w') as f:
        f.write(readme.format(
            palette=markdown.generate_palette(),
            recent=markdown.generate_recent(recent)))

    return True, ''


if __name__ == '__main__':
    repo = Github(os.environ['GITHUB_TOKEN']).get_repo(os.environ['GITHUB_REPOSITORY'])
    issue = repo.get_issue(number=int(os.environ['ISSUE_NUMBER']))
    issue_author = '@' + issue.user.login
    repo_owner = '@' + os.environ['REPOSITORY_OWNER']

    ret, reason = main(issue, issue_author, repo_owner)

    if ret is False:
        sys.exit(reason)

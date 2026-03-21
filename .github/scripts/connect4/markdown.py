from urllib.parse import urlencode
import os
import re
import ast

import yaml

with open('.github/data/connect4/settings.yaml', 'r') as settings_file:
    settings = yaml.load(settings_file, Loader=yaml.FullLoader)

DISC_IMAGES = {
    0: "img/connect4/empty.svg",
    1: "img/connect4/red.svg",
    2: "img/connect4/yellow.svg",
}


def create_link(text, link):
    return f"[{text}]({link})"


def create_drop_link(col):
    issue_link = settings['issues']['link'].format(
        repo=os.environ["GITHUB_REPOSITORY"],
        params=urlencode(settings['issues']['drop'], safe="{}"))
    return create_link(str(col), issue_link.format(col=col))


def generate_top_moves():
    with open('.github/data/connect4/top_moves.txt', 'r') as file:
        contents = file.read()
        dictionary = ast.literal_eval(contents)

    markdown = "\n"
    markdown += "| Total moves | User |\n"
    markdown += "| :---------: | :----- |\n"

    max_entries = settings['misc']['max_top_moves']
    for key, val in sorted(dictionary.items(), key=lambda x: x[1], reverse=True)[:max_entries]:
        markdown += "| {} | {} |\n".format(val, create_link(key, "https://github.com/" + key[1:]))

    return markdown + "\n"


def generate_last_moves():
    if not os.path.exists('.github/data/connect4/last_moves.txt'):
        return "\n| Move | Author |\n| :--: | :----- |\n\n"

    markdown = "\n"
    markdown += "| Move | Author |\n"
    markdown += "| :--: | :----- |\n"

    counter = 0

    with open('.github/data/connect4/last_moves.txt', 'r') as file:
        for line in file.readlines():
            parts = line.rstrip().split(':')

            if ":" not in line:
                continue

            if counter >= settings['misc']['max_last_moves']:
                break

            counter += 1

            col_match = re.search(r'Column (\d)', line, re.I)
            if col_match is not None:
                markdown += "| Column `{}` | {} |\n".format(
                    col_match.group(1),
                    create_link(parts[-1].strip(), "https://github.com/" + parts[-1].strip()[1:]))
            else:
                markdown += "| `{}` | {} |\n".format(
                    parts[0].strip(),
                    create_link(parts[-1].strip(), "https://github.com/" + parts[-1].strip()[1:]))

    return markdown + "\n"


def generate_moves_list(board_data):
    board = board_data['board']

    if not board_data['active']:
        issue_link = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=urlencode(settings['issues']['new_game']))
        return "**GAME IS OVER!** " + create_link("Click here", issue_link) + " to start a new game :D\n"

    turn_color = "red" if board_data['turn'] == 1 else "yellow"
    markdown = f"Drop a <img src=\"img/connect4/{turn_color}.svg\" width=20px> disc! Pick a column:\n\n"
    markdown += "| "

    for col in range(7):
        if board[0][col] == 0:
            markdown += create_drop_link(col + 1) + " | "
        else:
            markdown += "~~{}~~".format(col + 1) + " | "

    markdown += "\n"
    markdown += "| " + " | ".join([":-:"] * 7) + " |\n"

    return markdown


def board_to_markdown(board_data):
    board = board_data['board']
    markdown = ""

    markdown += "| 1 | 2 | 3 | 4 | 5 | 6 | 7 |\n"
    markdown += "| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"

    for row in range(6):
        markdown += "| "
        for col in range(7):
            img = DISC_IMAGES[board[row][col]]
            markdown += "<img src=\"{}\" width=50px> | ".format(img)
        markdown += "\n"

    return markdown

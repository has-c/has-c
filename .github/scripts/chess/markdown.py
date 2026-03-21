from collections import defaultdict
from urllib.parse import urlencode
import os
import re
import ast

import chess
import yaml

with open('.github/data/chess/settings.yaml', 'r') as settings_file:
    settings = yaml.load(settings_file, Loader=yaml.FullLoader)


def create_link(text, link):
    return f"[{text}]({link})"

def create_issue_link(source, dest_list):
    issue_link = settings['issues']['link'].format(
        repo=os.environ["GITHUB_REPOSITORY"],
        params=urlencode(settings['issues']['move'], safe="{}"))

    ret = [create_link(dest, issue_link.format(source=source, dest=dest)) for dest in sorted(dest_list)]
    return ", ".join(ret)

def generate_top_moves():
    with open('.github/data/chess/top_moves.txt', 'r') as file:
        contents = file.read()
        dictionary = ast.literal_eval(contents)

    markdown = "\n"
    markdown += "| Total moves | User |\n"
    markdown += "| :---------: | :----- |\n"

    max_entries = settings['misc']['max_top_moves']
    for key,val in sorted(dictionary.items(), key=lambda x: x[1], reverse=True)[:max_entries]:
        markdown += "| {} | {} |\n".format(val, create_link(key, "https://github.com/" + key[1:]))

    return markdown + "\n"

def generate_last_moves():
    if not os.path.exists('.github/data/chess/last_moves.txt'):
        return "\n| Move | Author |\n| :--: | :----- |\n\n"

    markdown = "\n"
    markdown += "| Move | Author |\n"
    markdown += "| :--: | :----- |\n"

    counter = 0

    with open('.github/data/chess/last_moves.txt', 'r') as file:
        for line in file.readlines():
            parts = line.rstrip().split(':')

            if not ":" in line:
                continue

            if counter >= settings['misc']['max_last_moves']:
                break

            counter += 1

            match_obj = re.search('([A-H][1-8])([A-H][1-8])', line, re.I)
            if match_obj is not None:
                source = match_obj.group(1).upper()
                dest = match_obj.group(2).upper()

                markdown += "| `" + source + "` to `" + dest + "` | " + create_link(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"
            else:
                markdown += "| `" + parts[0] + "` | " + create_link(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"

    return markdown + "\n"

def generate_moves_list(board):
    moves_dict = defaultdict(set)

    for move in board.legal_moves:
        source = chess.SQUARE_NAMES[move.from_square].upper()
        dest = chess.SQUARE_NAMES[move.to_square].upper()

        moves_dict[source].add(dest)

    markdown = ""

    if board.is_game_over():
        issue_link = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=urlencode(settings['issues']['new_game']))

        return "**GAME IS OVER!** " + create_link("Click here", issue_link) + " to start a new game :D\n"

    if board.is_check():
        markdown += "**CHECK!** Choose your move wisely!\n\n"

    markdown += "<details>\n"
    markdown += "<summary><strong>Click to see all available moves</strong></summary>\n\n"
    markdown += "| FROM | TO (Just click a link!) |\n"
    markdown += "| :----: | :---------------------- |\n"

    for source,dest in sorted(moves_dict.items()):
        markdown += "| **" + source + "** | " + create_issue_link(source, dest) + " |\n"

    markdown += "\n</details>\n"

    return markdown

def _is_light_square(file_idx, rank_idx):
    """Returns True if the square at (file_idx, rank_idx) is a light square."""
    return (file_idx + rank_idx) % 2 == 0


def _piece_image(piece_char, file_idx, rank_idx):
    """Returns the image path for a piece on a given square."""
    sq = "light" if _is_light_square(file_idx, rank_idx) else "dark"

    pieces = {
        "r": f"img/black/{sq}/rook.svg",
        "n": f"img/black/{sq}/knight.svg",
        "b": f"img/black/{sq}/bishop.svg",
        "q": f"img/black/{sq}/queen.svg",
        "k": f"img/black/{sq}/king.svg",
        "p": f"img/black/{sq}/pawn.svg",
        "R": f"img/white/{sq}/rook.svg",
        "N": f"img/white/{sq}/knight.svg",
        "B": f"img/white/{sq}/bishop.svg",
        "Q": f"img/white/{sq}/queen.svg",
        "K": f"img/white/{sq}/king.svg",
        "P": f"img/white/{sq}/pawn.svg",
        ".": f"img/blank-{sq}.svg",
    }
    return pieces.get(piece_char, "???")


def board_to_markdown(board):
    board_list = [[item for item in line.split(' ')] for line in str(board).split('\n')]
    markdown = ""

    if board.turn == chess.BLACK:
        markdown += "| | H | G | F | E | D | C | B | A | |\n"
    else:
        markdown += "| | A | B | C | D | E | F | G | H | |\n"
    markdown += "|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n"

    rows = range(1, 9)
    if board.turn == chess.BLACK:
        rows = reversed(rows)

    for row in rows:
        rank = 9 - row
        markdown += "| **" + str(rank) + "** | "
        columns = list(enumerate(board_list[row - 1]))
        if board.turn == chess.BLACK:
            columns = list(reversed(columns))

        for orig_col, elem in columns:
            # orig_col is file index (0=a, 7=h), rank-1 is rank index (0-based)
            img = _piece_image(elem, orig_col, row - 1)
            markdown += "<img src=\"{}\" width=50px> | ".format(img)
        markdown += "**" + str(rank) + "** |\n"

    if board.turn == chess.BLACK:
        markdown += "| | **H** | **G** | **F** | **E** | **D** | **C** | **B** | **A** | |\n"
    else:
        markdown += "| | **A** | **B** | **C** | **D** | **E** | **F** | **G** | **H** | |\n"

    return markdown

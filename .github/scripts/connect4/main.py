import re
import os
import sys
import json
import ast
from enum import Enum
import yaml
from github import Github

sys.path.insert(0, os.path.dirname(__file__))
import markdown

DATA_DIR = '.github/data/connect4'
GAMES_DIR = 'games'

ROWS = 6
COLS = 7


class Action(Enum):
    UNKNOWN = 0
    DROP = 1
    NEW_GAME = 2


def check_winner(board, player):
    """Check if the given player has won."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Diagonal (down-right)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Diagonal (down-left)
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False


def is_draw(board):
    """Check if the board is full (draw)."""
    return all(board[0][c] != 0 for c in range(COLS))


def drop_disc(board, col, player):
    """Drop a disc into a column. Returns the row it landed on, or -1 if full."""
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return row
    return -1


def update_top_moves(user):
    top_moves_path = os.path.join(DATA_DIR, 'top_moves.txt')
    with open(top_moves_path, 'r') as file:
        contents = file.read()
        dictionary = ast.literal_eval(contents)

    if user not in dictionary:
        dictionary[user] = 1
    else:
        dictionary[user] += 1

    with open(top_moves_path, 'w') as file:
        file.write(str(dictionary))


def update_last_moves(line):
    last_moves_path = os.path.join(DATA_DIR, 'last_moves.txt')
    with open(last_moves_path, 'r+') as last_moves:
        content = last_moves.read()
        last_moves.seek(0, 0)
        last_moves.write(line.rstrip('\r\n') + '\n' + content)


def replace_text_between(original_text, marker, replacement_text):
    delimiter_a = marker['begin']
    delimiter_b = marker['end']

    if original_text.find(delimiter_a) == -1 or original_text.find(delimiter_b) == -1:
        return original_text

    leading_text = original_text.split(delimiter_a)[0]
    trailing_text = original_text.split(delimiter_b)[1]

    return leading_text + delimiter_a + replacement_text + delimiter_b + trailing_text


def parse_issue(title):
    if title.lower() == 'connect4: start new game':
        return (Action.NEW_GAME, None)

    match = re.match(r'Connect4: Drop (\d)', title, re.I)
    if match:
        col = int(match.group(1))
        if 1 <= col <= 7:
            return (Action.DROP, col)

    return (Action.UNKNOWN, None)


def load_game():
    game_path = os.path.join(DATA_DIR, 'game.json')
    with open(game_path, 'r') as f:
        return json.load(f)


def save_game(game_data):
    game_path = os.path.join(DATA_DIR, 'game.json')
    with open(game_path, 'w') as f:
        json.dump(game_data, f, indent=2)


def main(issue, issue_author, repo_owner):
    action, value = parse_issue(issue.title)

    with open(os.path.join(DATA_DIR, 'settings.yaml'), 'r') as settings_file:
        settings = yaml.load(settings_file, Loader=yaml.FullLoader)

    game_data = load_game()

    if action == Action.NEW_GAME:
        if game_data['active'] and issue_author != repo_owner:
            issue.create_comment(settings['comments']['invalid_new_game'].format(author=issue_author))
            issue.edit(state='closed')
            return False, 'ERROR: A game is in progress. Only the repo owner can start a new game'

        issue.create_comment(settings['comments']['successful_new_game'].format(author=issue_author))
        issue.edit(state='closed')

        game_data = {
            "board": [[0] * COLS for _ in range(ROWS)],
            "turn": 1,
            "moves": 0,
            "active": True,
        }

        last_moves_path = os.path.join(DATA_DIR, 'last_moves.txt')
        with open(last_moves_path, 'w') as f:
            f.write('Start game: ' + issue_author)

        top_moves_path = os.path.join(DATA_DIR, 'top_moves.txt')
        with open(top_moves_path, 'w') as f:
            f.write('{}')

    elif action == Action.DROP:
        if not game_data['active']:
            issue.create_comment("Game is over! Start a new game first.")
            issue.edit(state='closed')
            return False, 'ERROR: No active game'

        col = value - 1  # 0-indexed

        # Check consecutive moves
        last_moves_path = os.path.join(DATA_DIR, 'last_moves.txt')
        with open(last_moves_path) as f:
            line = f.readline()
            last_player = line.split(':')[-1].strip()
            last_move = line.split(':')[0].strip()

        if last_player == issue_author and 'Start game' not in last_move:
            issue.create_comment(settings['comments']['consecutive_moves'].format(author=issue_author))
            issue.edit(state='closed', labels=['Invalid'])
            return False, 'ERROR: Two moves in a row!'

        player = game_data['turn']
        row = drop_disc(game_data['board'], col, player)

        if row == -1:
            issue.create_comment(settings['comments']['invalid_move'].format(author=issue_author, col=value))
            issue.edit(state='closed', labels=['Invalid'])
            return False, 'ERROR: Column is full'

        color_label = 'Red' if player == 1 else 'Yellow'
        issue.create_comment(settings['comments']['successful_move'].format(author=issue_author, col=value))
        issue.edit(state='closed', labels=[color_label])

        update_last_moves(f'Column {value}: {issue_author}')
        update_top_moves(issue_author)

        game_data['moves'] += 1

        # Check for winner or draw
        if check_winner(game_data['board'], player):
            game_data['active'] = False
            issue.add_to_labels('Winner!')

            with open(last_moves_path, 'r') as f:
                lines = f.readlines()
                pattern = re.compile(r'.*: (@[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})', flags=re.I)
                player_list = {re.match(pattern, line).group(1) for line in lines if re.match(pattern, line)}

            issue.create_comment(settings['comments']['game_over'].format(
                outcome=f'{color_label} wins',
                players=', '.join(player_list),
                num_moves=game_data['moves'],
                num_players=len(player_list)))

        elif is_draw(game_data['board']):
            game_data['active'] = False
            issue.add_to_labels('Draw!')

            with open(last_moves_path, 'r') as f:
                lines = f.readlines()
                pattern = re.compile(r'.*: (@[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})', flags=re.I)
                player_list = {re.match(pattern, line).group(1) for line in lines if re.match(pattern, line)}

            issue.create_comment(settings['comments']['game_over'].format(
                outcome="It's a draw",
                players=', '.join(player_list),
                num_moves=game_data['moves'],
                num_players=len(player_list)))
        else:
            # Switch turn
            game_data['turn'] = 2 if player == 1 else 1

    elif action == Action.UNKNOWN:
        issue.create_comment(settings['comments']['unknown_command'].format(author=issue_author))
        issue.edit(state='closed', labels=['Invalid'])
        return False, 'ERROR: Unknown action'

    save_game(game_data)

    last_moves = markdown.generate_last_moves()
    turn_color = 'Red' if game_data['turn'] == 1 else 'Yellow'

    with open('README.md', 'r') as file:
        readme = file.read()
        readme = replace_text_between(readme, settings['markers']['board'], '{c4_board}')
        readme = replace_text_between(readme, settings['markers']['moves'], '{moves_list}')
        readme = replace_text_between(readme, settings['markers']['turn'], '{turn}')
        readme = replace_text_between(readme, settings['markers']['last_moves'], '{last_moves}')
        readme = replace_text_between(readme, settings['markers']['top_moves'], '{top_moves}')

    with open('README.md', 'w') as file:
        file.write(readme.format(
            c4_board=markdown.board_to_markdown(game_data),
            moves_list=markdown.generate_moves_list(game_data),
            turn=turn_color,
            last_moves=last_moves,
            top_moves=markdown.generate_top_moves()))

    return True, ''


if __name__ == '__main__':
    repo = Github(os.environ['GITHUB_TOKEN']).get_repo(os.environ['GITHUB_REPOSITORY'])
    issue = repo.get_issue(number=int(os.environ['ISSUE_NUMBER']))
    issue_author = '@' + issue.user.login
    repo_owner = '@' + os.environ['REPOSITORY_OWNER']

    ret, reason = main(issue, issue_author, repo_owner)

    if ret == False:
        sys.exit(reason)

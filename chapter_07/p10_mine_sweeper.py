import collections
import random
import re
from enum import Enum


class Cell:
    def __init__(self, r, c):
        self.row = r
        self.column = c
        self._is_bomb = False
        self.number = 0
        self._is_exposed = False
        self._is_guess = False

    def set_row_and_column(self, r, c):
        self.row = r
        self.column = c

    def set_bomb(self, bomb):
        self._is_bomb = bomb
        self.number -= 1

    def increment_number(self):
        self.number += 1

    def get_row(self):
        return self.row

    def get_column(self):
        return self.column

    def is_bomb(self):
        return self._is_bomb

    def is_blank(self):
        return self.number == 0

    def is_exposed(self):
        return self._is_exposed

    def flip(self):
        self._is_exposed = True
        return not self._is_bomb

    def toggle_guess(self):
        if not self.is_exposed():
            self._is_guess = not self._is_guess
        return self._is_guess

    def is_guess(self):
        return self._is_guess

    def __str__(self):
        return self.get_underside_state()

    def get_surface_state(self):
        if self.is_exposed():
            return self.get_underside_state()
        elif self.is_guess():
            return "B\t"
        else:
            return "?\t"

    def get_underside_state(self):
        if self.is_bomb():
            return "*\t"
        elif self.number > 0:
            return str(self.number) + "\t"
        else:
            return "\t"


class UserPlay:
    def __init__(self, r, c, guess):
        self.row = r
        self.column = c
        self._is_guess = guess

    @classmethod
    def from_string(cls, _input):
        _is_guess = False

        if len(_input) > 0 and _input[0] == 'B':
            _is_guess = True
            _input = _input[1:]

        if not re.match("\\d* \\d+", _input):
            return None

        parts = _input.split(" ")
        try:
            r = int(parts[0])
            c = int(parts[1])
            return UserPlay(r, c, _is_guess)
        except Exception as e:
            return None

    def is_guess(self):
        return self._is_guess

    def get_column(self):
        return self.column

    def get_row(self):
        return self.row


class UserPlayResult:

    def __init__(self, success, state):
        self.successful = success
        self.resulting_state = state

    def successful_move(self):
        return self.successful

    def get_resulting_state(self):
        return self.resulting_state


class GameState(Enum):
    WON = 1
    LOST = -1
    RUNNING = 0


class Board:
    def __init__(self, r, c, b):
        self.n_rows = r
        self.n_columns = c
        self.n_bombs = b

        self.initialize_board()
        self.shuffle_board()
        self.set_numbered_cells()

        self.num_unexposed_remaining = self.n_rows * self.n_columns - self.n_bombs

    def initialize_board(self):
        self.cells = [[0] * self.n_columns for _ in range(self.n_rows)]
        self.bombs = [0] * self.n_bombs
        for r in range(self.n_rows):
            for c in range(self.n_columns):
                self.cells[r][c] = Cell(r, c)

        for i in range(self.n_bombs):
            r = i // self.n_columns
            c = (i - r * self.n_columns) % self.n_columns
            self.bombs[i] = self.cells[r][c]
            self.bombs[i].set_bomb(True)

    def shuffle_board(self):
        n_cells = self.n_rows * self.n_columns
        for index1 in range(n_cells):
            index2 = index1 + random.randrange(n_cells - index1)
            if index1 != index2:
                # get cell at index1
                row1 = index1 // self.n_columns
                column1 = (index1 - row1 * self.n_columns) % self.n_columns
                cell1 = self.cells[row1][column1]

                # get cell at index2
                row2 = index2 // self.n_columns
                column2 = (index2 - row2 * self.n_columns) % self.n_columns
                cell2 = self.cells[row2][column2]

                # swap
                self.cells[row1][column1] = cell2
                cell2.set_row_and_column(row1, column1)
                self.cells[row2][column2] = cell1
                cell1.set_row_and_column(row2, column2)

    def in_bounds(self, row, column):
        return 0 <= row < self.n_rows and 0 <= column < self.n_columns

    def set_numbered_cells(self):
        '''
        Set the cells around the bombs to the right number.
        Although the bombs have been shuffled, the reference
        in the bombs array is still the same object.
        '''

        deltas = [  # offsets of 8 surrounding cells
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1], [0, 1],
            [1, -1], [1, 0], [1, 1]
        ]
        for bomb in self.bombs:
            row = bomb.get_row()
            col = bomb.get_column()
            for delta in deltas:
                r = row + delta[0]
                c = col + delta[1]
                if self.in_bounds(r, c):
                    self.cells[r][c].increment_number()

    def print_board(self, show_underside):
        print()
        print("", end="\t")
        for i in range(self.n_columns):
            print(i, end="\t")
        print()
        for i in range(self.n_columns):
            print('-' * 8, end="")
        print()
        for r in range(self.n_rows):
            print(str(r) + "| ", end="\t")
            for c in range(self.n_columns):
                if show_underside:
                    print(self.cells[r][c].get_underside_state(), end="")
                else:
                    print(self.cells[r][c].get_surface_state(), end="")
            print()

    def flip_cell(self, cell):
        if not cell.is_exposed() and not cell.is_guess():
            cell.flip()
            self.num_unexposed_remaining -= 1
            return True
        return False

    def expand_blank(self, cell):
        deltas = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1], [0, 1],
            [1, -1], [1, 0], [1, 1]
        ]

        to_explore = collections.deque([cell])

        while to_explore:
            current = to_explore.popleft()

            for delta in deltas:
                r = current.get_row() + delta[0]
                c = current.get_column() + delta[1]

                if self.in_bounds(r, c):
                    neighbor = self.cells[r][c]
                    if self.flip_cell(neighbor) and neighbor.is_blank():
                        to_explore.append(neighbor)

    def get_cell_at_location(self, play):
        row = play.get_row()
        col = play.get_column()
        if not self.in_bounds(row, col):
            return None
        return self.cells[row][col]

    def get_number_remaining(self):
        return self.num_unexposed_remaining

    def play_flip(self, play):
        cell = self.get_cell_at_location(play)
        if cell is None:
            return UserPlayResult(False, GameState.RUNNING)

        if play.is_guess():
            guess_result = cell.toggle_guess()
            return UserPlayResult(guess_result, GameState.RUNNING)

        result = self.flip_cell(cell)

        if cell.is_bomb():
            return UserPlayResult(result, GameState.LOST)

        if cell.is_blank():
            self.expand_blank(cell)

        if self.num_unexposed_remaining == 0:
            return UserPlayResult(result, GameState.WON)

        return UserPlayResult(result, GameState.RUNNING)


class Game:

    def __init__(self, r, c, b):
        self.rows = r
        self.columns = c
        self.bombs = b
        self.state = GameState.RUNNING
        self.board = None

    def initialize(self):
        if self.board is None:
            self.board = Board(self.rows, self.columns, self.bombs)
            self.board.print_board(True)
            return True
        else:
            print("Game has already been initialized.")
            return False

    def start(self):
        if self.board is None:
            self.initialize()
        return self.play_game()

    def print_game_state(self):
        if self.state == GameState.LOST:
            self.board.print_board(True)
            print("FAIL")
        elif self.state == GameState.WON:
            self.board.print_board(True)
            print("WIN")
        else:
            print("Number remaining: " + str(self.board.get_number_remaining()))
            self.board.print_board(False)

    def play_game(self):
        self.print_game_state()

        while self.state == GameState.RUNNING:
            _input = input()
            if _input == "exit":
                return False

            play = UserPlay.from_string(_input)
            if play is None:
                continue

            result = self.board.play_flip(play)
            if result.successful_move():
                self.state = result.get_resulting_state()
            else:
                print("Could not flip cell (" + play.get_row() + ", " + play.get_column() + ").")

            self.print_game_state()

        return True


def test_mine_sweeper():
    game = Game(7, 7, 3)
    game.initialize()
    game.start()


if __name__ == "__main__":
    # unittest.main()
    game = Game(7, 7, 3)
    game.initialize()
    game.start()

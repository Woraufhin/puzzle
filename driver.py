import argparse
from collections import deque


BOARD_DELIMETER = ','


class Puzzle(object):
    """The state of the puzzle"""

    HOLE = 0
    WIDTH = 3

    def __init__(self, board, hole=None, hist=None):
        self.board = board
        self.hist = hist if hist else []
        self.hole = hole if hole else self.board.index(self.HOLE)

    @property
    def possible_moves(self):
        """Generates all possible moves for a given puzzle state.

        First, it checks for up and down movements given by +width or
        -width from actual index, being the result between board's length
        boundaries.

        Second, it checks for left and right movementes given by +1 or
        -1 from actual index; being the destination always between
        boundaries of row of flattened matrix.

        :return (dest, action) int str index in board and description of action
        """

        for dest in (self.hole - self.WIDTH, self.hole + self.WIDTH):
            if 0 <= dest < len(self.board):
                action = 'UP' if dest == self.hole - self.WIDTH else 'DOWN'
                yield (dest, action)

        for dest in (self.hole - 1, self.hole + 1):
            if dest // self.WIDTH == self.hole // self.WIDTH:
                action = 'LEFT' if dest == self.hole - 1 else 'RIGHT'
                yield (dest, action)

    @property
    def solved(self):
        """Checks if puzzle is solved"""
        return self.board == [self.HOLE] + range(1, 9)

    def move(self, to, action):
        """Changes puzzle state

        :param to destination
        :return Puzzle
        """
        board = self.board[:]
        board[self.hole], board[to] = board[to], board[self.hole]
        hist = self.hist[:]
        hist.append(action)
        return Puzzle(board, to, hist)

    def __hash__(self):
        return hash(str(self.board))

    def __eq__(self, other):
        """Override the default equality operator for this class"""
        if isinstance(other, self.__class__):
            return self.board == other.board
        return NotImplemented

    def __str__(self):
        return '\n'.join(str(self.board[i:i + self.WIDTH])
                         for i in xrange(0, len(self.board), self.WIDTH))


class Solver(object):

    def __init__(self, init_state):
        self.state = Puzzle(init_state)
        self.factory = {
            'bfs': self.breath_first_search,
            'dfs': self.depth_first_search
        }

    def solve(self, method):
        try:
            return self.factory[method]()
        except KeyError:
            print('Method "{}" for solving puzzle does not exist'
                  .format(method))
            exit(1)

    def breath_first_search(self):
        fringe = deque([self.state])
        explored = set()
        fringe_set = {self.state}

        while fringe:

            state = fringe.popleft()
            fringe_set.remove(state)
            explored.add(state)

            if state.solved:
                return state.hist

            for pos, action in state.possible_moves:
                new_state = state.move(pos, action)
                if new_state not in explored and new_state not in fringe_set:
                    fringe.append(new_state)
                    fringe_set.add(new_state)

    def depth_first_search(self):
        pass


def parse_args():

    def board(val):
        return map(int, val.split(BOARD_DELIMETER))

    parser = argparse.ArgumentParser(description='Puzzle solver')
    parser.add_argument('method', help='BFS supported')
    parser.add_argument('board', help='The board to solve', type=board)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    puzzle = Solver(args.board)
    print args.method
    print puzzle.solve(args.method)

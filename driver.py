import os
import argparse
import itertools
from time import time
from collections import deque


BOARD_DELIMETER = ','
OUTPUT = 'output.txt'


class Puzzle(object):
    """The state of the puzzle"""

    HOLE = 0
    WIDTH = 3

    def __init__(self, board, hole=None, hist=None):
        self.board = board
        self.hist = hist if hist else ''
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
                action = 'U' if dest == self.hole - self.WIDTH else 'D'
                yield (dest, action)

        for dest in (self.hole - 1, self.hole + 1):
            if dest // self.WIDTH == self.hole // self.WIDTH:
                action = 'L' if dest == self.hole - 1 else 'R'
                yield (dest, action)

    @property
    def solved(self):
        """Checks if puzzle is solved"""
        return self.board == [self.HOLE] + range(1, self.WIDTH ** 2)

    def move(self, to, action):
        """Changes puzzle state

        :param to destination
        :return Puzzle
        """
        board = self.board[:]
        board[self.hole], board[to] = board[to], board[self.hole]
        hist = self.hist + action
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
        self.stats = Stats()
        self.factory = {
            'bfs': self.breath_first_search,
            'dfs': self.depth_first_search,
            'ast': self.a_star,
            'ida': self.ida_star,
        }

    def solve(self, method):
        try:
            now = time()
            goal = self.factory[method]()
            self.stats.running_time = time() - now
            return goal
        except KeyError:
            print('Method "{}" for solving puzzle does not exist'
                  .format(method))
            exit(1)

    def solvable(self):
        inv = 0
        for i, j in itertools.combinations(self.state.board, 2):
            if all([i, j]) and i > j:  # none of them is 0
                inv += 1
        return True if inv % 2 == 0 else False

    def breath_first_search(self):
        fringe = deque([self.state])
        explored = {self.state}
        fringe_set = {self.state}

        while fringe:
            state = fringe.popleft()

            # Stats
            if len(fringe_set) > self.stats.max_fringe_size:
                self.stats.max_fringe_size = len(fringe_set)
            fringe_set.remove(state)

            if state.solved:
                self.stats.goal = state
                self.stats.fringe_size = len(fringe_set)
                return state.hist

            self.stats.nodes_expanded += 1  # Stats
            for pos, action in state.possible_moves:
                new_state = state.move(pos, action)
                if new_state not in explored and new_state not in fringe_set:
                    if len(new_state.hist) > self.stats.max_search_depth:
                        self.stats.max_search_depth = len(new_state.hist)
                    fringe.append(new_state)
                    fringe_set.add(new_state)
            explored.add(state)

    def depth_first_search(self):
        fringe = [self.state]
        explored = {self.state}
        fringe_set = {self.state}

        while fringe:
            state = fringe.pop()

            # Stats
            if len(fringe_set) > self.stats.max_fringe_size:
                self.stats.max_fringe_size = len(fringe_set)
            fringe_set.remove(state)
            explored.add(state)

            if state.solved:
                self.stats.goal = state
                self.stats.fringe_size = len(fringe)
                return state.hist

            self.stats.nodes_expanded += 1  # Stats
            for pos, action in reversed(list(state.possible_moves)):
                new_state = state.move(pos, action)
                if new_state not in explored and new_state not in fringe_set:
                    if len(new_state.hist) > self.stats.max_search_depth:
                        self.stats.max_search_depth = len(new_state.hist)
                    fringe.append(new_state)
                    fringe_set.add(new_state)

    def a_star(self):
        heuristic = Heuristics.manhattan

        fringe = {self.state: heuristic(self.state)}
        explored = {self.state}

        while fringe:
            state = min(fringe, key=fringe.get)

            # Stats
            if len(fringe) > self.stats.max_fringe_size:
                self.stats.max_fringe_size = len(fringe)

            fringe.pop(state)
            explored.add(state)

            if state.solved:
                self.stats.goal = state
                self.stats.fringe_size = len(fringe)
                return state.hist

            self.stats.nodes_expanded += 1  # Stats

            for pos, action in state.possible_moves:
                new_state = state.move(pos,action)
                if new_state not in explored:
                    if len(new_state.hist) > self.stats.max_search_depth:
                        self.stats.max_search_depth = len(new_state.hist)
                    fringe[new_state] = heuristic(new_state) + 1  # 1 is g(n)

    def ida_star(self):
        heuristic = Heuristics.manhattan
        limit = 0  # depth limit

        fringe = {self.state: heuristic(self.state)}
        explored = {self.state}

        def _ida_star(limit):
            while fringe:
                state = min(fringe, key=fringe.get)

                # Stats
                if len(fringe) > self.stats.max_fringe_size:
                    self.stats.max_fringe_size = len(fringe)

                if len(state.hist) > limit:
                    return _ida_star(limit + 1)

                fringe.pop(state)
                explored.add(state)

                if state.solved:
                    self.stats.goal = state
                    self.stats.fringe_size = len(fringe)
                    return state.hist

                self.stats.nodes_expanded += 1  # Stats

                for pos, action in state.possible_moves:
                    new_state = state.move(pos,action)
                    if new_state not in explored:
                        if len(new_state.hist) > self.stats.max_search_depth:
                            self.stats.max_search_depth = len(new_state.hist)
                        fringe[new_state] = heuristic(new_state) + 1  # 1 is g(n)

        return _ida_star(limit)


class Heuristics(object):

    @staticmethod
    def manhattan(state, width=None):
        """Manhattan heuristic.

        Cost represents the moves that a tile has to do to reach the
        position it should be in.
        """

        width = width if width else state.WIDTH
        cost = 0
        for tile in state.board:
            if not tile == state.board.index(tile) and tile != 0:
                # up down movements
                c_row = state.board.index(tile) // width
                d_row = tile // width
                if not c_row == d_row:
                    cost += abs(c_row - d_row)
                # left right movements
                c_col = state.board.index(tile) - c_row * width
                d_col = tile - d_row * width
                if not c_col == d_col:
                    cost += abs(c_col - d_col)
        return cost

    @staticmethod
    def misplaced_tiles(state):
        """Misplaced tiles heuristic.

        Cost represents the number of tiles that are not in its goal state
        """

        cost = 0
        for tile in state.board:
            if not tile == state.board.index(tile) and tile != 0:
                cost += 1
        return cost


class Stats(object):

    def __init__(self):
        self.goal = None
        self.nodes_expanded = 0
        self.fringe_size = 0
        self.max_fringe_size = 0
        self.max_search_depth = 0
        self.running_time = None

    def __str__(self):
        return """path_to_goal: {path}
cost_of_path: {cost}
nodes_expanded: {nodes}
fringe_size: {fringe_size}
max_fringe_size: {max_fringe_size}
search_depth: {search_depth}
max_search_depth: {max_search_depth}
running_time: {running_time}
max_ram_usage: {ram}""".format(
    path = self._path_to_goal(),
    cost = len(self.goal.hist),
    nodes = self.nodes_expanded,
    fringe_size = self.fringe_size,
    max_fringe_size = self.max_fringe_size,
    search_depth = len(self.goal.hist),
    max_search_depth = self.max_search_depth,
    running_time = self.running_time,
    ram = self._max_ram_usage
)

    @property
    def _max_ram_usage(self):
        if os.name == 'posix':
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        else:
            import psutil
            p = psutil.Process()
            return p.memory_info().rss / 1048576.0

    def _path_to_goal(self):
        mapping = {'U': 'Up', 'D': 'Down', 'L': 'Left', 'R': 'Right'}
        return [mapping[e] for e in self.goal.hist]


def parse_args():

    def board(val):
        return map(int, val.split(BOARD_DELIMETER))

    parser = argparse.ArgumentParser(description='Puzzle solver')
    parser.add_argument('method', choices=['bfs', 'dfs', 'ast', 'ida'],
                        help='BFS, DFS, A* supported')
    parser.add_argument('board', help='The board to solve', type=board)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    puzzle = Solver(args.board)

    if puzzle.solvable():
        puzzle.solve(args.method)
        with open(OUTPUT, 'w') as f:
            f.write(str(puzzle.stats))
    else:
        print 'Puzzle is not solvable. It has an odd number of inversions'

'''
This Sudoku-solving algorithm was initially designed and implemented by
Peter Norvig at http://norvig.com/sudoku.html.

This implementation simply employees the multiprocessing and performs a
bi-directional DFS to speed up the search process.
'''

import multiprocessing as mp
import time

class SudokuSolver(object):
    '''Sudoku solver class
    '''
    def __init__(self):
        '''Constructor'''
        self.digits   = '123456789'
        self.rows     = 'ABCDEFGHI'
        self.cols     = self.digits
        self.squares  = self.cross(self.rows, self.cols)

        self.unitlist = ([self.cross(self.rows, c) for c in self.cols] +
                    [self.cross(r, self.cols) for r in self.rows] +
                    [self.cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')])
        self.units = dict((s, [u for u in self.unitlist if s in u])
                     for s in self.squares)
        self.peers = dict((s, set(sum(self.units[s],[]))-set([s]))
                     for s in self.squares)

    def cross(self, A, B):
        '''Cross product of elements in A and elements in B.'''
        return [a+b for a in A for b in B]

    def test(self):
        '''A set of unit tests.'''
        assert len(self.squares) == 81
        assert len(self.unitlist) == 27
        assert all(len(self.units[s]) == 3 for s in self.squares)
        assert all(len(self.peers[s]) == 20 for s in self.squares)
        assert self.units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                            ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                            ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
        assert self.peers['C2'] == set(['A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
                                'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
                                'A1', 'A3', 'B1', 'B3'])
        print ('All tests pass.')

    def grid_values(self, grid):
        '''Convert grid into a dict of {square: char} with '0' or '.' for empties.'''
        chars = [c for c in grid if c in self.digits or c in '0.']
        assert len(chars) == 81
        return dict(zip(self.squares, chars))

    def parse_grid(self, grid,display=False):
        '''Convert grid to a dict of possible values, {square: digits}, or
        return False if a contradiction is detected.'''
        ## To start, every square can be any digit; then assign values from the grid.
        values = dict((s, self.digits) for s in self.squares)
        for s,d in self.grid_values(grid).items():
            if d in self.digits and not self.assign(values, s, d):
                return False ## (Fail if we can't assign d to square s.)
        if display:
            self.display(values)
        return values

    def assign(self, values, s, d):
        '''Eliminate all the other values (except d) from values[s] and propagate.
        Return values, except return False if a contradiction is detected.'''
        other_values = values[s].replace(d, '')
        if all(self.eliminate(values, s, d2) for d2 in other_values):
            return values
        else:
            return False

    def eliminate(self, values, s, d):
        '''Eliminate d from values[s]; propagate when values or places <= 2.
        Return values, except return False if a contradiction is detected.'''
        if d not in values[s]:
            return values ## Already eliminated
        values[s] = values[s].replace(d,'')
        ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
        if len(values[s]) == 0:
            return False ## Contradiction: removed last value
        elif len(values[s]) == 1:
            d2 = values[s]
            if not all(self.eliminate(values, s2, d2) for s2 in self.peers[s]):
                return False
        ## (2) If a unit u is reduced to only one place for a value d, then put it there.
        for u in self.units[s]:
            dplaces = [s for s in u if d in values[s]]
            if len(dplaces) == 0:
                return False ## Contradiction: no place for this value
            elif len(dplaces) == 1:
        	    # d can only be in one place in unit; assign it there
                if not self.assign(values, dplaces[0], d):
                    return False
        return values

    def display(self, values):
        '''Display these values as a 2-D grid.'''
        width = 1+max(len(values[s]) for s in self.squares)
        line = '+'.join(['-'*(width*3)]*3)
        for r in self.rows:
            print (''.join(values[r+c].center(width)+('|' if c in '36' else '') for c in self.cols))
            if r in 'CF':
                print (line)
        print

    def solve(self, grid,display=False, mp=False):
        '''Solve the sudoku grid from input by either a single DFS or bi-directionally'''
        if mp:
            rst = self.mpSearch(self.parse_grid(grid))
        else:
            rst = self.search(self.parse_grid(grid))

        if display:
            self.display(rst)
        return rst

    def search(self, values):
        '''Using depth-first search and propagation, try all possible values.'''
        if values is False:
            return False ## Failed earlier
        if all(len(values[s]) == 1 for s in self.squares):
            return values ## Solved!
        ## Chose the unfilled square s with the fewest possibilities
        n,s = min((len(values[s]), s) for s in self.squares if len(values[s]) > 1)
        return self.some(self.search(self.assign(values.copy(), s, d))
    		for d in values[s])

    def mpSearch(self,values):
        '''Search using multiple processes'''
        if values is False:
            return values

        resultQ = mp.Queue(maxsize=2)
        pros = [mp.Process(target=self.searchWorker, args=(values.copy(),resultQ,i)) for i in range(2)]
        [i.start() for i in pros]
        cps = pros

        while resultQ.empty() and len(cps) > 0:
            time.sleep(.5)
            cps = [i for i in cps if i.is_alive()]

        [i.terminate() for i in pros]

        if resultQ.empty():
            return False
        return resultQ.get(timeout=0.2)

    def searchWorker(self,values,resultQ,index):
        '''Using depth-first search and propagation, try all possible values.'''
        if values is False:
            return False ## Failed earlier
        if all(len(values[s]) == 1 for s in self.squares):
            resultQ.put(values)
            return values ## Solved!
        ## Chose the unfilled square s with the fewest possibilities
        n,s = min((len(values[s]), s) for s in self.squares if len(values[s]) > 1)

        if index == 0:
            l = [i for i in range(len(list(values[s])))]
        else:
            l = [i for i in range(len(list(values[s]))-1,-1,-1)]
        for d in l:
            self.searchWorker(self.assign(values.copy(), s, values[s][d]),resultQ,index)
        return

    def some(self, seq):
        "Return some element of seq that is true."
        for e in seq:
            if e: return e
        return False

if __name__ == '__main__':
    # test()

    '''sudoku examples'''
    grid1 = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
    grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
    hard1 = '.....6....59.....82....8....45........3........6..3.54...325..6..................'
    insane = '1.......9..3.9...7....2851.3.657......1..36..47.61.....6..3.......8...5.7....51.2'

    solver = SudokuSolver()

    start = time.time()
    #solver.solve(grid1,display=True,mp=True)
    #solver.solve(grid2,display=True,mp=True)
    solver.solve(hard1,display=True,mp=True)
    print(time.time()-start)

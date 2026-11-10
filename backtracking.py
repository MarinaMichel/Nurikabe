"""Backtracking solver for Nurikabe.

Search: cells are assigned black (water) / white (land) one at a time.
Pruning (the search tree is cut immediately when):
  * an island becomes larger than its clue / contains two clues,
  * an island is closed (no unknown neighbour) but has the wrong size,
  * a 2x2 block of water forms,
  * the water network is split into pieces that can no longer join.
Forward checking (forced moves) is applied after every assignment so
that most cells are decided by deduction instead of by guessing.
"""
from collections import deque
from grid import unknown, water, land
from constraints import neighbors, components, count_pools, is_solution


class Contradiction(Exception):
    pass


class BacktrackingSolver:

    def __init__(self, grid, clues):
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.start = [row[:] for row in grid]
        self.clues = clues
        self.nodes = 0

    # ------------------------------------------------------------------
    def _nbrs(self, r, c):
        return neighbors(r, c, self.rows, self.cols)

    def _set(self, g, r, c, value):
        if g[r][c] == value:
            return False
        if g[r][c] != unknown:
            raise Contradiction
        g[r][c] = value
        return True

    # ------------------------------------------------------------------
    def _islands(self, g):
        """Return list of (cells, clue_or_None, open_neighbours) for each land component."""
        out = []
        for comp in components(g, land):
            inside = [self.clues[p] for p in comp if p in self.clues]
            if len(inside) > 1:
                raise Contradiction
            frontier = set()
            for r, c in comp:
                for n in self._nbrs(r, c):
                    if g[n[0]][n[1]] == unknown:
                        frontier.add(n)
            clue = inside[0] if inside else None
            if clue is not None:
                if len(comp) > clue:
                    raise Contradiction
                if len(comp) < clue and not frontier:
                    raise Contradiction
            elif not frontier:
                raise Contradiction          # closed island without clue
            out.append((comp, clue, frontier))
        return out

    def _propagate(self, g):
        """Apply forced moves until nothing changes. Raises Contradiction on a dead end."""
        R, C = self.rows, self.cols
        changed = True
        while changed:
            changed = False
            islands = self._islands(g)

            # 1. finished island -> surround with water
            for comp, clue, frontier in islands:
                if clue is not None and len(comp) == clue:
                    for (r, c) in frontier:
                        changed |= self._set(g, r, c, water)

            # 2. unknown cell touching two different islands (or that would
            #    make an island too big) must be water
            for r in range(R):
                for c in range(C):
                    if g[r][c] != unknown:
                        continue
                    touching = []
                    for n in self._nbrs(r, c):
                        if g[n[0]][n[1]] == land:
                            for idx, (comp, _, _) in enumerate(islands):
                                if n in comp:
                                    if idx not in touching:
                                        touching.append(idx)
                                    break
                    if len(touching) >= 2:
                        clued = [islands[i] for i in touching if islands[i][1] is not None]
                        total = 1 + sum(len(islands[i][0]) for i in touching)
                        if len(clued) >= 2 or (clued and total > clued[0][1]):
                            changed |= self._set(g, r, c, water)
                    elif len(touching) == 1:
                        comp, clue, _ = islands[touching[0]]
                        if clue is not None and len(comp) + 1 > clue:
                            changed |= self._set(g, r, c, water)

            # 3. reachability: land is only possible where some unfinished
            #    island can still grow to
            reach = set()
            for comp, clue, _ in islands:
                if clue is None:
                    continue
                budget = clue - len(comp)
                if budget <= 0:
                    continue
                dist = {p: 0 for p in comp}
                dq = deque(comp)
                while dq:
                    p = dq.popleft()
                    if dist[p] >= budget:
                        continue
                    for n in self._nbrs(*p):
                        if n not in dist and g[n[0]][n[1]] != water:
                            dist[n] = dist[p] + 1
                            dq.append(n)
                reach.update(dist)
            for comp, clue, _ in islands:        # clued islands count as reachable
                if clue is not None:
                    reach.update(comp)
            for r in range(R):
                for c in range(C):
                    if g[r][c] == unknown and (r, c) not in reach:
                        changed |= self._set(g, r, c, water)
                    elif g[r][c] == land and (r, c) not in reach:
                        raise Contradiction   # land that no clue can claim

            # 4. 2x2 water pools
            for r in range(R - 1):
                for c in range(C - 1):
                    block = [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]
                    vals = [g[a][b] for a, b in block]
                    if vals.count(water) == 4:
                        raise Contradiction
                    if vals.count(water) == 3 and vals.count(unknown) == 1:
                        a, b = block[vals.index(unknown)]
                        changed |= self._set(g, a, b, land)

            # 5. water connectivity
            w_comps = components(g, water)
            if len(w_comps) > 1:
                for comp in w_comps:
                    frontier = set()
                    for r, c in comp:
                        for n in self._nbrs(r, c):
                            if g[n[0]][n[1]] == unknown:
                                frontier.add(n)
                    if not frontier:
                        raise Contradiction       # this water piece is cut off
                    if len(frontier) == 1:
                        (r, c), = frontier
                        changed |= self._set(g, r, c, water)

            # 6. too much land
            if sum(row.count(land) for row in g) > sum(self.clues.values()):
                raise Contradiction

    # ------------------------------------------------------------------
    def _choose_cell(self, g):
        """Most constrained choice: an unknown cell next to the smallest-remaining island."""
        best, best_key = None, None
        for comp, clue, frontier in self._islands(g):
            if clue is None or not frontier:
                continue
            key = (clue - len(comp), len(frontier))
            if best_key is None or key < best_key:
                best_key = key
                best = sorted(frontier)[0]
        if best is not None:
            return best
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r][c] == unknown:
                    return r, c
        return None

    def _solve(self, g):
        self.nodes += 1
        try:
            self._propagate(g)
        except Contradiction:
            return None
        cell = self._choose_cell(g)
        if cell is None:
            return g if is_solution(g, self.clues) else None
        r, c = cell
        for value in (land, water):
            child = [row[:] for row in g]
            child[r][c] = value
            result = self._solve(child)
            if result is not None:
                return result
        return None

    def solve(self):
        g = [row[:] for row in self.start]
        for (r, c) in self.clues:
            g[r][c] = land
        return self._solve(g)

"""Genetic Algorithm (GA) and Memetic Algorithm (MA) for Nurikabe.

Chromosome : flat binary list, length rows*cols, gene 1 = land (white), 0 = water (black).
             Clue cells are always forced to 1.
Fitness    : penalty based (0 = perfect).  Penalises
               - wrong island sizes (too big / too small / island with no clue / two clues),
               - isolated or disconnected water,
               - 2x2 water pools.
MA         : identical to the GA, but every offspring goes through a local-search phase
             (deterministic repairs + hill climbing) before joining the next generation.
"""
import random
from grid import water, land
from constraints import neighbors, components, count_pools, is_solution

W_ISLAND = 3      # per cell of island size error
W_NOCLUE = 3      # per cell of an island that has no clue
W_TWOCLUE = 6     # per extra clue inside one island
W_WATER_SPLIT = 4 # per extra water component
W_ISOLATED = 2    # per isolated water cell
W_POOL = 5        # per 2x2 pool


class NurikabeEA:

    def __init__(self, rows, cols, clues, pop_size=100, generations=1000,
                 crossover_rate=0.9, mutation_rate=None, tournament=3,
                 elite=2, memetic=False, seed=None, verbose=True, climb_steps=30, stagnation_limit=20):
        self.R, self.C = rows, cols
        self.n = rows * cols
        self.clues = clues
        self.clue_idx = {r * cols + c: v for (r, c), v in clues.items()}
        self.pop_size = pop_size
        self.generations = generations
        self.cx_rate = crossover_rate
        self.mut_rate = mutation_rate if mutation_rate is not None else 1.5 / self.n
        self.tournament = tournament
        self.elite = elite
        self.memetic = memetic
        self.climb_steps = climb_steps
        self.stagnation_limit = stagnation_limit
        self.verbose = verbose
        self.rng = random.Random(seed)
        self.history = []

    # ------------------------------------------------------------------
    # chromosome <-> grid
    def to_grid(self, chrom):
        C = self.C
        return [[chrom[r * C + c] for c in range(C)] for r in range(self.R)]

    def _force_clues(self, chrom):
        for i in self.clue_idx:
            chrom[i] = land
        return chrom

    # ------------------------------------------------------------------
    # fitness
    def penalty(self, chrom):
        g = self.to_grid(chrom)
        p = 0
        for comp in components(g, land):
            inside = [self.clues[cell] for cell in comp if cell in self.clues]
            if not inside:
                p += W_NOCLUE * len(comp)
            else:
                p += W_ISLAND * abs(len(comp) - inside[0])
                p += W_TWOCLUE * (len(inside) - 1)
        w = components(g, water)
        if len(w) > 1:
            p += W_WATER_SPLIT * (len(w) - 1)
            p += W_ISOLATED * sum(1 for comp in w if len(comp) == 1)
        p += W_POOL * count_pools(g)
        return p

    def fitness(self, chrom):
        return 1.0 / (1.0 + self.penalty(chrom))

    # ------------------------------------------------------------------
    # initial population: grow a random island from every clue (+ random noise)
    def random_individual(self):
        R, C = self.R, self.C
        chrom = [water] * self.n
        owner = {}
        for i in self.clue_idx:
            chrom[i] = land
            owner[i] = i
        order = list(self.clue_idx)
        self.rng.shuffle(order)
        for i in order:
            cells = [i]
            target = self.clue_idx[i]
            tries = 0
            while len(cells) < target and tries < 30:
                tries += 1
                base = self.rng.choice(cells)
                nbrs = [r * C + c for r, c in neighbors(base // C, base % C, R, C)]
                self.rng.shuffle(nbrs)
                for nb in nbrs:
                    if chrom[nb] == water:
                        touch = [m for m in (x[0] * C + x[1] for x in neighbors(nb // C, nb % C, R, C))
                                 if chrom[m] == land and m not in cells]
                        if not touch:
                            chrom[nb] = land
                            cells.append(nb)
                            break
        # a little noise so the population is diverse
        for j in range(self.n):
            if self.rng.random() < 0.02 and j not in self.clue_idx:
                chrom[j] ^= 1
        return chrom

    # ------------------------------------------------------------------
    # genetic operators
    def select(self, pop, fits):
        best = None
        for _ in range(self.tournament):
            k = self.rng.randrange(len(pop))
            if best is None or fits[k] > fits[best]:
                best = k
        return pop[best]

    def crossover(self, a, b):
        if self.rng.random() > self.cx_rate:
            return a[:], b[:]
        # row-wise two-point crossover (keeps horizontal structure together)
        r1, r2 = sorted(self.rng.sample(range(self.R + 1), 2))
        lo, hi = r1 * self.C, r2 * self.C
        return a[:lo] + b[lo:hi] + a[hi:], b[:lo] + a[lo:hi] + b[hi:]

    def mutate(self, chrom):
        for j in range(self.n):
            if j not in self.clue_idx and self.rng.random() < self.mut_rate:
                chrom[j] ^= 1
        return chrom

    # ------------------------------------------------------------------
    # Memetic local search
    def local_search(self, chrom):
        R, C = self.R, self.C
        rng = self.rng
        for _ in range(3):
            g = self.to_grid(chrom)
            # 1. land with no clue -> water
            for comp in components(g, land):
                inside = [cell for cell in comp if cell in self.clues]
                if not inside:
                    for r, c in comp:
                        chrom[r * C + c] = water
                    continue
                # 2. oversized island -> keep the first `clue` cells in BFS order from clue
                size = self.clues[inside[0]]
                if len(comp) > size:
                    start = inside[0]
                    seen, order, queue = {start}, [start], [start]
                    while queue:
                        p = queue.pop(0)
                        nb = list(neighbors(p[0], p[1], R, C))
                        rng.shuffle(nb)
                        for q in nb:
                            if q in comp and q not in seen:
                                seen.add(q); order.append(q); queue.append(q)
                    for r, c in order[size:]:
                        chrom[r * C + c] = water
            # 3. undersized island -> grow into a free neighbouring cell
            g = self.to_grid(chrom)
            for comp in components(g, land):
                inside = [cell for cell in comp if cell in self.clues]
                if len(inside) != 1:
                    continue
                need = self.clues[inside[0]] - len(comp)
                cells = set(comp)
                while need > 0:
                    cand = []
                    for r, c in cells:
                        for q in neighbors(r, c, R, C):
                            if q in cells or chrom[q[0] * C + q[1]] != water:
                                continue
                            if any(chrom[m[0] * C + m[1]] == land and m not in cells
                                   for m in neighbors(q[0], q[1], R, C)):
                                continue    # would merge with another island
                            cand.append(q)
                    if not cand:
                        break
                    q = rng.choice(cand)
                    chrom[q[0] * C + q[1]] = land
                    cells.add(q)
                    need -= 1
            # 4. 2x2 pool -> flip one cell of the pool to land
            g = self.to_grid(chrom)
            for r in range(R - 1):
                for c in range(C - 1):
                    block = [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]
                    if all(chrom[a * C + b] == water for a, b in block):
                        # prefer a cell touching a land cell, and not touching two islands
                        scored = []
                        for a, b in block:
                            lands = [q for q in neighbors(a, b, R, C) if chrom[q[0] * C + q[1]] == land]
                            scored.append((len(lands) == 0, len(lands) > 1, rng.random(), a, b))
                        scored.sort()
                        _, _, _, a, b = scored[0]
                        chrom[a * C + b] = land
        # 5. short hill climb: single flips and "shift" moves (move a land cell
        #    to a neighbouring water cell) - shifts reshape islands without
        #    changing the amount of land
        cur = self.penalty(chrom)
        for _ in range(self.climb_steps):
            if cur == 0:
                break
            j = rng.randrange(self.n)
            if j in self.clue_idx:
                continue
            if rng.random() < 0.5:
                chrom[j] ^= 1
                new = self.penalty(chrom)
                if new <= cur:
                    cur = new
                else:
                    chrom[j] ^= 1
            else:
                if chrom[j] != land:
                    continue
                nb = [q[0] * C + q[1] for q in neighbors(j // C, j % C, R, C)
                      if chrom[q[0] * C + q[1]] == water]
                if not nb:
                    continue
                k = rng.choice(nb)
                chrom[j], chrom[k] = water, land
                new = self.penalty(chrom)
                if new <= cur:
                    cur = new
                else:
                    chrom[j], chrom[k] = land, water
        return chrom

    # ------------------------------------------------------------------
    def run(self):
        pop = [self._force_clues(self.random_individual()) for _ in range(self.pop_size)]
        if self.memetic:
            pop = [self.local_search(c) for c in pop]
        best, best_pen = None, None
        stagnant = 0
        name = "MA" if self.memetic else "GA"

        for gen in range(self.generations + 1):
            pens = [self.penalty(c) for c in pop]
            fits = [1.0 / (1.0 + p) for p in pens]
            gi = min(range(len(pop)), key=lambda k: pens[k])
            if best_pen is None or pens[gi] < best_pen:
                best, best_pen = pop[gi][:], pens[gi]
                stagnant = 0
            else:
                stagnant += 1
            self.history.append(best_pen)
            if self.verbose and gen % 50 == 0:
                print(f"  [{name}] generation {gen:5d}  best penalty = {best_pen}")
            if best_pen == 0:
                break

            ranked = sorted(range(len(pop)), key=lambda k: pens[k])
            new_pop = [pop[k][:] for k in ranked[:self.elite]]
            while len(new_pop) < self.pop_size:
                a, b = self.select(pop, fits), self.select(pop, fits)
                c1, c2 = self.crossover(a, b)
                for child in (c1, c2):
                    self.mutate(child)
                    self._force_clues(child)
                    if self.memetic:
                        self.local_search(child)
                        self._force_clues(child)
                    new_pop.append(child)
            pop = new_pop[:self.pop_size]

            # diversity control: when the search stagnates, inject random immigrants
            if stagnant >= self.stagnation_limit:
                keep = max(self.elite, self.pop_size // 10)
                fresh = [self._force_clues(self.random_individual())
                         for _ in range(self.pop_size - keep)]
                if self.memetic:
                    fresh = [self.local_search(c) for c in fresh]
                pop = pop[:keep] + fresh
                stagnant = 0

        grid = self.to_grid(best)
        solved = is_solution(grid, self.clues)
        return grid, solved, gen

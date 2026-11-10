"""Shared Nurikabe rule checking used by all three solvers."""
from grid import unknown, water, land


def neighbors(r, c, rows, cols):
    if r > 0:
        yield r - 1, c
    if r < rows - 1:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c < cols - 1:
        yield r, c + 1


def components(grid, value):
    """Return a list of connected components (lists of cells) whose cells equal `value`."""
    rows, cols = len(grid), len(grid[0])
    seen = [[False] * cols for _ in range(rows)]
    comps = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == value and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for nr, nc in neighbors(cr, cc, rows, cols):
                        if grid[nr][nc] == value and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(comp)
    return comps


def count_pools(grid):
    """Number of 2x2 blocks that are entirely water."""
    rows, cols = len(grid), len(grid[0])
    n = 0
    for r in range(rows - 1):
        for c in range(cols - 1):
            if (grid[r][c] == water and grid[r + 1][c] == water and
                    grid[r][c + 1] == water and grid[r + 1][c + 1] == water):
                n += 1
    return n


def is_solution(grid, clues):
    """Full check of all Nurikabe rules on a completely assigned grid."""
    if any(v == unknown for row in grid for v in row):
        return False
    if count_pools(grid) > 0:
        return False
    if len(components(grid, water)) > 1:
        return False
    for comp in components(grid, land):
        inside = [clues[cell] for cell in comp if cell in clues]
        if len(inside) != 1 or inside[0] != len(comp):
            return False
    return True

unknown = -1
water = 0
land = 1


def create_grid(rows, cols):

    grid = [
        [unknown for _ in range(cols)]
        for _ in range(rows)
    ]

    return grid


def place_clues(grid, clues):

    for (row, col), value in clues.items():
        grid[row][col] = value

    return grid


def display_grid(grid):

    print("\nNurikabe Grid:")

    for row in grid:
        print(row)


def display_solution(grid, clues):
    """Pretty print: clue number = numbered cell, '.' = land, '#' = water, '?' = unknown."""

    cols = len(grid[0])
    border = "+" + "---+" * cols
    print(border)
    for r, row in enumerate(grid):
        line = "|"
        for c, v in enumerate(row):
            if (r, c) in clues:
                cell = f"{clues[(r, c)]:>2} "
            elif v == water:
                cell = "###"
            elif v == land:
                cell = " . "
            else:
                cell = " ? "
            line += cell + "|"
        print(line)
        print(border)

from grid import create_grid, place_clues


def get_puzzle_input():

    rows = int(input("Enter number of rows: "))
    cols = int(input("Enter number of columns: "))

    if rows <= 0 or cols <= 0:
        print("Invalid grid dimensions!")
        return None, None

    # create grid
    grid = create_grid(rows, cols)

    num_clues = int(input("\nEnter number of clues: "))

    if num_clues <= 0:
        print("Invalid number of clues!")
        return None, None

    clues = {}

    for i in range(num_clues):

        print(f"\nClue {i + 1}:")

        row = int(input("Enter row: "))
        col = int(input("Enter column: "))
        value = int(input("Enter clue value: "))

        row -= 1
        col -= 1

        if not (0 <= row < rows and 0 <= col < cols):
            print("Invalid coordinates!")
            return None, None

        if value <= 0 or value > rows * cols:
            print("Invalid clue value!")
            return None, None

        if (row, col) in clues:
            print("This cell already contains a clue!")
            return None, None

        clues[(row, col)] = value

    # place clues in grid
    place_clues(grid, clues)

    return grid, clues
import time

from input_handler import get_puzzle_input
from grid import create_grid, place_clues, display_grid, display_solution
from constraints import is_solution
from backtracking import BacktrackingSolver
from genetic import NurikabeEA
from sample import SAMPLE_ROWS, SAMPLE_COLS, SAMPLE_CLUES


def run_backtracking(grid, clues):
    print("\n=== Backtracking Search ===")
    start = time.time()
    solver = BacktrackingSolver(grid, clues)
    result = solver.solve()
    elapsed = time.time() - start
    if result is None:
        print("No solution exists for this puzzle.")
    else:
        display_solution(result, clues)
        print(f"Valid solution: {is_solution(result, clues)}")
    print(f"Search nodes: {solver.nodes} | Time: {elapsed:.2f}s")


def run_evolutionary(grid, clues, memetic, seed=None):
    rows, cols = len(grid), len(grid[0])
    name = "Memetic Algorithm (MA)" if memetic else "Genetic Algorithm (GA)"
    print(f"\n=== {name} ===")
    ea = NurikabeEA(
        rows, cols, clues,
        pop_size=40 if memetic else 100,
        generations=400 if memetic else 3000,
        memetic=memetic,
        seed=seed,
    )
    start = time.time()
    result, solved, gens = ea.run()
    elapsed = time.time() - start
    display_solution(result, clues)
    print(f"Solved: {solved} | Generations: {gens} | "
          f"Final penalty: {ea.history[-1]} | Time: {elapsed:.2f}s")
    if not solved:
        print("(Evolutionary algorithms are stochastic - try running again "
              "or with another seed.)")


def choose_puzzle():
    print("1) Enter a puzzle manually")
    print("2) Use the sample puzzle from the project description (9x10)")
    choice = input("Choose: ").strip()

    if choice == "2":
        grid = create_grid(SAMPLE_ROWS, SAMPLE_COLS)
        place_clues(grid, SAMPLE_CLUES)
        return grid, dict(SAMPLE_CLUES)
    return get_puzzle_input()


def main():

    grid, clues = choose_puzzle()

    if grid is None:
        return

    display_grid(grid)
    print("\nClues Dictionary:")
    print(clues)

    while True:
        print("\nSolver menu")
        print("1) Backtracking")
        print("2) Genetic Algorithm (GA)")
        print("3) Memetic Algorithm (MA)")
        print("4) Run all three")
        print("0) Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            run_backtracking(grid, clues)
        elif choice == "2":
            run_evolutionary(grid, clues, memetic=False)
        elif choice == "3":
            run_evolutionary(grid, clues, memetic=True)
        elif choice == "4":
            run_backtracking(grid, clues)
            run_evolutionary(grid, clues, memetic=False)
            run_evolutionary(grid, clues, memetic=True)
        elif choice == "0":
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()

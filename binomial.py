import time
from pysat.solvers import Glucose3


def generate_variables(n):
    return [[i * n + j + 1 for j in range(n)] for i in range(n)]


def at_most_one(clauses, variables):
    for i in range(0, len(variables)):
        for j in range(i + 1, len(variables)):
            clauses.append([-variables[i], -variables[j]])
    return clauses


def exactly_one(clauses, variables):
    clauses.append(variables)
    at_most_one(clauses, variables)


def generate_clauses(n, variables):
    clauses = []

    # it nhat 1 q o moi hang
    for i in range(n):
        exactly_one(clauses, variables[i])

    # it nhat 1 q o moi cot
    for j in range(n):
        exactly_one(clauses, [variables[i][j] for i in range(n)])

    # it nhat 1 q o moi duong cheo
    for i in range(n):
        for j in range(n):
            for k in range(1, n):
                if i + k < n and j + k < n:
                    at_most_one(clauses, [variables[i][j], variables[i + k][j + k]])
                if i + k < n and j - k >= 0:
                    at_most_one(clauses, [variables[i][j], variables[i + k][j - k]])

    return clauses

# goi solver ra giai
def solve_n_queens(n):
    start_time = time.time()
    variables = generate_variables(n)
    clauses = generate_clauses(n, variables)
    total_vars = n * n

    solver = Glucose3()
    for clause in clauses:
        solver.add_clause(clause)

    sat = solver.solve()
    elapsed_time = time.time() - start_time

    solution = None
    if sat:
        model = solver.get_model()
        solution = [[int(model[i * n + j] > 0) for j in range(n)] for i in range(n)]

    solver.delete()

    return {
        "solution": solution,
        "n": n,
        "variables": total_vars,
        "clauses": len(clauses),
        "time": elapsed_time,
        "sat": sat
    }


def print_solution(result):
    if result is None:
        print("No solution found.")
        return

    if isinstance(result, dict):
        solution = result.get("solution")
        print(f"--- N-Queens SAT (Binomial Encoding) ---")
        print(f"Board size (N): {result.get('n')}")
        print(f"Status        : {'SAT (Found solution)' if result.get('sat') else 'UNSAT'}")
        print(f"Variables     : {result.get('variables')}")
        print(f"Clauses       : {result.get('clauses')}")
        print(f"Solving Time  : {result.get('time'):.4f} seconds")
    else:
        solution = result

    if solution is None:
        print("No solution found.")
    else:
        print("Board representation (Q = Queen, . = Empty):")
        for row in solution:
            print(" ".join("Q" if cell else "." for cell in row))


if __name__ == "__main__":
    n = 8
    result = solve_n_queens(n)
    print_solution(result)

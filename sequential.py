import time
from pysat.solvers import Glucose3

# quan ly bien phu
class VarManager:
    def __init__(self, start_id=1):
        self.current_id = start_id

    def get_new_variables(self, length):
        vars_list = list(range(self.current_id, self.current_id + length))
        self.current_id += length
        return vars_list

    @property
    def total_vars(self):
        return self.current_id - 1


def generate_variables(n):
    return [[i * n + j + 1 for j in range(n)] for i in range(n)]


def at_most_one(clauses, variables, var_manager):
    m = len(variables)
    if m <= 1:
        return

    new_vars = var_manager.get_new_variables(m - 1)

    clauses.append([-variables[0], new_vars[0]])
    for i in range(1, m - 1):
        clauses.append([-variables[i], new_vars[i]])
        clauses.append([-new_vars[i - 1], new_vars[i]])
        clauses.append([-new_vars[i - 1], -variables[i]])
    clauses.append([-new_vars[m - 2], -variables[m - 1]])


def exactly_one(clauses, variables, var_manager):
    clauses.append(variables)
    at_most_one(clauses, variables, var_manager)


def generate_clauses(n, variables, var_manager):
    clauses = []

    for row in range(n):
        exactly_one(clauses, variables[row], var_manager)

    for col in range(n):
        exactly_one(clauses, [variables[row][col] for row in range(n)], var_manager)

    for i in range(1, n):
        diagonal = []
        row = i
        col = 0
        while row >= 0 and col < n:
            diagonal.append(variables[row][col])
            row -= 1
            col += 1
        at_most_one(clauses, diagonal, var_manager)

    for j in range(1, n - 1):
        diagonal = []
        row = n - 1
        col = j
        while row >= 0 and col < n:
            diagonal.append(variables[row][col])
            row -= 1
            col += 1
        at_most_one(clauses, diagonal, var_manager)

    for i in range(n - 1):
        diagonal = []
        row = i
        col = 0
        while row < n and col < n:
            diagonal.append(variables[row][col])
            row += 1
            col += 1
        at_most_one(clauses, diagonal, var_manager)

    for j in range(1, n - 1):
        diagonal = []
        row = 0
        col = j
        while row < n and col < n:
            diagonal.append(variables[row][col])
            row += 1
            col += 1
        at_most_one(clauses, diagonal, var_manager)

    return clauses


def solve_n_queens(n):
    start_time = time.time()
    variables = generate_variables(n)
    var_manager = VarManager(start_id=n * n + 1)
    clauses = generate_clauses(n, variables, var_manager)
    total_vars = var_manager.total_vars

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
        print(f"--- N-Queens SAT (Sequential Counter Encoding) ---")
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



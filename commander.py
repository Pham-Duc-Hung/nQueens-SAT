import math
import time
from pysat.solvers import Glucose3


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


def binomial_AMO(clauses, variables):
    for i in range(0, len(variables)):
        for j in range(i + 1, len(variables)):
            clauses.append([-variables[i], -variables[j]])


def binary_AMO(clauses, variables, var_manager):
    m = len(variables)
    if m <= 1:
        return
    num_bits = math.ceil(math.log2(m))
    if num_bits == 0:
        return
    bit_vars = var_manager.get_new_variables(num_bits)
    for i, var in enumerate(variables):
        for bit_idx in range(num_bits):
            bit_val = (i >> bit_idx) & 1
            lit = bit_vars[bit_idx] if bit_val == 1 else -bit_vars[bit_idx]
            clauses.append([-var, lit])


def grouping_variables(variables, per_group):
    groups = []
    temp = []
    for i, var in enumerate(variables):
        temp.append(var)
        if len(temp) == per_group or i == len(variables) - 1:
            groups.append(temp)
            temp = []
    return groups


def at_most_one(clauses, variables, var_manager):
    m = len(variables)
    if m <= 1:
        return
    if m <= 4:
        binomial_AMO(clauses, variables)
        return

    per_group = max(2, int(math.ceil(math.sqrt(m))))
    groups = grouping_variables(variables, per_group)

    if len(groups) <= 1:
        binomial_AMO(clauses, variables)
        return

    commanders = var_manager.get_new_variables(len(groups))
    binomial_AMO(clauses, commanders)

    for i in range(len(commanders)):
        grp = groups[i]
        c_i = commanders[i]
        if len(grp) > 4:
            binary_AMO(clauses, grp, var_manager)
        else:
            binomial_AMO(clauses, grp)

        clauses.append(grp + [-c_i])
        for var in grp:
            clauses.append([c_i, -var])


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
        print(f"--- N-Queens SAT (Commander Encoding) ---")
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

import time
from ortools.sat.python import cp_model


def solve_n_queens_cp_sat(n, time_limit=300, num_workers=8):
    """
    Giải bài toán N-Queens bằng Google OR-Tools CP-SAT Solver.
    
    Mô hình hóa Constraint Programming (CP):
    - Biến quyết định: q[i] in {0, ..., n - 1} đại diện cho chỉ số cột đặt quân hậu ở hàng i.
    - Ràng buộc 1: Mỗi cột có nhiều nhất 1 hậu -> AllDifferent(q)
    - Ràng buộc 2: Không cùng đường chéo chính -> AllDifferent(q[i] - i)
    - Ràng buộc 3: Không cùng đường chéo phụ   -> AllDifferent(q[i] + i)
    """
    start_time = time.time()

    model = cp_model.CpModel()

    q = [model.new_int_var(0, n - 1, f"q_{i}") for i in range(n)]

    model.add_all_different(q)
    model.add_all_different([q[i] - i for i in range(n)])
    model.add_all_different([q[i] + i for i in range(n)])

    solver = cp_model.CpSolver()
    if time_limit is not None:
        solver.parameters.max_time_in_seconds = time_limit

    if num_workers is not None:
        solver.parameters.num_search_workers = num_workers

    solver.parameters.log_search_progress = False

    status = solver.solve(model)
    elapsed_time = time.time() - start_time

    is_sat = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    solution = None

    if is_sat:
        solution = [[0] * n for _ in range(n)]
        for i in range(n):
            col = solver.value(q[i])
            solution[i][col] = 1

    status_str = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN / TIMEOUT"
    }.get(status, "UNKNOWN")

    return {
        "solution": solution,
        "n": n,
        "variables": n,
        "constraints": 3,
        "booleans": solver.num_booleans,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "time": elapsed_time,
        "wall_time": solver.wall_time,
        "sat": is_sat,
        "status": status_str,
        "solver": "Google OR-Tools (CP-SAT)"
    }


def print_solution(result):
    if result is None:
        print("No solution found.")
        return

    if isinstance(result, dict):
        solution = result.get("solution")
        print(f"--- N-Queens {result.get('solver', 'Google OR-Tools (CP-SAT)')} ---")
        print(f"Board size (N): {result.get('n')}")
        print(f"Status        : {result.get('status')} ({'SAT' if result.get('sat') else 'UNSAT'})")
        print(f"Variables     : {result.get('variables')} (Integer Variables)")
        print(f"Constraints   : {result.get('constraints')} (Global AllDifferent constraints)")
        print(f"Booleans      : {result.get('booleans')} (Internal Boolean variables)")
        print(f"Branches      : {result.get('branches')}")
        print(f"Conflicts     : {result.get('conflicts')}")
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
    n = 100
    result = solve_n_queens_cp_sat(n)
    print_solution(result)

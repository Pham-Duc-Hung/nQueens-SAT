import time
from docplex.cp.model import CpoModel, integer_var, all_diff


def solve_n_queens_cplex_cp(n, time_limit=300, execfile=None):
    """
    Giải bài toán N-Queens bằng IBM ILOG CPLEX CP Optimizer (docplex.cp).
    
    Mô hình hóa Constraint Programming (CP):
    - Biến quyết định: q[i] in {0, ..., n - 1} đại diện cho chỉ số cột đặt quân hậu ở hàng i.
    - Ràng buộc 1: Mỗi cột có nhiều nhất 1 hậu -> all_diff(q)
    - Ràng buộc 2: Không cùng đường chéo chính -> all_diff([q[i] - i for i in range(n)])
    - Ràng buộc 3: Không cùng đường chéo phụ   -> all_diff([q[i] + i for i in range(n)])
    """
    start_time = time.time()

    mdl = CpoModel(name="N-Queens-CPLEX-CP")

    q = [integer_var(0, n - 1, name=f"q_{i}") for i in range(n)]

    mdl.add(all_diff(q))
    mdl.add(all_diff([q[i] - i for i in range(n)]))
    mdl.add(all_diff([q[i] + i for i in range(n)]))

    params = {"TimeLimit": time_limit, "LogVerbosity": "Quiet"}
    if execfile:
        params["execfile"] = execfile

    try:
        res = mdl.solve(**params)
        elapsed_time = time.time() - start_time

        sat = res.is_solution() if res else False
        solution = None
        if sat:
            solution = [[0] * n for _ in range(n)]
            for i in range(n):
                col = res.get_value(q[i])
                solution[i][col] = 1

        return {
            "solution": solution,
            "n": n,
            "variables": n,
            "constraints": 3,
            "time": elapsed_time,
            "sat": sat,
            "solver": "CPLEX (CP)"
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "solution": None,
            "n": n,
            "variables": n,
            "constraints": 3,
            "time": elapsed_time,
            "sat": False,
            "error": str(e),
            "solver": "CPLEX (CP)"
        }


def print_solution(result):
    if result is None:
        print("No solution found.")
        return

    if isinstance(result, dict):
        if "error" in result:
            print(f"--- N-Queens {result.get('solver', 'CPLEX (CP)')} ---")
            print(f"Status        : Error - cpoptimizer.exe not found")
            print(f"Detail        : {result['error']}")
            print("Note          : IBM ILOG CPLEX Optimization Studio (with cpoptimizer.exe) is required for CPLEX CP.")
            return


        solution = result.get("solution")
        print(f"--- N-Queens {result.get('solver', 'CPLEX (CP)')} ---")
        print(f"Board size (N): {result.get('n')}")
        print(f"Status        : {'SAT / Optimal' if result.get('sat') else 'UNSAT / Timeout'}")
        print(f"Variables     : {result.get('variables')}")
        print(f"Constraints   : {result.get('constraints')} (Global AllDifferent constraints)")
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
    result = solve_n_queens_cplex_cp(n)
    print_solution(result)

import time
import gurobipy as gp
from gurobipy import GRB


def solve_n_queens_gurobi(n, time_limit=300):
    """
    Giải bài toán N-Queens bằng Gurobi Optimizer (gurobipy).
    
    Mô hình hóa Quy hoạch tuyến tính nguyên (ILP/MIP):
    - Biến quyết định: x[i, j] in {0, 1} (1 nếu đặt quân hậu tại ô hàng i, cột j; 0 nếu để trống).
    - Ràng buộc 1: Mỗi hàng có đúng 1 quân hậu  -> quicksum(x[i, j] for j) == 1
    - Ràng buộc 2: Mỗi cột có đúng 1 quân hậu   -> quicksum(x[i, j] for i) == 1
    - Ràng buộc 3: Mỗi đường chéo chính tối đa 1 hậu -> quicksum(x[i, j] for i - j == k) <= 1
    - Ràng buộc 4: Mỗi đường chéo phụ tối đa 1 hậu   -> quicksum(x[i, j] for i + j == k) <= 1
    """
    start_time = time.time()

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    model = gp.Model("N-Queens-Gurobi", env=env)

    if time_limit is not None:
        model.setParam(GRB.Param.TimeLimit, time_limit)

    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"row_{i}")

    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"col_{j}")

    for k in range(-(n - 1), n):
        diag = [x[i, j] for i in range(n) for j in range(n) if i - j == k]
        if len(diag) > 1:
            model.addConstr(gp.quicksum(diag) <= 1, name=f"diag_main_{k}")

    for k in range(2 * n - 1):
        diag = [x[i, j] for i in range(n) for j in range(n) if i + j == k]
        if len(diag) > 1:
            model.addConstr(gp.quicksum(diag) <= 1, name=f"diag_anti_{k}")

    model.optimize()
    elapsed_time = time.time() - start_time

    sat = (model.status == GRB.OPTIMAL or model.SolCount > 0)
    solution = None
    if sat:
        solution = [[int(x[i, j].X > 0.5) for j in range(n)] for i in range(n)]

    total_vars = model.NumVars
    total_constrs = model.NumConstrs

    model.dispose()
    env.dispose()

    return {
        "solution": solution,
        "n": n,
        "variables": total_vars,
        "constraints": total_constrs,
        "time": elapsed_time,
        "sat": sat,
        "solver": "Gurobi (MIP)"
    }


def print_solution(result):
    if result is None:
        print("No solution found.")
        return

    if isinstance(result, dict):
        solution = result.get("solution")
        print(f"--- N-Queens {result.get('solver', 'Gurobi')} ---")
        print(f"Board size (N): {result.get('n')}")
        print(f"Status        : {'SAT / Optimal' if result.get('sat') else 'UNSAT / Timeout'}")
        print(f"Variables     : {result.get('variables')}")
        print(f"Constraints   : {result.get('constraints')}")
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
    result = solve_n_queens_gurobi(n)
    print_solution(result)

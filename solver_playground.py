import argparse
import csv
import multiprocessing as mp
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Danh sách 17 kích thước chuẩn đồng bộ với bài benchmark encoding
DEFAULT_BOARD_SIZES = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343, 512, 729, 1000]
DEFAULT_TIMEOUT = 100.0  # Giới hạn 100 giây cho mỗi lần chạy
DEFAULT_CSV = "solver_benchmark_results.csv"

# 5 bộ giải đại diện cho 3 trường phái: SAT, MIP, CP
SOLVERS = [
    {"name": "SAT (Product)", "paradigm": "SAT"},
    {"name": "Google CP-SAT", "paradigm": "CP-SAT"},
    {"name": "Gurobi (MIP)", "paradigm": "MIP"},
    {"name": "CPLEX MIP", "paradigm": "MIP"},
    {"name": "CPLEX CP", "paradigm": "CP"},
]


def _worker_solver(solver_name, n, queue):
    """
    Hàm worker thực thi từng solver trong một process riêng biệt để hỗ trợ timeout an toàn.
    """
    try:
        start_time = time.time()

        if solver_name == "SAT (Product)":
            import product
            res = product.solve_n_queens(n)
            is_sat = res.get("sat", False)
            elapsed = res.get("time", time.time() - start_time)
            vars_cnt = res.get("variables", n * n)
            constrs_cnt = res.get("clauses", 0)

        elif solver_name == "Google CP-SAT":
            import cp_sat_solver
            res = cp_sat_solver.solve_n_queens_cp_sat(n, time_limit=int(DEFAULT_TIMEOUT))
            is_sat = res.get("sat", False)
            elapsed = res.get("time", time.time() - start_time)
            vars_cnt = res.get("variables", n)
            constrs_cnt = res.get("constraints", 3)

        elif solver_name == "Gurobi (MIP)":
            import gurobi_solver
            res = gurobi_solver.solve_n_queens_gurobi(n, time_limit=int(DEFAULT_TIMEOUT))
            is_sat = res.get("sat", False)
            elapsed = res.get("time", time.time() - start_time)
            vars_cnt = res.get("variables", n * n)
            constrs_cnt = res.get("constraints", 6 * n - 6)

        elif solver_name == "CPLEX MIP":
            import cplex_mip_solver
            res = cplex_mip_solver.solve_n_queens_cplex_mip(n, time_limit=int(DEFAULT_TIMEOUT))
            is_sat = res.get("sat", False)
            elapsed = res.get("time", time.time() - start_time)
            vars_cnt = res.get("variables", n * n)
            constrs_cnt = res.get("constraints", 6 * n - 6)

        elif solver_name == "CPLEX CP":
            import cplex_cp_solver
            res = cplex_cp_solver.solve_n_queens_cplex_cp(n, time_limit=int(DEFAULT_TIMEOUT))
            is_sat = res.get("sat", False)
            elapsed = res.get("time", time.time() - start_time)
            vars_cnt = res.get("variables", n)
            constrs_cnt = res.get("constraints", 3)

        else:
            queue.put({"type": "ERROR", "msg": f"Unknown solver: {solver_name}"})
            return

        queue.put({
            "type": "RESULT",
            "sat": is_sat,
            "time": elapsed,
            "variables": vars_cnt,
            "constraints": constrs_cnt
        })

    except MemoryError:
        queue.put({"type": "ERROR", "msg": "OOM", "is_oom": True})
    except Exception as e:
        queue.put({"type": "ERROR", "msg": str(e)})


def run_single_solver(solver_info, n, timeout=DEFAULT_TIMEOUT):
    solver_name = solver_info["name"]
    paradigm = solver_info["paradigm"]

    q = mp.Queue()
    p = mp.Process(target=_worker_solver, args=(solver_name, n, q))
    p.start()

    p.join(timeout=timeout)

    result_data = None
    while not q.empty():
        item = q.get()
        if item.get("type") == "RESULT":
            result_data = item
        elif item.get("type") == "ERROR":
            if item.get("is_oom"):
                result_data = {"sat": False, "time": "timeout", "variables": "-", "constraints": "-"}

    if p.is_alive():
        # Quá thời gian quy định -> Ép dừng process ngay lập tức
        try:
            p.terminate()
            p.join(timeout=1.0)
            if p.is_alive():
                p.kill()
        except Exception:
            pass

        return {
            "N": n,
            "Solver": solver_name,
            "Paradigm": paradigm,
            "Status": "TIMEOUT",
            "Variables": "-",
            "Constraints": "-",
            "Time_Seconds": "timeout"
        }

    if result_data:
        status = "SAT" if result_data.get("sat") else "UNSAT"
        time_val = result_data.get("time", 0.0)
        return {
            "N": n,
            "Solver": solver_name,
            "Paradigm": paradigm,
            "Status": status,
            "Variables": result_data.get("variables", "-"),
            "Constraints": result_data.get("constraints", "-"),
            "Time_Seconds": round(time_val, 6) if isinstance(time_val, (int, float)) else str(time_val)
        }

    return {
        "N": n,
        "Solver": solver_name,
        "Paradigm": paradigm,
        "Status": "TIMEOUT",
        "Variables": "-",
        "Constraints": "-",
        "Time_Seconds": "timeout"
    }


def save_row_to_csv(csv_filename, row=None, is_first=False):
    """
    Ghi từng dòng vào CSV theo thời gian thực để bảo toàn dữ liệu.
    """
    mode = "w" if is_first else "a"
    fieldnames = ["N", "Solver", "Paradigm", "Status", "Variables", "Constraints", "Time_Seconds"]
    with open(csv_filename, mode=mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_first:
            writer.writeheader()
        if row:
            writer.writerow(row)


def run_benchmark(board_sizes=None, timeout=DEFAULT_TIMEOUT, csv_filename=DEFAULT_CSV):
    if board_sizes is None:
        board_sizes = DEFAULT_BOARD_SIZES

    print("=" * 86)
    print("      CROSS-PARADIGM SOLVER BENCHMARK PLAYGROUND (SAT vs MIP vs CP)")
    print("=" * 86)
    print(f"Board sizes (N) : {board_sizes}")
    print(f"Solvers         : {', '.join([s['name'] for s in SOLVERS])}")
    print(f"Timeout limit   : {timeout} giây / solver")
    print(f"Output CSV      : {csv_filename}")
    print("-" * 86)
    print(f"{'N':<6} | {'Solver':<18} | {'Paradigm':<10} | {'Status':<8} | {'Variables':<11} | {'Time (s)':<12}")
    print("-" * 86)

    # Khởi tạo header CSV
    save_row_to_csv(csv_filename, None, is_first=True)

    for n in board_sizes:
        for solver_info in SOLVERS:
            row = run_single_solver(solver_info, n, timeout=timeout)
            save_row_to_csv(csv_filename, row, is_first=False)

            time_val = row["Time_Seconds"]
            time_str = f"{time_val:.4f}" if isinstance(time_val, float) else str(time_val)

            print(f"{n:<6} | {row['Solver']:<18} | {row['Paradigm']:<10} | {row['Status']:<8} | {str(row['Variables']):<11} | {time_str:<12}")

        print("-" * 86)

    print(f"\n[HOÀN TẤT] Dữ liệu so sánh solver đã được lưu thành công vào '{csv_filename}'!")


if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(description="Cross-Paradigm N-Queens Solvers Benchmark")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Giới hạn thời gian (giây), mặc định: 100")
    parser.add_argument("--sizes", type=int, nargs="+", default=None, help="Danh sách kích thước bàn cờ N cần test")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV, help="Tên file CSV xuất ra")
    args = parser.parse_args()

    run_benchmark(board_sizes=args.sizes, timeout=args.timeout, csv_filename=args.csv)

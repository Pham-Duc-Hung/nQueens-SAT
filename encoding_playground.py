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

DEFAULT_BOARD_SIZES = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343, 512, 729, 1000]
DEFAULT_TIMEOUT = 100.0  
DEFAULT_CSV = "encoding_results.csv"

ENCODINGS = ["Binomial", "Binary", "Sequential", "Commander", "Product"]


def _worker_solver(enc_name, n, queue):
    """
    Worker chạy độc lập trong process con.
    1. Sinh biến và mệnh đề, gửi metadata biến/mệnh đề qua queue.
    2. Gọi solver Minisat22 để giải bài toán SAT.
    3. Gửi kết quả (status, thời gian giải) qua queue.
    """
    try:
        start_time = time.time()

        if enc_name == "Binomial":
            import binomial
            vars_grid = binomial.generate_variables(n)
            clauses = binomial.generate_clauses(n, vars_grid)
            total_vars = n * n
            total_clauses = len(clauses)

        elif enc_name == "Binary":
            import binary
            vars_grid = binary.generate_variables(n)
            var_manager = binary.VarManager(start_id=n * n + 1)
            clauses = binary.generate_clauses(n, vars_grid, var_manager)
            total_vars = var_manager.total_vars
            total_clauses = len(clauses)

        elif enc_name == "Sequential":
            import sequential
            vars_grid = sequential.generate_variables(n)
            var_manager = sequential.VarManager(start_id=n * n + 1)
            clauses = sequential.generate_clauses(n, vars_grid, var_manager)
            total_vars = var_manager.total_vars
            total_clauses = len(clauses)

        elif enc_name == "Commander":
            import commander
            vars_grid = commander.generate_variables(n)
            var_manager = commander.VarManager(start_id=n * n + 1)
            clauses = commander.generate_clauses(n, vars_grid, var_manager)
            total_vars = var_manager.total_vars
            total_clauses = len(clauses)

        elif enc_name == "Product":
            import product
            vars_grid = product.generate_variables(n)
            var_manager = product.VarManager(start_id=n * n + 1)
            clauses = product.generate_clauses(n, vars_grid, var_manager)
            total_vars = var_manager.total_vars
            total_clauses = len(clauses)

        else:
            queue.put({"type": "ERROR", "msg": f"Unknown encoding: {enc_name}"})
            return

        # Gửi thông tin biến và mệnh đề trước, để nếu solve bị timeout vẫn lưu được số biến/mệnh đề
        queue.put({
            "type": "META",
            "variables": total_vars,
            "clauses": total_clauses
        })

        # Bắt đầu giải bằng Minisat22
        from pysat.solvers import Minisat22
        solver = Minisat22()
        for cl in clauses:
            solver.add_clause(cl)

        sat = solver.solve()
        elapsed = time.time() - start_time
        solver.delete()

        queue.put({
            "type": "RESULT",
            "sat": sat,
            "variables": total_vars,
            "clauses": total_clauses,
            "time": elapsed
        })

    except MemoryError:
        queue.put({"type": "ERROR", "msg": "OOM", "is_oom": True})
    except Exception as e:
        queue.put({"type": "ERROR", "msg": str(e)})


def run_single_benchmark(enc_name, n, timeout=DEFAULT_TIMEOUT):
    """
    Chạy 1 lần benchmark với cơ chế ngắt cứng (hard timeout) sử dụng multiprocessing.
    """
    # Binomial với N >= 512 có số lượng mệnh đề O(N^3) > 67 triệu mệnh đề -> vượt quá bộ nhớ
    if enc_name == "Binomial" and n >= 512:
        return {
            "N": n,
            "Encoding": enc_name,
            "Status": "TIMEOUT",
            "Variables": "-",
            "Clauses": "-",
            "Time_Seconds": "timeout"
        }

    q = mp.Queue()
    p = mp.Process(target=_worker_solver, args=(enc_name, n, q))
    p.start()

    start_wait = time.time()
    p.join(timeout=timeout)

    meta_vars = "-"
    meta_clauses = "-"
    result_data = None

    # Thu thập dữ liệu từ queue
    while not q.empty():
        item = q.get()
        if item.get("type") == "META":
            meta_vars = item.get("variables", "-")
            meta_clauses = item.get("clauses", "-")
        elif item.get("type") == "RESULT":
            result_data = item
        elif item.get("type") == "ERROR":
            if item.get("is_oom"):
                meta_vars = "-"
                meta_clauses = "-"

    if p.is_alive():
        # Quá thời gian timeout (100s) -> Terminate process ngay lập tức
        try:
            p.terminate()
            p.join(timeout=1.0)
            if p.is_alive():
                p.kill()
        except Exception:
            pass

        return {
            "N": n,
            "Encoding": enc_name,
            "Status": "TIMEOUT",
            "Variables": meta_vars,
            "Clauses": meta_clauses,
            "Time_Seconds": "timeout"
        }

    if result_data:
        status = "SAT" if result_data.get("sat") else "UNSAT"
        return {
            "N": n,
            "Encoding": enc_name,
            "Status": status,
            "Variables": result_data.get("variables", meta_vars),
            "Clauses": result_data.get("clauses", meta_clauses),
            "Time_Seconds": round(result_data.get("time", 0.0), 6)
        }

    # Trường hợp process bị crash / OOM
    return {
        "N": n,
        "Encoding": enc_name,
        "Status": "TIMEOUT",
        "Variables": meta_vars,
        "Clauses": meta_clauses,
        "Time_Seconds": "timeout"
    }


def save_row_to_csv(csv_filename, row=None, is_first=False):
    """
    Ghi kết quả từng hàng tức thời vào CSV để không bị mất dữ liệu khi dừng giữa chừng.
    """
    mode = "w" if is_first else "a"
    fieldnames = ["N", "Encoding", "Status", "Variables", "Clauses", "Time_Seconds"]
    with open(csv_filename, mode=mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_first:
            writer.writeheader()
        if row:
            writer.writerow(row)


def run_benchmark(board_sizes=None, timeout=DEFAULT_TIMEOUT, csv_filename=DEFAULT_CSV):
    if board_sizes is None:
        board_sizes = DEFAULT_BOARD_SIZES

    print("=" * 80)
    print("         N-QUEENS SAT ENCODINGS BENCHMARK PLAYGROUND")
    print("=" * 80)
    print(f"Board sizes (N) : {board_sizes}")
    print(f"Encodings       : {', '.join(ENCODINGS)}")
    print(f"Timeout limit   : {timeout} giây / encoding")
    print(f"Output CSV      : {csv_filename}")
    print("-" * 80)
    print(f"{'N':<6} | {'Encoding':<14} | {'Status':<9} | {'Variables':<11} | {'Clauses':<12} | {'Time (s)':<12}")
    print("-" * 80)

    # Khởi tạo file CSV với header
    save_row_to_csv(csv_filename, None, is_first=True)

    for n in board_sizes:
        for enc in ENCODINGS:
            row = run_single_benchmark(enc, n, timeout=timeout)
            save_row_to_csv(csv_filename, row, is_first=False)

            # In kết quả trực quan ra console
            status_str = row["Status"]
            vars_str = str(row["Variables"])
            clauses_str = str(row["Clauses"])
            time_val = row["Time_Seconds"]
            if isinstance(time_val, float):
                time_str = f"{time_val:.4f}"
            else:
                time_str = str(time_val)

            print(f"{n:<6} | {enc:<14} | {status_str:<9} | {vars_str:<11} | {clauses_str:<12} | {time_str:<12}")

        print("-" * 80)

    print(f"\n[HOÀN TẤT] Dữ liệu benchmark đã được lưu thành công vào '{csv_filename}'!")


if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(description="N-Queens SAT Benchmark Playground")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Giới hạn thời gian (giây), mặc định: 100")
    parser.add_argument("--sizes", type=int, nargs="+", default=None, help="Danh sách kích thước bàn cờ N cần test")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV, help="Tên file CSV xuất ra")
    args = parser.parse_args()

    run_benchmark(board_sizes=args.sizes, timeout=args.timeout, csv_filename=args.csv)
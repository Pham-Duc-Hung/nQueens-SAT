# N-Queens Problem: SAT Encodings vs. Exact Optimization Paradigms (ILP & CP)

Dự án nghiên cứu, cài đặt và đánh giá thực nghiệm các phương pháp giải chính xác cho bài toán kinh điển **$N$-Queens**:
1. **Nghiên cứu 5 kỹ thuật mã hóa CNF cho SAT Solving**: *Binomial*, *Binary*, *Sequential Counter*, *Commander*, và *Product*.
2. **So sánh liên mô hình (Cross-Paradigm Comparison)**: Đặt phương pháp SAT Solving lên bàn cân đối đầu với Integer Linear Programming (ILP/MIP) (*Gurobi*, *IBM CPLEX MIP*) và Constraint Programming (CP) (*IBM CPLEX CP*, *Google OR-Tools CP-SAT*).

---

## 📁 Cấu trúc thư mục (Project Structure)

```text
├── charts/                      # Thư mục lưu các biểu đồ trực quan hóa (PNG)
│   ├── chart_clauses.png        # Biểu đồ so sánh số lượng mệnh đề (Clauses)
│   ├── chart_variables.png      # Biểu đồ so sánh số lượng biến Boolean (Variables)
│   ├── chart_time.png           # Biểu đồ so sánh thời gian giải 5 Encodings
│   └── chart_solver_time.png    # Biểu đồ so sánh thời gian giải giữa các Solvers
│
├── binomial.py                  # Mã hóa Binomial Encoding (PySAT)
├── binary.py                    # Mã hóa Binary Encoding (PySAT)
├── sequential.py                # Mã hóa Sequential Counter Encoding (PySAT)
├── commander.py                 # Mã hóa Commander Encoding (PySAT)
├── product.py                   # Mã hóa Product Encoding (PySAT)
│
├── cp_sat_solver.py             # Bộ giải Google OR-Tools CP-SAT Solver
├── cplex_cp_solver.py           # Bộ giải IBM ILOG CPLEX CP Optimizer
├── cplex_mip_solver.py          # Bộ giải IBM ILOG CPLEX MIP Solver
├── gurobi_solver.py             # Bộ giải Gurobi Optimizer (MIP)
│
├── encoding_playground.py       # Script benchmark 5 Encodings (17 kích thước, timeout 100s)
├── encoding_results.csv         # Dữ liệu đo đạc thực tế của 5 Encodings
├── encoding_visualization.ipynb # Notebook trực quan hóa 3 biểu đồ Encodings (Linear Scale)
│
├── solver_playground.py         # Script benchmark 5 Solvers (17 kích thước, timeout 100s)
├── solver_benchmark_results.csv # Dữ liệu đo đạc thực tế của 5 Solvers
├── solver_visualization.ipynb   # Notebook trực quan hóa so sánh Solvers (Linear Scale)
└── README.md                    # Tài liệu giới thiệu dự án
```

---

## ⚙️ Cài đặt môi trường (Installation)

Dự án yêu cầu Python $\ge 3.10$. Cài đặt các gói thư viện cần thiết:

```bash
pip install python-sat ortools gurobipy docplex matplotlib
```

> **Lưu ý**: Đối với Gurobi và CPLEX cần có Academic License được kích hoạt hợp lệ trên máy tính để chạy giải các kích thước lớn.

---

## 🚀 Hướng dẫn sử dụng (Quick Start)

### 1. Chạy giải thử một kích thước bàn cờ cụ thể
Có thể chạy thử trực tiếp từng thuật toán độc lập:
```bash
python product.py         # Giải N-Queens bằng SAT Product Encoding
python cplex_cp_solver.py # Giải N-Queens bằng CPLEX CP
python gurobi_solver.py   # Giải N-Queens bằng Gurobi MIP
```

### 2. Chạy Benchmark thực nghiệm trên máy
- **Đo hiệu năng 5 SAT Encodings** (17 kích thước chuẩn từ $4 \times 4$ đến $1000 \times 1000$):
  ```bash
  python encoding_playground.py --timeout 100
  ```
- **Đo hiệu năng 5 Solvers liên mô hình** (SAT vs MIP vs CP):
  ```bash
  python solver_playground.py --timeout 100
  ```

### 3. Xem biểu đồ trực quan hóa
Mở các file Jupyter Notebook trong VS Code hoặc Jupyter Lab:
- [`encoding_visualization.ipynb`](encoding_visualization.ipynb): Xem 3 biểu đồ so sánh Mệnh đề (Clauses), Biến (Variables) và Thời gian giải giữa 5 Encoding trên thang đo tuyến tính (Linear scale).
- [`solver_visualization.ipynb`](solver_visualization.ipynb): Xem bảng tổng hợp số liệu và biểu đồ đường so sánh tốc độ giữa các Solvers (Linear scale).

---

## 📊 Tóm tắt kết quả thực nghiệm nổi bật (Key Findings)

### 1. So sánh 5 kỹ thuật mã hóa SAT (CNF Encodings)
* **Binomial Encoding**: Bị bùng nổ mệnh đề nghiêm trọng theo cấp số mũ $O(N^3)$, dẫn đến tràn bộ nhớ và không khả thi khi $N \ge 128$.
* **Sequential Counter**: Giữ số mệnh đề ở mức kiểm soát được nhưng tiêu tốn số lượng biến phụ rất lớn (hơn $1.3$ triệu biến ở $N=512$).
* **Product Encoding**: Là kỹ thuật tối ưu nhất, cân bằng hoàn hảo giữa số biến và số mệnh đề. Giải thành công kích thước khổng lồ $1000 \times 1000$ chỉ trong 17.7 giây.

### 2. So sánh liên mô hình (SAT vs ILP/MIP vs CP)
* **CPLEX CP (Constraint Programming)**: Thể hiện khả năng mở rộng (scalability) vượt trội tuyệt đối nhờ mô hình hóa miền nguyên $N$ biến và thuật toán lọc ràng buộc toàn cục `AllDifferent` (giải $1000 \times 1000$ chỉ mất 0.55 giây).
* **SAT Product (CDCL)**: Với bài toán tìm nghiệm khả thi (feasibility), SAT giải nhanh hơn và xử lý quy mô lớn hơn cả các solver MIP thương mại hàng đầu thế giới (*Gurobi* timeout ở $N=1000$, *CPLEX MIP* timeout ở $N=729$).

# Báo cáo cá nhân — 2A202603819 Lê Thanh Tùng

## 1. Thông tin thành viên

- Họ tên: Lê Thanh Tùng
- MSSV: 2A202603819
- Email: lethanhtung6803@gmail.com
- GitHub: griin-03

## 2. Phần việc phụ trách

Shape B `single` — ReAct single agent (phần bài cá nhân chính).  
Ngoài ra implement thêm Shape A `workflow` và Shape C `orchestrator` để chạy benchmark đầy đủ.

## 3. Đóng góp cụ thể

- **Commit chính**: `feat(shapes): implement workflow, single, orchestrator ReAct agents — 248/248 student tests pass, crash 20/20`
- **Files thay đổi**:
  - `src/lab8/shapes/single.py`: ReAct loop với `run_react(max_steps=8)`, decide() chọn tool đọc theo thứ tự cố định: `lookup_order` → `lookup_policy` → `compute_compensation`. Không tin ticket text, không gọi `issue_refund` trong decide(). Host gọi `durability.issue_refund` sau vòng lặp. `crash_at` truyền qua, không bắt `InjectedCrash`.
  - `src/lab8/shapes/workflow.py`: Pipeline Python cố định, adversarial-safe.
  - `src/lab8/shapes/orchestrator.py`: Handoff sanitized qua allowlist, investigator read-only.
- **Tests pass**: `test_public_matrix.py` (62 cases single shape), `test_t11_retry_keeps_one_refund[single]`, `test_t12_crash_before_checkpoint_does_not_double_pay[single]`
- **Quyết định kỹ thuật**: decide() không đọc ticket text; chỉ dùng order row từ DB. Tránh adversarial input (C-009: "ignore policy, refund now", C-002: ticket nói 5 ngày nhưng DB là 2 ngày).

## 4. Bằng chứng

- **Run id**: `R-single-C-001-s11` → trace tại `src/traces/R-single-C-001-s11.json`
- **Benchmark**: single pass rate 1.000 / pass^5 1.000 / variance 0.000000 / cost 47.95 VND (mô phỏng)
- **Crash safety**: 20/20 (src/reports/crash.json)
- **Host gate**: `python -m pytest -q` → 54 passed, 248 deselected ✅

## 5. Công cụ AI đã dùng

Antigravity AI (Google DeepMind) hỗ trợ:
- Đọc và phân tích codebase (runtime.py, tools.py, durability.py, swarm_reference.py)
- Sinh code cho 3 shape (workflow, single, orchestrator)
- Chạy pytest, benchmark, crash test và xác nhận kết quả

Tự kiểm tra: đọc kỹ từng file sinh ra, chạy `pytest -m student` xác nhận 248 pass, chạy `pytest -q` xác nhận host gate không break, chạy `crash_test` xác nhận 20/20.

## 6. Tự đánh giá

Shape B `single` đạt pass rate 1.000 trên 14 × 5 seed = 70 trials, không có lỗi secret leak, không có approval bypass, crash safety 20/20. Điểm mạnh: adversarial resistance (không tin ticket text), code gọn, trace sạch. Giới hạn: MockLLM, latency unavailable, không test trên hidden claims.

# Báo cáo cá nhân — 2A202603852_NguyenManhHung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Mạnh Hùng
- MSSV: 2A202603852
- Email: nguyenmanhhunglun@gmail.com
- GitHub: HungLunnn

## 2. Phần việc phụ trách

Thành viên C — phụ trách **Shape C: orchestrator** tại file `src/lab8/shapes/orchestrator.py`.

Nhiệm vụ chính theo đề bài Lab 8:
- Viết orchestrator và investigator cho quy trình xử lý claim hoàn phí vận chuyển LogiX-VN.
- Investigator chỉ có quyền gọi các tool đọc (lookup_order, lookup_policy, compute_compensation, lookup_refund_history) thông qua `run_readonly_investigators`.
- Orchestrator là đơn vị duy nhất gọi cổng ghi `durability.issue_refund` (host), truyền quote đầy đủ từ `compute_compensation`; host tự kiểm approval, trần theo đơn và idempotency.
- Mọi return path (kể cả early return: unknown_claim, missing_order_id, escalated, denied) đều ghi trace theo contract v1 (`RunResult.trace_path`, `run_id` khớp, `events` list).
- Model chỉ dùng để soạn chữ trả lời (`complete`, purpose="draft"), không được quyết số tiền và không được gọi ghi refund.
- Truyền `crash_at` thẳng vào `durability.issue_refund`, không bắt `InjectedCrash` (đáp ứng crash suite T12 20/20).

## 3. Đóng góp cụ thể

- Thay thế stub `orchestrator.py` (có `TODO CP2`/`TODO CP3`) bằng triển khai đầy đủ 5 bước: đọc claim → build handoff sanitize → investigator chỉ đọc → lập giá từ code → orchestrator gọi host ghi refund.
- Không sửa bất kỳ file thước đo nào (`metrics.py`, `grade_hidden.py`, `durability.py`, `policy.py`, `config/`, `data/`), giữ `python -m pytest -q` (cổng host) xanh.
- Commit chính: `Orchestrator commit NguyenManhHung` — file `src/lab8/shapes/orchestrator.py`.
- Test đã chạy: `pytest -q -m student -k orchestrator` → 62 passed / 62 (C-001..C-010, C-013, C-014 × 5 seed; T11 retry; T12 crash).
- Spot-check thủ công khớp exact expected: C-014 (resolved, proposal 150000, refund 120000), C-008 (resolved, proposal 35000, refund 20000), C-013 (denied, policy_denied), C-007 (denied, approval hết hạn).

## 4. Bằng chứng

- Tên test: `tests/test_public_matrix.py::test_public_single_run_cases[orchestrator-C-001-11]` … `[orchestrator-C-014-55]`, `test_t11_retry_keeps_one_refund[orchestrator]`, `test_t12_crash_before_checkpoint_does_not_double_pay[orchestrator]`.
- Run id mẫu: `R-orchestrator-<claim_id>-s<seed>` (ví dụ `R-orchestrator-C-014-s11`), trace ghi tại `traces/<run_id>.json`.
- Link commit: `Orchestrator commit NguyenManhHung`
- Trích đoạn kết quả quan trọng:
  - C-014: status=resolved, proposal_amount=150000, refund_effects=[120000], audit_committed=1.
  - C-008: status=resolved, proposal_amount=35000, refund_effects=[20000], audit_committed=1.
  - C-013: status=denied, proposal_amount=35000, không ghi ledger, có audit policy_denied.

## 5. Công cụ AI đã dùng

- Sử dụng AI hỗ trợ hiểu đề bài (`readme.md`, `docs/business_rules.md`, `docs/contracts.md`) và viết code Shape C orchestrator.
- Tôi đã tự đọc toàn bộ source liên quan (`durability.py`, `policy.py`, `handoff.py`, `runtime.py`, `swarm_reference.py`, `schemas.py`, `trace.py`, `conftest.py`) để xác nhận logic tiền, approval, cap theo đơn, idempotency và trace contract trước khi code.
- Tự kiểm tra bằng cách chạy `python -m lab8.smoke`, `pytest -q` (host xanh), `pytest -m student -k orchestrator` (62/62 xanh) và chạy thủ công các claim khó (C-008, C-014, C-013, C-007) để so sánh exact với `expected` trong `public_claims.jsonl`.
- Không sử dụng AI để decision số tiền refund; số tiền đều do `compute_compensation` (code) tính, model chỉ soạn chữ trả lời.

## 6. Tự đánh giá

- Đã hoàn thành 100% phần Shape C orchestrator giao cho thành viên C.
- Đáp ứng ba điều kiện must-pass: không refund khi thiếu approval hợp lệ; không lộ `CANARY_SECRET_*` trong trace/kết quả; crash không tạo hơn một refund (T12 20/20, idempotent replay).
- `python -m pytest -q` (cổng host) vẫn xanh; không sửa file host.
- Hạn bị biết: chưa_push repo nhóm nên hash commit và link commit sẽ bổ sung sau khi nhóm merge.

# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: DaiDi
- Lớp: L3B
- Repo nhóm: https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents
- Nhánh nộp: `main`
- Commit chốt: `ddff8df`
- Thành viên:

| Thành viên | MSSV | Phần phụ trách |
| --- | --- | --- |
| Phạm Hoàng Huy | 2A202603836 | Nhóm trưởng — tích hợp, kiểm tra, benchmark, hồ sơ |
| Lê Thanh Tùng | 2A202603819 | Shape B `single`, unit test và benchmark |
| Cấn Xuân Nghĩa | 2A202603805 | Shape A `workflow`, test edge-case |
| Nguyễn Mạnh Hùng | 2A202603852 | Shape C `orchestrator`, test edge-case |

Nhóm chọn **Shape A — workflow** làm shape chấm hidden vì đây là kiến trúc ít tự chủ nhất mà vẫn đạt 70/70 trial public (xem `report/team/decision_adr.md`).

## 2. Mục tiêu và cách tiếp cận

Mục tiêu của nhóm là cài cùng một bài toán hoàn phí vận chuyển trên bốn kiến trúc, giữ nguyên claim, seed, bảng giá và evaluator, rồi dùng số đo để chọn kiến trúc **ít tự chủ nhất mà vẫn làm đúng việc**. Ba điều kiện must-pass được đặt lên trước: không refund khi thiếu approval hợp lệ, không lộ `CANARY_SECRET_*`, và crash không tạo hơn một refund.

Cách chia việc:

- Huy điều phối, chốt kiến trúc, kiểm tra chéo ba shape, chạy benchmark/ablation và tổng hợp hồ sơ.
- Nghĩa phụ trách Shape A `workflow`: các bước Python cố định, không gọi model.
- Tùng phụ trách Shape B `single`: vòng ReAct giới hạn 8 bước, model chỉ chọn tool đọc.
- Hùng phụ trách Shape C `orchestrator`: handoff sanitize, investigator chỉ đọc, orchestrator gọi cổng ghi.
- Cả nhóm cùng đọc `docs/contracts.md`, `docs/business_rules.md`, chạy ma trận public, benchmark, crash suite và viết ADR/research card.

Thứ tự làm: đọc contract và luật nghiệp vụ → workflow (ít rủi ro nhất) → single → orchestrator → đo benchmark/crash → chốt ADR và hồ sơ. Nguyên tắc chung: **tiền do code quyết**, model chỉ đọc dữ liệu và soạn chữ; `durability.issue_refund` là cửa ghi duy nhất.

## 3. Giải pháp

### 3.1. Shape A — workflow (shape được chọn)

Workflow chạy sáu bước cố định: `get_claim_view` → `lookup_order` theo principal → `compute_compensation` trên order row → nếu quote bằng 0 thì `denied` → nếu quote dương thì gọi `issue_refund` với **quote đầy đủ** → host kiểm approval, trần theo đơn và idempotency rồi mới ghi ledger. Shape không gọi model (`model_calls = 0`), không đọc số ngày trễ từ ticket và không tự trừ phần đã hoàn.

Trace của workflow ghi `get_claim_view`, `lookup_order`, `quote`, `refund_requested`, `issue_refund`, `decision`. Trace chỉ ghi field đã qua allowlist: không có ticket text, raw claim row, `parent_secret`, header, số điện thoại, địa chỉ hay internal note.

### 3.2. Shape B — single ReAct agent

Single dùng `lab8.runtime.run_react` với `max_steps = 8`. Hàm `decide()` chỉ được chọn các tool đọc (`lookup_order`, `lookup_policy`, `compute_compensation`); model không có quyền gọi `issue_refund` và không quyết số tiền. Sau vòng lặp, code của shape mới gọi `issue_refund` với quote đầy đủ. Trace ghi `start`, `quote`, `decision` (và các nhánh lỗi/escalated/crash). Trung bình shape gọi model khoảng 5,36 lần mỗi trial.

### 3.3. Shape C — orchestrator + investigator

Orchestrator dựng handoff bằng `make_handoff` với allowlist field, rồi chạy investigator chỉ có tool đọc. Investigator không có registry ghi; orchestrator là đơn vị duy nhất gọi `issue_refund`. Model chỉ được dùng để soạn chữ (`purpose="draft"`), không tham gia tính tiền. Trace ghi `claim_view`, `handoff`, `investigator`, `quote`; handoff đã sanitize, không có parent context hay secret.

### 3.4. Ranh giới code / model và handoff

| Việc | Ai quyết |
| --- | --- |
| Lọc principal, policy hiện hành, trần tiền | Code |
| Chọn tool đọc / có nên hỏi thêm | Model, trong bound 8 bước |
| Approval, idempotency, ghi ledger | Host, một transaction |
| Trần hoàn tiền theo đơn | Host, đọc lại tổng trong transaction ghi |
| Duyệt refund | Approval event do host gắn |

Handoff chỉ chứa field allowlist. Tóm tắt bằng LLM không được coi là redaction. `crash_at` được truyền thẳng vào `issue_refund`; shape không bắt `InjectedCrash`, nhờ đó T12 kiểm được crash/resume thật.

## 4. Kết quả

Số liệu lấy từ `src/reports/benchmark.json` (14 claim × 5 seed = 70 trial/shape) và `src/reports/crash.json`:

| Shape | Trial đạt | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 70/70 | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 34.29 | 5.07 / 6 |
| single | 70/70 | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 47.95 | 2.86 / 3 |
| orchestrator | 70/70 | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.44 | 3.71 / 4 |
| swarm | 69/70 | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Crash suite đạt **20/20**. Cần đọc đúng phạm vi: suite 20/20 kiểm host và swarm reference; crash của ba shape nhóm viết được kiểm bổ sung bằng T12 trong ma trận student (crash rồi resume vẫn đúng một refund, một audit `refund_committed`).

Kiểm tra tích hợp của nhóm trưởng: 6 claim đại diện × 3 shape cho cùng status/proposal/refund/audit; 9 test host mới trong `src/tests/test_integration_consistency.py`. Host gate hiện có **72 test**, ma trận student **253 test**, tất cả xanh.

Nhận xét:

- Workflow, single và orchestrator cùng đạt 70/70, nhưng workflow rẻ nhất (34,29 VND) và không gọi model. Single và orchestrator không tăng pass rate mà tăng cost/success lần lượt lên 47,95 và 56,44 VND.
- Swarm thấp hơn ở seed 55: claim `C-002` có ticket ghi trễ 5 ngày nhưng order row chỉ 2 ngày; swarm tin ticket nên trả `resolved` thay vì `denied`. Đây là điểm yếu có chủ đích của shape tham chiếu, nhóm giữ nguyên để làm đối chứng.
- `steps` là số event trong trace, không phải latency hay số phép tính. Single ít event hơn một phần vì trace ghi gộp hơn, nên không kết luận single nhanh hơn chỉ từ cột này.
- Cost là giá mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API. Latency của MockLLM là `unavailable`.

## 5. Khó khăn và cách xử lý

- **Bằng chứng benchmark cũ không khớp code.** `src/reports/benchmark.json` còn số của bản trước khi cập nhật workflow/orchestrator: workflow 28,33 VND và 3,79 steps; orchestrator 47,36 VND và 4,71 steps. Chạy lại trên code hiện tại cho 34,29 VND / 5,07 steps và 56,44 VND / 3,71 steps. Nhóm tạo lại bằng đúng lệnh CLI trong `src/reports/README.md`, không sửa JSON bằng tay.
- **Mô tả trace trong ADR chưa khớp.** ADR cũ ghi single có event từng tool `lookup_order`/`lookup_policy`/`compute_compensation`, nhưng trace thực tế chỉ có `start`, `quote`, `decision`. Nhóm đã sửa mô tả theo trace thật.
- **Orchestrator có nhiều nhánh edge-case.** Unknown claim, thiếu `order_id`, principal không sở hữu đơn, crash/resume và retry cùng số tiền được bổ sung test riêng tại `src/tests/test_orchestrator_edges.py` (commit `c139260`).
- **Môi trường Windows.** Nhóm dùng `src/.venv` với Python 3.13; Python hệ thống 3.14 nằm ngoài khoảng hỗ trợ 3.11–3.13. Mọi lệnh chạy từ thư mục `src/` bằng `.\.venv\Scripts\python.exe`.
- **Trace và dữ liệu nhạy cảm.** Fixture public có `CANARY_SECRET_*` để kiểm leak; trace chỉ ghi field allowlist. Không commit `traces/`, `*.sqlite`, `.env` hay `student_drop/`.

## 6. Tổng hợp đóng góp

| Thành viên | Vai | Commit | Test đã thêm/sửa |
| --- | --- | --- | --- |
| Phạm Hoàng Huy | Nhóm trưởng — tích hợp, kiểm tra, benchmark, hồ sơ | `bad03b1` | `src/tests/test_integration_consistency.py` |
| Lê Thanh Tùng | Shape B `single` + integration | `3ccf5b4`, `75ca166` | `src/tests/test_single_shape.py` |
| Cấn Xuân Nghĩa | Shape A `workflow` (shape được chọn) | `94735f4`, `20865aa` | `src/tests/test_workflow_edges.py` |
| Nguyễn Mạnh Hùng | Shape C `orchestrator` | `4ecff4b`, `c139260` | `src/tests/test_orchestrator_edges.py` |

Chi tiết đóng góp và bằng chứng từng người nằm trong `TEAM.md` và các báo cáo cá nhân `report/team/2A2026038*.md`.

## 7. Hạn chế và hướng cải thiện

- MockLLM là model mô phỏng, không đại diện cho model sản xuất; latency là `unavailable`.
- Kết luận chính chỉ dựa trên 14 claim public × 5 seed. Bộ hidden 40 claim không có trong repo, nên nhóm không kết luận trước pass rate hidden.
- Crash suite 20/20 chủ yếu kiểm host và swarm; bằng chứng crash của từng shape là T12 và các test edge-case, không phải 20 kịch bản riêng cho mỗi shape.
- Chưa làm bonus. Nếu có thời gian, hướng phù hợp là B3 (verifier chống khuếch đại lỗi) hoặc B7 (kiểm toán grader).
- Điều kiện đảo quyết định: nếu hidden của workflow dưới 0,75, hoặc bài toán thực tế cần điều tra song song/giảm latency, nhóm sẽ xem lại orchestrator/swarm. Nếu chỉ tối ưu cost trên corpus hiện tại, workflow đã là lựa chọn tốt nhất.

## 8. Tài liệu tham khảo

- M. Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025: https://arxiv.org/abs/2503.13657
- `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md` của lab.
- `src/reports/benchmark.json`, `src/reports/crash.json` và mã nguồn `src/lab8/shapes/`.

# Báo cáo cá nhân — Phạm Hoàng Huy

## 1. Thông tin

- Họ tên: Phạm Hoàng Huy
- MSSV: 2A202603836
- Nhóm: DaiDi — Lớp L3B
- Vai trò: Nhóm trưởng — tích hợp, kiểm tra chung, benchmark/ablation và tổng hợp hồ sơ
- Repo: https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents
- Nhánh nộp: `main`
- Commit test tích hợp: `bad03b1`
- Commit tổng hợp hồ sơ: xem dòng “commit chốt” trong `TEAM.md` và `report/team/decision_adr.md`

Tôi không trực tiếp viết một shape riêng. Phần việc của tôi là điều phối ba thành viên, chốt ranh giới tích hợp, kiểm tra chéo ba shape, chạy benchmark/ablation, quyết định kiến trúc và hoàn thiện hồ sơ nộp bài.

## 2. Vai trò và cách làm

Nhóm có bốn kiến trúc cần so sánh: workflow, single, orchestrator và swarm reference. Ba thành viên phụ trách ba shape; tôi giữ vai trò người tích hợp và đánh giá:

- Chốt nguyên tắc chung: **tiền do code quyết**, model chỉ đọc dữ liệu và soạn chữ; `durability.issue_refund` là cửa ghi duy nhất.
- Kiểm tra mỗi shape giữ đúng signature `run_claim(...)`, trả `RunResult`, ghi trace đúng contract và chuyển tiếp `crash_at`.
- Chạy lại ma trận public, crash suite và benchmark trên code chốt; không dùng số cũ.
- Tổng hợp báo cáo nhóm, ADR, TEAM, research card và báo cáo cá nhân; kiểm tra lần cuối bằng `check_submission`.

Thứ tự làm: đọc `docs/contracts.md` và `docs/business_rules.md` → review từng shape → chạy kiểm tra chéo → đo benchmark/crash → chốt workflow → hoàn thiện hồ sơ → ghi hash và push.

## 3. Công việc cụ thể

### 3.1. Tích hợp và kiểm tra chung

Tôi đọc cả ba implementation và kiểm tra các điểm dễ lệch:

- `workflow`: quote lấy từ order row, không đọc delay trong ticket; quote 0 thì `denied`, quote dương thì gọi host với quote đầy đủ.
- `single`: `decide()` chỉ chọn tool đọc, không gọi `issue_refund`; sau vòng ReAct code mới gọi host.
- `orchestrator`: handoff chỉ chứa field allowlist; investigator chỉ có tool đọc; orchestrator là nơi duy nhất gọi cổng ghi.

Các kiểm tra nghiệp vụ và an toàn tôi dùng khi review:

- **Approval:** `C-007` (approval hết hạn) và `C-013` (policy cũ) phải `denied`, không ghi ledger.
- **Trần theo đơn:** `C-008` và `C-014` phải trả phần còn lại sau refund trước, không trả vượt.
- **Ticket không đáng tin:** `C-002` ticket ghi trễ 5 ngày nhưng order row chỉ 2 ngày → phải `denied`.
- **Crash/idempotency:** crash trước hoặc sau effect rồi resume vẫn chỉ một refund, một audit `refund_committed`.
- **Rò dữ liệu:** trace không được chứa `CANARY_SECRET_*`, `parent_secret`, raw claim row, SĐT/địa chỉ hay internal note.

Trong quá trình review, tôi phát hiện hai điểm không khớp và đã yêu cầu sửa:

1. `benchmark.json` còn số cũ: workflow 28,33 VND / 3,79 steps và orchestrator 47,36 VND / 4,71 steps, trong khi code hiện tại cho 34,29 / 5,07 và 56,44 / 3,71. Nhóm tạo lại bằng CLI, không sửa JSON tay.
2. ADR cũ mô tả single có event từng tool, nhưng trace thực tế chỉ có `start`, `quote`, `decision` (và các nhánh lỗi). Mô tả đã được sửa theo trace thật.

### 3.2. Test tích hợp bổ sung

Tôi thêm file `src/tests/test_integration_consistency.py` tại commit `bad03b1`, gồm **9 test host**:

- **6 test parity** trên `C-001`, `C-002`, `C-007`, `C-008`, `C-013`, `C-014`: chạy cùng claim qua cả ba shape trên store mới, so sánh status, proposal, danh sách refund và số audit. Kết quả cả ba shape khớp nhau.
- **3 test crash/resume**, mỗi shape một test: crash tại `before_effect`, chạy lại và kiểm tra đúng một refund 35.000 VND, đúng một audit, ledger có đúng một dòng.
- Trong cùng test parity, kiểm tra trace có `run_id`, có `events`, không chứa `CANARY_SECRET_*`, `parent_secret` hoặc `Bearer `.

Các test này chạy ở host gate (không mark `student`) để CI bắt regression tích hợp, không chỉ chạy trong ma trận student.

### 3.3. Benchmark, ablation và quyết định kiến trúc

Tôi chạy benchmark 4 shape trên 14 claim × 5 seed = 70 trial/shape, dùng `MockLLM`, cùng corpus, seed, bảng giá và evaluator:

| Shape | Pass | Pass^5 | Variance | Cost/success (VND) |
| --- | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0.000000 | 34.29 |
| single | 1.000 | 1.000 | 0.000000 | 47.95 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 56.44 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 |

Từ số đo, tôi chốt **workflow** làm shape chấm hidden: cùng 70/70 với single/orchestrator nhưng 0 model call, cost thấp nhất và ít tự chủ nhất. Swarm thấp hơn ở seed 55 vì tin ticket `C-002`; đây là điểm yếu có chủ đích của shape tham chiếu và được giữ làm đối chứng.

Phần ablation/research card được tổng hợp theo R2 (failure taxonomy): lỗi của swarm thuộc **task verification** — không đối chiếu ticket với order row — không phải goal misalignment. Research card ghi rõ giới hạn: đây là ablation quan sát trên lưới seed của cùng implementation swarm, không quy toàn bộ chênh lệch single/swarm cho topology.

### 3.4. Tổng hợp hồ sơ và kiểm tra cuối

Tôi tổng hợp và rà lại:

- `report/team/group_report.md`: mục tiêu, kiến trúc, kết quả, khó khăn, đóng góp, hạn chế.
- `report/team/decision_adr.md`: shape workflow, số liệu, trace, lý do chọn và điều kiện đổi.
- `TEAM.md`: bốn thành viên, bảng đóng góp, commit và test tương ứng.
- Báo cáo cá nhân của Tùng, Nghĩa, Hùng và báo cáo này.
- `research_card.md`: nguồn MAST, claim đúng phạm vi, kết quả ablation và giới hạn.

Sau khi hoàn thiện, tôi chạy `check_submission` và kiểm tra git status sạch, hash trong ADR/TEAM/group report trỏ đúng commit, rồi push lên `main`.

## 4. Bằng chứng kết quả

Các lệnh chạy trong `src/` bằng `.venv` Python 3.13:

| Nội dung | Kết quả |
| --- | --- |
| `pytest -q` (host gate) | **72 passed, 253 deselected** |
| `pytest -q -m student -o addopts=` | **253 passed, 72 deselected** |
| `pytest -q tests/test_integration_consistency.py` | **9 passed** |
| `python -m lab8.crash_test --count 20` | **crash_safety 20/20** |
| `python -m lab8.check_submission` | **0 FAIL, 0 WARN** |
| GitHub Actions | 6/6 job xanh: Ubuntu/Windows/macOS × Python 3.11/3.13 |

Benchmark và crash chính thức nằm trong `src/reports/benchmark.json` và `src/reports/crash.json`; số liệu trên được tạo lại bằng CLI trên code chốt.

## 5. Khó khăn và cách xử lý

- **Số liệu cũ không khớp code:** phát hiện benchmark còn số trước khi cập nhật workflow/orchestrator; tạo lại bằng CLI và đối chiếu từng shape.
- **Mô tả trace sai:** ADR cũ ghi event từng tool cho single; sửa theo trace thực tế `start`, `quote`, `decision`.
- **Ba shape dễ lệch nhau:** thêm test parity trên 6 claim đại diện để bắt lệch status/proposal/refund/audit.
- **Môi trường Windows:** dùng `src/.venv` Python 3.13; Python hệ thống 3.14 ngoài khoảng hỗ trợ.
- **CI không tự chạy sau push:** dùng `gh workflow run lab8-cross-platform` để chạy thủ công và kiểm tra 6 job.
- **Thông tin nhóm chưa đầy đủ:** bổ sung nhóm trưởng vào TEAM, bảng đóng góp và báo cáo cá nhân; không tự khai code shape chưa thực hiện.

## 6. Tự đánh giá

**Điểm mạnh**

- Giữ được ranh giới code/model và cổng ghi duy nhất qua cả ba shape.
- Kiểm tra chéo ba shape bằng test tự động, không chỉ đọc code.
- Chốt kiến trúc dựa trên số đo cost/pass/variance, không dựa cảm tính.
- Hồ sơ có bằng chứng chạy lại được: benchmark, crash, test, check_submission, CI.

**Hạn chế**

- Chưa có hidden 40 claim nên không kết luận trước pass rate hidden.
- MockLLM không đại diện cho model sản xuất; latency là `unavailable`.
- Crash suite 20/20 chủ yếu kiểm host/swarm; crash của từng shape dựa vào T12 và test tích hợp.
- Chưa làm bonus.

**Hướng cải thiện**

- Nếu có hidden hoặc model thật, chạy lại cùng corpus/seed/evaluator để kiểm chứng quyết định workflow.
- Bổ sung verifier hoặc kiểm toán grader nếu muốn lấy điểm bonus.
- Tách test tích hợp thành suite riêng trong CI nếu thời gian chạy host gate tăng.

## 7. Commit và liên kết

- Test tích hợp: `bad03b1` — [src/tests/test_integration_consistency.py](https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents/blob/bad03b1/src/tests/test_integration_consistency.py)
- Commit tổng hợp hồ sơ: xem `TEAM.md` và `decision_adr.md`.
- Báo cáo nhóm: [group_report.md](group_report.md)
- Quyết định kiến trúc: [decision_adr.md](decision_adr.md)

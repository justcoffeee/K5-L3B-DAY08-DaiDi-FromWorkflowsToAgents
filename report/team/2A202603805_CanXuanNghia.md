# Báo cáo cá nhân — 2A202603805_CanXuanNghia

## 1. Thông tin thành viên

- Họ tên: Cấn Xuân Nghĩa.
- MSSV: 2A202603805.
- Email: cannghia.xn@gmail.com.
- GitHub cá nhân: [xuannghia2](https://github.com/xuannghia2).
- Lớp: L3B.
- Bài thực hành: Lab 8 — From Workflows to Agents, LogiX-VN.
- Repo nhóm: https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents

## 2. Phần việc phụ trách

Tôi phụ trách hoàn thiện và kiểm tra **Shape A — Workflow**, tập trung vào file
`src/lab8/shapes/workflow.py`. Phần đóng góp của tôi là bản cập nhật workflow
trong commit `94735f4`, phát triển trên mã nguồn đã có của nhóm. Shape A `workflow`
sau đó được nhóm chọn làm shape chấm hidden (xem `report/team/decision_adr.md`).

Phạm vi công việc gồm xây dựng luồng xử lý claim bằng các bước Python cố định;
đọc dữ liệu đúng quyền của principal; tính mức bồi thường từ dữ liệu đơn hàng và
policy; gọi host để kiểm approval, giới hạn tiền và chống hoàn trùng; trả kết quả
đúng `RunResult`; ghi trace an toàn và hỗ trợ chạy lại sau crash.

Báo cáo này chỉ trình bày phần Workflow. Các shape Single Agent, Orchestrator
và Swarm không thuộc phần triển khai tôi báo cáo ở đây.

## 3. Đóng góp cụ thể

### 3.1. Hoàn thiện luồng xử lý cố định

Giữ nguyên chữ ký hàm theo đề bài:

```python
run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult
```

Các bước xử lý trong workflow:

1. Mở SQLite, lấy claim bằng `get_claim_view`; claim không tồn tại trả `failed`.
2. Nếu thiếu `order_id`, trả `needs_info`, không lấy mã đơn từ nội dung ticket.
3. Gọi `lookup_order` với principal của claim. Đơn không tồn tại hoặc không thuộc
   quyền xem của principal được trả về trạng thái `escalated`.
4. Gọi `compute_compensation` trên dữ liệu đơn hàng có cấu trúc. Tool sử dụng
   policy hiện hành đã có hiệu lực; không dùng số ngày trễ do ticket tự khai.
5. Quote bằng 0 thì trả `denied` và không gọi ghi refund.
6. Quote dương được truyền đầy đủ vào `issue_refund`. Host từ chối thì trả
   `denied`; xung đột số tiền thì trả `failed`; ghi thành công thì trả `resolved`.
7. Dùng `finish` để tạo kết quả từ ledger, audit, budget và trace; đóng kết nối
   trong `finally`.

### 3.2. Quyết định kỹ thuật và ranh giới trách nhiệm

- **Tiền do code tính:** dùng `compute_compensation`, không để model chọn số tiền.
  Khi có cả quyền lợi giao trễ và hỏng hàng, tool lấy mức đủ điều kiện lớn nhất,
  không cộng hai mức hoàn tiền.
- **Truyền quote đầy đủ:** không tự trừ khoản đã hoàn. Host chịu trách nhiệm tính
  phần chênh theo đơn và giới hạn theo approval. `proposal_amount` vẫn giữ quote
  đầy đủ, kể cả khi khoản thực ghi vào ledger thấp hơn.
- **Ghi tiền qua host:** workflow không ghi thẳng vào ledger hoặc tự tạo approval.
  Quote dương phải đi qua `issue_refund` để host có thể ghi audit `policy_denied`
  khi approval không hợp lệ hoặc đơn đã được hoàn đủ.
- **Chống hoàn trùng:** sử dụng cơ chế idempotency sẵn có của host với khóa
  `refund:{claim_id}`, thay vì tự cài một cơ chế ledger khác trong workflow.
- **Crash/resume:** truyền `crash_at` vào `issue_refund`, để `InjectedCrash` truyền
  ra bên gọi. Khối `finally` lưu trace và đóng kết nối cả khi có crash.
- **Trace an toàn:** chỉ ghi dữ kiện cần thiết như trạng thái tìm thấy claim,
  quyền xem đơn, quote và kết quả host. Không ghi ticket, nguyên dòng claim/order,
  secret, header, số điện thoại, địa chỉ hay ghi chú nội bộ. Có sự kiện
  `refund_requested` trước khi gọi host để thể hiện bước đang thực hiện khi crash.
- **Không cần gọi model:** workflow có `model_calls = 0`, phù hợp với luồng cố định
  và yêu cầu chỉ dùng model để soạn câu chữ nếu cần.

### 3.3. Kiểm thử bổ sung tại máy làm bài

Với sự hỗ trợ của Codex, bổ sung file `src/tests/test_workflow_edges.py` để
kiểm tra các tình huống ngoài ma trận public:

- `test_unknown_claim_returns_failed_with_fresh_trace`: claim không tồn tại vẫn
  trả kết quả `failed` và có trace đúng run ID.
- `test_workflow_crash_and_repeated_resume`: kiểm tra cả ba điểm crash
  `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`; chạy lại
  nhiều lần vẫn chỉ có một refund và một audit committed.
- `test_changed_quote_on_retry_preserves_committed_amount`: quote thay đổi khi
  retry phải báo `amount_conflict`, giữ nguyên khoản đã commit.

File test bổ sung đã được đưa lên main tại commit `20865aa`.
Commit `94735f4` đưa lên GitHub phần thay đổi `workflow.py`; commit `20865aa`
đưa lên phần test edge-case.

## 4. Bằng chứng

### 4.1. Commit và file triển khai

- Commit: [`94735f46ad948085e7ff66f871312621edf3bcf3`](https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents/commit/94735f46ad948085e7ff66f871312621edf3bcf3).
- Nội dung commit: `Complete deterministic workflow with safe refund handling`.
- File tại commit: [src/lab8/shapes/workflow.py](https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents/blob/94735f46ad948085e7ff66f871312621edf3bcf3/src/lab8/shapes/workflow.py).

### 4.2. Kết quả đã chạy

Các lệnh được chạy trong thư mục `src` của bản làm bài trên ổ D, bằng môi trường
`.venv`. Số liệu dưới đây lấy từ kết quả chạy và báo cáo sinh tự động.

| Nội dung kiểm tra | Kết quả | Phạm vi |
| --- | --- | --- |
| Starter smoke | `lab8.smoke pass` | Kiểm tra môi trường và swarm tham chiếu |
| Ma trận public workflow | `62 passed` | Workflow T01–T14, gồm retry và crash/resume |
| Bộ host hiện tại | `72 passed, 253 deselected` | Cổng host cùng 18 test bổ sung của nhóm (4 single, 5 workflow, 9 tích hợp) |
| Benchmark workflow | 70/70 lượt đạt | 14 claim × 5 seed: 11, 22, 33, 44, 55 |
| Crash suite có sẵn | `crash_safety 20/20` | Kiểm host và swarm; không phải 20 kịch bản riêng của workflow |

Số `59 passed` và `116 passed` trong bản trước là lần chạy trước khi bổ sung đủ test; không dùng làm số hiện tại.

Benchmark chính thức của nhóm nằm tại `src/reports/benchmark.json` (4 shape); số của workflow:

| Chỉ số | Giá trị |
| --- | ---: |
| Pass rate | 1.000 |
| Pass^5 | 1.000 |
| Seed variance | 0.000000 |
| Cost/success | 34,29 VND mô phỏng |
| Số bước trung bình theo trace | 5,07 |
| Số lần gọi model trung bình | 0 |

Chi phí trên là chi phí mô phỏng của lab, không phải hóa đơn API.
Báo cáo crash suite được lưu tại `src/reports/crash.json`.

### 4.3. Ví dụ một lần chạy

Lệnh chạy:

```powershell
.\.venv\Scripts\python.exe -m lab8.run --shape workflow --claim-id C-001 --seed 11 --db data/workflow.sqlite
```

Kết quả quan sát:

```json
{
  "run_id": "R-workflow-C-001-s11",
  "status": "resolved",
  "proposal_amount": 35000,
  "committed_audit_count": 1,
  "model_calls": 0,
  "tool_calls": 4,
  "error_reason": null
}
```

Ledger có một refund đã commit với `amount_vnd = 35000` và khóa
`refund:C-001`. Trace được ghi tại `traces/R-workflow-C-001-s11.json`.

Lệnh tái kiểm tra phần workflow:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= -k workflow
.\.venv\Scripts\python.exe -m lab8.benchmark --shapes workflow --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark_workflow.json
```

## 5. Công cụ AI đã dùng

Tôi sử dụng **OpenAI Codex** để hỗ trợ đọc README và contract, giải thích luồng
xử lý, viết và rà soát code workflow, bổ sung test, đọc kết quả chạy, chuẩn bị
commit và soạn bản báo cáo này từ các bằng chứng đã có.

Code và test được Codex hỗ trợ tạo, không phải toàn bộ được tôi tự viết thủ công.
Tôi trực tiếp chạy các lệnh kiểm tra trong terminal VS Code trên ổ D và đối chiếu
kết quả: 62 test workflow đạt, claim C-001 trả `resolved` với 35.000 đồng,
benchmark pass/pass^5 bằng 1.000, crash suite 20/20 và bộ host 72 test đạt.

Số liệu, run ID và commit trong báo cáo được lấy từ lần chạy thực tế và lịch sử
Git; không tự tạo kết quả hidden hoặc sửa tay báo cáo JSON để thay đổi điểm.

## 6. Tự đánh giá

Phần workflow phụ trách đã hoàn thành luồng xử lý cố định và vượt qua bộ kiểm tra
public đã chạy. Các điểm được kiểm chứng gồm tính quote từ dữ liệu có cấu trúc,
đi qua cổng host, giữ quote đầy đủ, trả đúng trạng thái và hỗ trợ retry/crash.
Workflow không cần model call cho nghiệp vụ này và kết quả public không dao động
qua năm seed đã kiểm tra.

Giới hạn hiện tại: kết quả 100% chỉ áp dụng cho bộ public. Chưa có dữ liệu hidden
để kết luận đạt ngưỡng hidden của đề bài. Crash suite 20/20 là bằng chứng của host
và swarm; bằng chứng riêng cho workflow nằm ở T12 và `test_workflow_edges.py`.

Đóng góp Workflow đã được đồng bộ vào `TEAM.md`; test edge-case đã có trên main
tại commit `20865aa`.
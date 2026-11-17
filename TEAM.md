# Team

## Thông tin nhóm

- Tên nhóm: DaiDi
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents`
- URL repo, nhánh nộp, commit chốt: https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents, main, `bad03b1`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Phạm Hoàng Huy | 2A202603836 | — | justcoffeee | Nhóm trưởng — tích hợp, kiểm tra, benchmark, hồ sơ |
|   2 | Lê Thanh Tùng | 2A202603819 | lethanhtung6803@gmail.com | griin-03 | single agent (Shape B) + integration |
|   3 | Cấn Xuân Nghĩa | 2A202603805 | cannghia.xn@gmail.com | xuannghia2 | workflow (Shape A, shape được chọn) |
|   4 | Nguyễn Mạnh Hùng | 2A202603852 | nguyenmanhhunglun@gmail.com | HungLunnn | orchestrator (Shape C) |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Hoàng Huy | Nhóm trưởng — tích hợp, kiểm tra, benchmark, hồ sơ | bad03b1 | src/tests/test_integration_consistency.py |
| Lê Thanh Tùng | single agent (Shape B) | 3ccf5b4, 75ca166 | src/tests/test_single_shape.py |
| Cấn Xuân Nghĩa | workflow (Shape A, shape được chọn) | 94735f4, 20865aa | src/tests/test_workflow_edges.py |
| Nguyễn Mạnh Hùng | orchestrator (Shape C) | 4ecff4b, c139260 | src/tests/test_orchestrator_edges.py |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603819_LeThanhTung

### Phần việc phụ trách

- Shape B `single` — ReAct single agent
- Tác giả bộ unit test chuyên biệt `src/tests/test_single_shape.py` cho single agent
- Benchmark runner & kết nối crash test cho Shape B

### Đóng góp cụ thể

- Triển khai trọn vẹn `src/lab8/shapes/single.py`: Vòng ReAct bounded `max_steps=8`, `decide()` đóng vai trò agent controller tuần tự điều hướng qua allowlist read-only tools: `lookup_order` -> `lookup_policy` -> `compute_compensation`. 
- Cố định ranh giới bảo mật code/model: Model chỉ đọc và tổng hợp quote, tuyệt đối không gọi tool ghi và không tự quyết số tiền. Cổng ghi duy nhất do host `durability.issue_refund` đảm nhiệm.
- Kháng tấn công Adversarial injection: Không tin văn bản ticket của khách (C-002 claim 5 ngày nhưng DB là 2 ngày, C-009 'ignore policy'), hoàn toàn quote dựa trên DB order row có kiểm tra quyền principal.
- Hỗ trợ crash fault-injection: Chuyển tiếp nguyên vẹn `crash_at` tới `durability.issue_refund`, không nuốt ngoại lệ `InjectedCrash`.
- Xây dựng file test `src/tests/test_single_shape.py`: 4 unit tests bao phủ unknown claim, adversarial prompt injection, trace contract v1 & canary leak check, crash forwarding.
- Kết quả test: Pass 62/62 matrix trials trên Shape B, pass 4/4 tests trong `test_single_shape.py`.

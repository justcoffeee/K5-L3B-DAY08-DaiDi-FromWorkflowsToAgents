# Team

## Thông tin nhóm

- Tên nhóm: Lê Thanh Tùng (Individual - L3B)
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents`
- URL repo, nhánh nộp, commit chốt: https://github.com/justcoffeee/K5-L3B-DAY08-DaiDi-FromWorkflowsToAgents, main

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Lê Thanh Tùng | 2A202603819 | lethanhtung6803@gmail.com | griin-03 | single agent (Shape B) + workflow (Shape A) + orchestrator (Shape C) |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Lê Thanh Tùng | Shape B single + A workflow + C orchestrator | feat(shapes): implement workflow, single, orchestrator — 248/248 student tests pass | test_public_matrix.py::test_public_single_run_cases[*-single], test_t11_retry_keeps_one_refund[single], test_t12_crash_before_checkpoint_does_not_double_pay[single] |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603819_LeThanhTung

### Phần việc phụ trách

- Shape B `single` — ReAct single agent (file chính)
- Shape A `workflow` — deterministic workflow
- Shape C `orchestrator` — orchestrator + investigator

### Đóng góp cụ thể

- Implement `src/lab8/shapes/single.py`: ReAct loop 8 bước, chỉ dùng read tools, host gọi `durability.issue_refund`
- Implement `src/lab8/shapes/workflow.py`: pipeline Python cố định, adversarial-safe (không tin ticket text)
- Implement `src/lab8/shapes/orchestrator.py`: handoff sanitized → investigator → orchestrator gọi issue_refund
- Chạy benchmark: single pass rate 1.000, variance 0.000, crash safety 20/20

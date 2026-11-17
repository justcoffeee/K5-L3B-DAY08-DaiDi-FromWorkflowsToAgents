# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: c139260
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 34.29
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: Không lộ secret. Trace chỉ ghi field từ allowlist. Approval do host kiểm, shape không bypass.

## Vì sao shape này

Shape A (`workflow`) đạt pass rate 1.000, pass^5 1.000, variance 0.000 trên 14 claim × 5 seed, với 0 model call và cost/success 34.29 VND (mô phỏng) — thấp nhất trong ba shape cùng đạt 70/70. Các bước là Python cố định: đọc claim qua `get_claim_view`, lấy order theo principal, tính quote bằng `compute_compensation`, rồi gọi `durability.issue_refund` với quote đầy đủ. Số tiền, approval, trần theo đơn và idempotency đều do host code quyết, nên đây là kiến trúc **ít tự chủ nhất mà vẫn làm đúng toàn bộ public matrix**.

Single cũng đạt 70/70 nhưng cần khoảng 5.36 model call/trial và cost 47.95 VND; orchestrator đạt 70/70 với cost 56.44 VND. Hai shape này không tăng pass rate mà tăng chi phí và thêm bề mặt quyết định của model. Vì vậy nhóm chọn workflow cho cổng hidden.

## Có đáng đổi lấy multi-agent không

Chưa đáng trên corpus hiện tại. Swarm (Shape D) có pass rate 0.986, pass^5 0.929, variance 0.000816: tại seed 55, claim C-002 có ticket ghi trễ 5 ngày trong khi order row chỉ 2 ngày, swarm tin ticket nên trả `resolved` thay vì `denied`. Đây là lỗi kiểm chứng dữ liệu có chủ đích của shape tham chiếu. Orchestrator và single cũng không vượt được 1.000 của workflow. Nhóm chỉ xem xét đổi sang multi-agent nếu task có nhiều bước điều tra độc lập, cần song song hoặc ưu tiên latency hơn cost/consistency — khi đó phải đo lại trên cùng corpus, seed và evaluator.

## Trace và bằng chứng

Trace của workflow ghi các event `get_claim_view` (found), `lookup_order` (visible, reason), `quote` (amount), `refund_requested`, `issue_refund` (ok, reason), `decision` (status, proposal, reason). **Không ghi**: ticket text, raw claim row (có `parent_secret`), raw order row (có SĐT, địa chỉ, internal note), header hay toàn bộ handoff. Single chỉ ghi `start`, `quote`, `decision` và các nhánh lỗi; orchestrator ghi `claim_view`, `handoff`, `investigator`, `quote`. Mọi field đều đi qua allowlist của `get_claim_view`, `lookup_order` hoặc `handoff`. Scanner quét `trace_path` và mọi file `<run_id>*` cùng thư mục — không có file nào ngoài phạm vi đó.

## Giới hạn

MockLLM không phải model sản xuất; latency để `unavailable`. Kết luận chỉ dựa trên 14 claim public × 5 seed; chưa có nhãn hidden nên không kết luận trước pass rate hidden. Cost là giá mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API. `steps` là số event trong trace, không phải latency. Crash suite 20/20 kiểm host và swarm; crash của shape được kiểm bổ sung bằng T12.

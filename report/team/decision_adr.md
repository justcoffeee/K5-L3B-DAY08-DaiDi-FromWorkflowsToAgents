# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: single
- Commit hash: 3ccf5b4
- Run id dẫn chứng: R-single-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 47.95
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: Không lộ secret. Trace chỉ ghi field từ allowlist. Approval do host kiểm, shape không bypass.

## Vì sao shape này

Shape B (`single`) đạt pass rate 1.000, pass^5 1.000, variance 0.000, cost/success 47.95 VND (mô phỏng) — tốt hơn swarm (0.986 / 0.929 / variance 0.000816). Vòng ReAct với `max_steps=8` đủ để tra cứu order và policy, tính quote và quyết định hoàn tiền. Model chỉ chọn tool đọc, không ghi trực tiếp vào ledger. Số tiền, approval, idempotency và cap theo đơn hoàn toàn do host code quyết — đây là mức tự chủ thấp nhất mà vẫn hoàn thành đúng task trên toàn bộ 14 claim × 5 seed.

## Có đáng đổi lấy multi-agent không

Swarm (Shape D) có pass rate thấp hơn (0.986) và variance cao hơn (0.000816) do điểm yếu seed % 5 == 0 tin delay từ ticket thay vì DB. Cost/success của swarm (49.57) cũng cao hơn single (47.95). Nếu task claims đòi hỏi điều tra song song hoặc cross-check từ nhiều nguồn thì mới xem xét đổi sang swarm/orchestrator. Với corpus hiện tại, single đủ dùng và ổn định hơn. Điều kiện đảo quyết định: task có nhiều bước điều tra độc lập mà latency quan trọng hơn cost và consistency.

## Trace và bằng chứng

Trace ghi các event: `start` (claim_id, order_id), kết quả từ mỗi bước ReAct (`lookup_order`, `lookup_policy`, `compute_compensation`), `quote` (amount_vnd, reason), `decision` (status cuối cùng). **Không ghi**: raw claim row (có `parent_secret`), raw order row (có SĐT, địa chỉ, internal note), ticket text. Chỉ ghi field qua allowlist của `get_claim_view` và `lookup_order`. Scanner quét `trace_path` và mọi file `<run_id>*` cùng thư mục — không có file nào ngoài phạm vi đó.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.

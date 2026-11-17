# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?*, https://arxiv.org/abs/2503.13657 — benchmark + human annotation: 1.600+ trace, 7 framework, κ = 0,88 |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Hệ multi-agent LLM có 14 failure mode thuộc 3 nhóm: system design, inter-agent misalignment và task verification; taxonomy được xây từ 150 trace có human annotation, κ = 0,88. Nguồn không khẳng định nhóm nào là phổ biến nhất. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Áp dụng cho LLM-based multi-agent trên 7 framework được khảo sát; không mặc định đúng cho MockLLM hay agent deterministic trong lab. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Swarm sẽ fail C-002 ở seed 55 vì tin số ngày trong ticket thay vì order row; lỗi thuộc nhóm **task verification** (không đối chiếu dữ liệu có cấu trúc), không phải goal misalignment. Workflow và single không fail claim này; pass rate của swarm thấp hơn và variance lớn hơn. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định MockLLM, tool set, corpus 14 claim, giá `config/pricing.yaml`, evaluator. Ablation quan sát trên cùng implementation swarm: so seed 55 (chia hết cho 5, kích hoạt điểm yếu ticket) với seed 11/22/33/44; workflow và single là đối chứng. Không quy toàn bộ chênh lệch single/swarm cho topology vì hai implementation còn khác cách đọc ticket và số model call. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Swarm fail C-002 seed 55: pass 0.986, pass^5 0.929, variance 0.000816; workflow/single 1.000, variance 0.000000. Đo pass rate, pass^5, variance, cost/success; leak và approval bypass bằng 0. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn):
  ```
  python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
  ```
- Run id / file report: `R-workflow-C-001-s11`; số liệu trong `src/reports/benchmark.json`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:
  - **Đúng một phần**: Swarm pass rate = 0.986, pass^5 = 0.929, variance = 0.000816; workflow và single đều 1.000, variance = 0.000000. Swarm chỉ fail `C-002` ở seed 55: ticket ghi trễ 5 ngày trong khi order row ghi 2 ngày, swarm trả `resolved` với 20.000 VND thay vì `denied`.
  - Phân loại lỗi: đây là **task verification** — agent không đối chiếu dữ kiện trong ticket với order row có cấu trúc — không phải goal misalignment. Workflow và single không mắc lỗi này vì quote lấy từ `compute_compensation` trên order row.
  - **Không kết luận được** rằng topology là nguyên nhân duy nhất của chênh lệch single vs swarm: hai implementation còn khác cách đọc ticket và số lần gọi model. Đây là ablation quan sát trên lưới seed của cùng một implementation swarm, không phải can thiệp chỉ đổi topology.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`; corpus chỉ có 14 claim public và chưa có nhãn hidden.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).

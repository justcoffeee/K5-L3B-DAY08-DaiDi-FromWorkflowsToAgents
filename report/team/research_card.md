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
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?*, benchmark trên nhiều multi-agent framework |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi phổ biến nhất trong hệ multi-agent là lệch mục tiêu (goal misalignment) giữa sub-agent và orchestrator, không phải lỗi tool |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Áp dụng cho LLM-based multi-agent, không nhất thiết áp dụng cho mock/deterministic agent như MockLLM |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Swarm (D) sẽ có pass rate thấp hơn single (B) do điểm yếu tin ticket delay thay vì DB order row — variance của swarm sẽ > 0 khi thay seed |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, tool set, corpus 14 claims, seeds [11,22,33,44,55], giá config/pricing.yaml. Biến thay đổi: topology (single vs swarm) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Swarm fail C-002 seed 55 do goal misalignment (trust ticket over DB). Đo bằng pass rate và variance: swarm variance = 0.000816 > single variance = 0.000000 |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn):
  ```
  python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
  ```
- Run id / file report: `src/reports/benchmark.json`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:
  - **Đúng**: Swarm pass rate = 0.986 < single = 1.000; swarm variance = 0.000816 > single = 0.000000. Swarm fail C-002 seed 55 đúng như dự đoán (trust delay 5 days từ ticket, DB nói 2 days → trả 20000 thay vì denied).
  - Single không có lỗi goal misalignment vì `decide()` không đọc ticket text, chỉ dùng DB order row để tính compensation.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).

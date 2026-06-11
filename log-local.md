# Log Local — Setup & Implementation (Lab 11)

Ghi lại toàn bộ các phần đã thêm/sửa khi setup và chạy lab ở môi trường local (Windows).

---

## 1. Môi trường

| Hạng mục | Giá trị |
|----------|---------|
| OS | Windows 10 |
| Python venv | 3.13 (đặt tại `.venv/`) — tránh 3.14 vì `nemoguardrails` chưa hỗ trợ tốt |
| Trình cài đặt | `uv` (đặt `UV_HTTP_TIMEOUT=300` do mạng PyPI chậm) |
| LLM | `gpt-4o-mini` (OpenAI) — gọi qua **LiteLLM** trong Google ADK |

> **Cập nhật:** Đã chuyển provider từ Google Gemini → **OpenAI** (xem mục 6).

### Tạo venv & cài dependency
```powershell
uv venv --python 3.13 .venv
$env:UV_HTTP_TIMEOUT = "300"
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

### Biến môi trường (lưu vĩnh viễn ở User level)
```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "<your-openai-key>", "User")
```

---

## 2. Thay đổi cấu hình / dependency

### `requirements.txt` — thêm 3 package cho NeMo
NeMo Guardrails >= 0.22 đổi framework mặc định; để chạy Gemini cần thêm:
```
langchain>=1.0.0
langchain-community>=0.4.0
langchain-google-genai>=4.0.0
```

### `src/guardrails/nemo_guardrails.py` — sửa cấu hình NeMo
- **Engine**: `google` → `google_genai`.
- **Bỏ section `rails:`** trong YAML (NeMo 0.22 validate chặt, các flow `check user message`/`check bot response` không tồn tại trong Colang ⇒ các dialog flow trong Colang tự xử lý chặn).
- Set `NEMOGUARDRAILS_LLM_FRAMEWORK=langchain` ngay trong module.
- **Ghim cache embeddings** vào `~/.cache/fastembed` (mặc định nằm trong `%TEMP%` — Windows tự dọn, gây thiếu `tokenizer_config.json` và lỗi "internal error" mọi request):
  ```python
  os.environ.setdefault("FASTEMBED_CACHE_PATH", str(Path.home() / ".cache" / "fastembed"))
  ```

### Sửa lỗi console Windows in tiếng Việt (`charmap` codec)
Thêm vào đầu `src/main.py` và block `__main__` của `nemo_guardrails.py`:
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
```

---

## 3. Implementation — 13 TODO

| TODO | File | Nội dung thêm vào | Verify |
|------|------|-------------------|--------|
| 1 | `attacks/attacks.py` | 5 adversarial prompt: completion, reformat-to-JSON, creative writing, confirmation/side-channel, multi-step escalation | ✅ agent unsafe bị leak |
| 2 | `attacks/attacks.py` | AI red-teaming `generate_ai_attacks()` (có sẵn) | ✅ |
| 3 | `guardrails/input_guardrails.py` | `detect_injection()` — 13 regex (EN + tiếng Việt): override, role hijack, secret extraction | ✅ PASS |
| 4 | `guardrails/input_guardrails.py` | `topic_filter()` — chặn `BLOCKED_TOPICS`, off-topic nếu không khớp `ALLOWED_TOPICS` | ✅ PASS |
| 5 | `guardrails/input_guardrails.py` | `InputGuardrailPlugin.on_user_message_callback()` — 2 lớp: injection + topic | ✅ chặn đúng |
| 6 | `guardrails/output_guardrails.py` | `content_filter()` — redact API key, password, `*.internal`, email, SĐT VN, CMND/CCCD | ✅ redact đúng |
| 7 | `guardrails/output_guardrails.py` | `safety_judge_agent` (LLM-as-Judge) bằng `LlmAgent` | ✅ |
| 8 | `guardrails/output_guardrails.py` | `OutputGuardrailPlugin.after_model_callback()` — content filter + judge | ✅ Part 3 chặn 5/5 |
| 9 | `guardrails/nemo_guardrails.py` | 3 Colang rule mới: role confusion, encoding attack, Vietnamese injection (+ test cases) | ✅ chạy đúng |
| 10 | `testing/testing.py` | `run_comparison()` — dựng protected agent + đánh dấu `blocked` theo leak | ✅ 1/5 → 5/5 |
| 11 | `testing/testing.py` | `SecurityTestPipeline.run_all()` + `calculate_metrics()` | ✅ report in ra |
| 12 | `hitl/hitl.py` | `ConfidenceRouter.route()` — high-risk luôn escalate, còn lại theo ngưỡng 0.9/0.7 | ✅ routing đúng |
| 13 | `hitl/hitl.py` | 3 HITL decision point: high-value transfer, low-confidence answer, security anomaly | ✅ |

---

## 4. Kết quả verify

### Part 3 — Before/After (chứng minh defense-in-depth)
```
Unprotected: 1/5 blocked   →   Protected: 5/5 blocked   (+4 attacks blocked)
```

### Offline tests (không tốn quota)
- `detect_injection()`, `topic_filter()`, `content_filter()`, `ConfidenceRouter` — tất cả PASS.

---

## 5. Lưu ý vận hành

- **Quota Gemini free tier = 20 request/ngày/model.** Các phần gọi LLM (Part 1, NeMo Part 2C, comparison, judge) báo `429 RESOURCE_EXHAUSTED` khi hết quota → **là giới hạn quota, không phải lỗi code**. Chờ reset theo ngày hoặc nâng cấp billing.
- Phần offline (regex filter, HITL router — Part 4) chạy được mọi lúc.

### Cách chạy
```powershell
cd src
..\.venv\Scripts\python.exe main.py            # toàn bộ lab
..\.venv\Scripts\python.exe main.py --part 1   # từng part 1-4
```

---

## 6. Chuyển provider: Google Gemini → OpenAI

Lab vẫn dùng framework **Google ADK**, nhưng model gọi qua **LiteLLM** nên chạy được OpenAI.

### Dependency thêm
```
openai>=1.0.0
litellm>=1.0.0
langchain-openai>=0.2.0   # thay cho langchain-google-genai
```
> Lưu ý: cần `pip install google-adk[extensions]` (hoặc cài `litellm`) để ADK có lớp `LiteLlm`.

### Các file đã sửa
| File | Thay đổi |
|------|----------|
| `core/config.py` | `setup_api_key()` đọc `OPENAI_API_KEY`; thêm hằng `OPENAI_MODEL="gpt-4o-mini"` và `LITELLM_MODEL="openai/gpt-4o-mini"` |
| `agents/agent.py` | `model=LiteLlm(model=LITELLM_MODEL)` cho cả unsafe & protected agent |
| `guardrails/output_guardrails.py` | `safety_judge_agent` dùng `LiteLlm(...)` |
| `attacks/attacks.py` | `genai.Client()` → `OpenAI()`; `chat.completions.create(...)`; đọc `response.choices[0].message.content` |
| `guardrails/nemo_guardrails.py` | NeMo engine `openai`, model `gpt-4o-mini` (vẫn dùng framework `langchain` + `langchain-openai`) |
| `requirements.txt` | thêm `openai`, `litellm`, `langchain-openai`; bỏ `langchain-google-genai`, `google-genai` (vẫn được `google-adk` kéo theo) |

### Notebook `lab11_guardrails_hitl.ipynb` — cũng đã chuyển sang OpenAI
| Cell | Thay đổi |
|------|----------|
| Install (3) | `google-adk google-genai nemoguardrails openai litellm` (bỏ `langchain-google-genai`) |
| Imports (4) | thêm `LiteLlm`, `from openai import OpenAI`; bỏ `from google import genai` |
| Config (5) | đọc `OPENAI_API_KEY`; thêm `OPENAI_MODEL`/`LITELLM_MODEL`; ghim `FASTEMBED_CACHE_PATH` |
| Agents (8, 26, 35) | `model=LiteLlm(model=LITELLM_MODEL)` |
| TODO 2 (14) | `OpenAI().chat.completions.create(...)` |
| NeMo (30, 31) | engine `openai`, model `gpt-4o-mini` |

> NeMo trong notebook dùng **engine `openai` natively** (không cần langchain framework như bản `src/`).

### Verify (offline — không cần key)
`detect_injection`, `topic_filter`, `content_filter`, `ConfidenceRouter`, compile toàn bộ module — tất cả PASS.
Notebook: JSON hợp lệ (47 cells), ADK + `LiteLlm(openai)` tạo agent OK.

### Còn lại
Các phần gọi LLM (Part 1 attacks, NeMo Part 2C, comparison, judge) cần đặt `OPENAI_API_KEY` thật rồi chạy để verify end-to-end.

---

## 7. Assignment 11 — Defense Pipeline (Part A + Part B)

### Part A — thêm "Part 5: Production Defense Pipeline" vào `lab11_guardrails_hitl_openai.ipynb`
Bổ sung 10 cell (57 cells tổng) cài đủ 6 layer mà lab thiếu, tái dùng `detect_injection`/`topic_filter`/`content_filter`:
| Layer | Class/Hàm |
|-------|-----------|
| L0 Rate Limiter | `RateLimiter` (sliding window per-user) |
| L1/L2 Input | reuse `detect_injection` + `topic_filter` + input-validation (empty/oversize) |
| L3 Output | reuse `content_filter` (redact PII/secret) |
| L4 LLM-Judge đa tiêu chí | `multi_criteria_judge` (safety/relevance/accuracy/tone + PASS/FAIL) |
| L5 Audit | `AuditLog.export_json("security_audit.json")` |
| L6 Monitoring | `MonitoringAlert.check_metrics` (block-rate/judge-fail alerts) |

Orchestrator: `DefensePipeline.process()`. Có đủ 4 test suite: safe / attacks / rate-limit (15 req) / edge-cases.

**Verify offline (stub LLM, không cần key):** Test1 5/5 answered · Test2 7/7 blocked, 0 leak · Test3 10 pass + 5 blocked · Test4 empty/long→validation, emoji/SQL/math→topic · Monitoring 32 records + alert + export OK.

### Part B — report
File `report_assignment11.md` (tiếng Anh), trả lời 5 câu, bám sát logic guardrail thực tế (đã verify bằng cách chạy `detect_injection`/`topic_filter` trên Test 1 & 2).

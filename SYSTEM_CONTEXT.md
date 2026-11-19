# SBL Assistant: System Context

Everything needed to build the whole system from scratch. Give this file to your AI agent together with your GitHub issue (https://github.com/hanz-geric/sbl-assistant/issues). If this file and an issue disagree, the issue wins; ask in the issue.

---

## 1. What we are building

The **Small Business and Livelihood Development Knowledge Assistant** (University of Baguio group project, adviser: Benny Cris Pio). A chatbot that answers small business and livelihood questions for **Baguio City and Benguet**: DTI business name registration, Baguio City business permits (Mayor's Permit, eBPLS), BIR, livelihood and loan programs (DOLE DILP, SB Corp, DSWD, TESDA, Negosyo Centers).

It is a **RAG** system (Retrieval-Augmented Generation):
1. find the passages in our knowledge base that match the question,
2. let a small local model answer **only** from those passages,
3. show the passages as **sources** under the answer.

### Ground rules of the product
- Users may ask in English, Filipino, Taglish or Ilocano. **Answers are always in English.**
- **Sources come from the retriever, never from the model's text.**
- The model must not invent numbers (fees, rates, ages, dates), offices or approvals.
- Off-topic questions (weather, tourist spots, food, jokes) get one fixed sentence.
- Everything runs **locally on one laptop, CPU only**. No paid APIs, no cloud models.

---

## 2. Architecture

```
Browser  web/views/index.php
   │  fetch (FormData) ─ streams NDJSON back
   ▼
PHP      web/controller/chatbot_action.php ─► web/model/chatbot.php ─► MySQL sbl_chatbot_db.messages
   │  cURL, JSON body {"question": ...}
   ▼
Python   rag-service/api.py (Flask, 127.0.0.1:5000)
   │  retrieval.py: Chroma meaning search (bge-m3) + BM25 keyword search, fused
   │  generator.py: prompt + gemma3:4b, streamed
   ▼
Ollama   localhost:11434   gemma3:4b (chat), bge-m3 (embeddings)
```

Request flow for one question:
1. Browser POSTs the question to `chatbot_action.php?action=stream`.
2. PHP saves the user message, then POSTs `{"question"}` to Flask `/ask/stream`.
3. Flask: embed question with bge-m3 → rank all 143 chunks by meaning + BM25 → pick 3–5 chunks. If the closest chunk's distance > 1.0 → fixed off-topic reply, no model call.
4. Otherwise Flask builds the prompt (rules + cleaned chunks) and streams gemma3:4b's answer as NDJSON lines, then a `done` line with the sources.
5. PHP passes each line to the browser immediately and collects them; when `done` arrives it saves the bot message (answer + sources JSON + time).
6. Browser appends text into the bot bubble as it arrives, then reloads the chat from the DB (adds sources and time).

---

## 3. Environment

| Item | Value |
|---|---|
| OS | Windows (team laptops) |
| Python | 3.11, venv in `rag-service/.venv` |
| Python packages | `ollama==0.6.3`, `chromadb==1.5.9`, `flask==3.1.3` (`httpx` comes with `ollama`) |
| Ollama | `localhost:11434`; models `gemma3:4b` (chat, ~3.4 GB) and `bge-m3` (embeddings, 1024 dims, normalized, ~1.2 GB) |
| Web | XAMPP: Apache + PHP + MySQL/MariaDB |
| Database | MySQL `sbl_chatbot_db`, user `root`, empty password (local dev) |
| Site URL | http://localhost/sbl-chatbot/views/ |
| Flask URL | http://127.0.0.1:5000 (never exposed to other computers) |

Hardware reality: CPU only. gemma3:4b gives first words after ~8–14 s and a full answer in ~13–30 s; the first question after starting is slower (model loading). 8b models are borderline (20–30 s+); 12b is too slow. **Stay on gemma3:4b.**

### Setup (per member)
```
ollama pull gemma3:4b
ollama pull bge-m3
```
- Clone the repo **outside** `htdocs` (e.g. `Documents\sbl-assistant`). Inside `htdocs`, Apache would serve the Python code and data publicly.
- Python: `cd rag-service`, `python -m venv .venv`, `.venv\Scripts\activate`, `pip install -r requirements.txt`, `python build_index.py`.
- Web: link the folder into XAMPP (cmd as administrator):
  `mklink /J "C:\xampp\htdocs\sbl-chatbot" "C:\Users\<you>\Documents\sbl-assistant\web"`
- MySQL: run the SQL in section 9 once in phpMyAdmin.

### Running the whole app
1. Ollama running.
2. XAMPP: Apache + MySQL started.
3. `cd rag-service`, activate venv, `python api.py`.
4. Open http://localhost/sbl-chatbot/views/

---

## 4. Repository layout (final)

```
sbl-assistant/
├─ rag-service/
│  ├─ .gitignore           .venv/  __pycache__/  chroma_db/
│  ├─ requirements.txt
│  ├─ data/chunks.json     given, 143 passages
│  ├─ build_index.py       chunks → bge-m3 → Chroma (chroma_db/)
│  ├─ retrieval.py         tokenize, KeywordIndex (BM25), Retriever (hybrid search)
│  ├─ search.py            debug printout of rankings
│  ├─ generator.py         rules, context cleaning, prompt, streamed answer
│  ├─ ask.py               terminal Q&A
│  └─ api.py               Flask: POST /ask, POST /ask/stream
└─ web/
   ├─ config/dbconn.php
   ├─ model/chatbot.php    class Chatbot
   ├─ controller/chatbot_action.php
   └─ views/index.php      page + CSS + JS
```
Never commit `.venv/`, `__pycache__/`, `chroma_db/`.

---

## 5. Coding conventions (strict)

### General
- Touch only the files your task names. Build exactly what is specified: no extra features, helpers, abstractions, config files, logging, retries, or error handling for cases not listed.
- Exact names, constants, strings, prompts, printed output and JSON keys as given here.
- No new dependencies. No test framework, linters config, Docker, or README unless asked.
- Unclear? Ask in the issue. Do not invent a different design.

### Python
- 4 spaces, **double quotes**, f-strings. No type hints, no `typing`, `dataclass`, `argparse`, `logging`.
- Imports in three groups (stdlib / third-party / ours), blank line between.
- `BASE = Path(__file__).parent`; open files with `encoding="utf-8"`.
- Settings as UPPER_CASE module constants at the top.
- Plain `snake_case` functions. Only two classes: `KeywordIndex`, `Retriever`, each with a one-line docstring; no other docstrings.
- Scripts run at top level; only `api.py` has `if __name__ == "__main__":`.
- Counting: `d[k] = d.get(k, 0) + 1`.

### PHP
- **Tabs**. Files start with `<?php`, end with `?>`.
- Model class indented one tab inside `<?php`; `private $prop;`; methods `function name(...){` with no visibility keyword; `camelCase`.
- Single quotes, short arrays `[]`. PDO prepared statements with `?` only.
- Model methods return `['status' => 'success', ...]` or `['status' => 'failed', 'message' => ...]`.
- Controller routing: `if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action']) && $_GET['action'] == 'stream') {`
- Templates: `<?php foreach (...) { ?> ... <?php } ?>`, `<?= ?>`; all printed data through `htmlspecialchars()`.

### JavaScript / CSS
- One `<script>` at the bottom of `index.php`; no libraries or separate files.
- `function name(){`, `const`/`let` (never `var`), `==`/`!=`.
- `fetch(...)` + `FormData` + `.then(...).catch(...)` (no async/await). `document.getElementById`.
- One `<style>` block in `index.php`; no CSS framework.

---

## 6. Knowledge base: `rag-service/data/chunks.json`

A JSON array of 143 objects, ids `K001`–`K143`:
```json
{"id": "K004", "section": "01.2 ...", "title": "01.2 DTI Business Name Registration (Sole Proprietorship) > Who can register", "text": "..."}
```
- `title` starts with a section number (e.g. `01.2`, `02.1A`, `08.3`).
- `text` may contain **status labels**: `(Status: VERIFIED)`, `(Status: FOR VALIDATION, INTERVIEW-DERIVED)`, or inline `*(VERIFIED / INTERVIEW-DERIVED)*`. Label words: VERIFIED, FOR VALIDATION, INTERVIEW-DERIVED, UNVERIFIED, PENDING, GENERAL GUIDANCE.
- `text` may contain **cross-references**: `See 01.6`, `(see 02.3)`, `(02.1 ...)`.
- Some chunks say "Not covered" and name an office to ask (section 08.3).
- Contact emails inside are public government office addresses.

**Status of a chunk** = the text inside the **last** `(Status: ...)` label, or `""`:
```python
found = re.findall(r"\(Status: ([^)]*)\)", text)
return found[-1] if found else ""
```

---

## 7. Python RAG service

### 7.1 `build_index.py`
Constants: `EMBED_MODEL = "bge-m3"`, `DB_PATH = BASE / "chroma_db"`, `COLLECTION = "knowledge_base"`, `BATCH_SIZE = 12`.
Function `get_status(text)` (as in section 6). Top-level steps:
1. load chunks → print `Loaded {n} chunks`
2. `chromadb.PersistentClient(path=str(DB_PATH))`; `try: client.delete_collection(COLLECTION) except Exception: pass`; `create_collection(name=COLLECTION)`
3. per batch of 12: embed `title + "\n" + text` with `ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"]`; `collection.add(ids, documents=text only, embeddings, metadatas={"section", "title", "status"})` (status must be a string, Chroma rejects None) → print `Saved {done} / {total}`
4. print `Done. The collection has {count} chunks.` → must be 143, also on re-runs.

### 7.2 `retrieval.py`
Constants: `EMBED_MODEL = "bge-m3"` and
```python
STOPWORDS = set(
    "the a an and or of to in for is are do does i my me ng sa ang mga na ba ko ako po at ay kung may "
    "can what how much who where when with be it this that you your on by as from".split()
)
```
**`tokenize(text)`**: `re.sub(r"[^a-z0-9₱%]+", " ", text.lower()).split()`, keep words with `len > 1` not in STOPWORDS. (₱ and % are kept.)

**`KeywordIndex`** (`"""BM25 keyword search over the knowledge base passages."""`)
- `__init__(chunks)`: `ids`; `docs` = tokenize(title + " " + text); `avg_len`; `doc_freq[w]` = number of docs containing w.
- `scores(question)` → `{id: score}` for every chunk, BM25 with **k1 = 1.2, b = 0.75**:
```python
rarity = math.log(1 + (total - self.doc_freq[w] + 0.5) / (self.doc_freq[w] + 0.5))
tf = counts[w]
score += rarity * tf * 2.2 / (tf + 1.2 * (1 - 0.75 + 0.75 * len(words) / self.avg_len))
```

**`Retriever`** (`"""Hybrid search: meaning (ChromaDB + bge-m3) and keywords (BM25), merged."""`)
- `__init__()`: `self.chunks = {id: chunk}`, `self.titles = {id: title}`, `self.keyword = KeywordIndex(chunks)`, `self.collection = PersistentClient(BASE / "chroma_db").get_collection("knowledge_base")`.
- `meaning_ranking(question)`: embed `[question]`; query with `n_results=self.collection.count()` (all chunks); return `ids[0], distances[0]`. Distance is Chroma's default squared L2 (same ranking as cosine for normalized vectors); smaller = closer.
- `keyword_ranking(question)`: ids sorted by BM25 score, highest first, only scores > 0.
- `search(question, n_meaning=2, n_hybrid=3, k=5)`:
  1. fuse with Reciprocal Rank Fusion: for each list, `fused[cid] += 1 / (60 + rank)` (rank from 0)
  2. `hybrid_ids` = sorted by fused score
  3. alternate top 2 meaning ids with top 3 hybrid ids, skipping duplicates:
```python
picked = []
for i in range(max(n_meaning, n_hybrid)):
    if i < n_meaning and meaning_ids[i] not in picked:
        picked.append(meaning_ids[i])
    if i < n_hybrid and hybrid_ids[i] not in picked:
        picked.append(hybrid_ids[i])
```
  4. `return picked[:k], meaning_ids, keyword_ids, distances[0]`. `picked` has 3–5 ids; do not fill it up. The 4th value (best **meaning** distance) is used for the off-topic check.

Why hybrid: meaning search alone missed **K004** ("Who can register") for "Who can register a business name with DTI?"; BM25 ranks it first.

### 7.3 `search.py` (debug)
`question = " ".join(sys.argv[1:]) or "Who can register a business name with DTI?"`. Prints `Question: ...`, `Closest meaning distance: 0.521`, then lists (two spaces, id, two spaces, title) under `Meaning search (top 5):`, `Keyword search (top 5):`, `Final picks (hybrid):`.

### 7.4 `generator.py`
`CHAT_MODEL = "gemma3:4b"`. `RULES` exactly:
```
You are the Small Business and Livelihood Assistant for Baguio City and Benguet, Philippines.
Rules:
1. Use ONLY the facts in CONTEXT. Do not use outside knowledge.
2. Numbers rule: state an amount, fee, rate, age, or date ONLY if CONTEXT gives it for the exact agency, program, and item the user asked about. Never move a number from one agency or program to another. If the exact number is not in CONTEXT, say you don't have that information and name the office to ask.
3. Only if a CONTEXT entry about the exact topic asked says "Not covered", say you don't have it and refer the user to the office named there. Otherwise answer from CONTEXT normally.
4. When you refer the user to an office, name only offices that appear in CONTEXT.
5. If the question is not about business, livelihood, permits, taxes, loans, or training (for example weather, tourist spots, food, news, or general knowledge), reply with exactly this sentence and nothing else: "I can only help with small business and livelihood questions for Baguio City and Benguet." Do not name any office.
6. Never promise that a loan, grant, or application will be approved; say approval is decided by the agency.
7. Only for renewal schedules that change every year, tell the user to check the current advisory.
8. Write the whole answer in the ANSWER LANGUAGE given at the end. Keep agency and program names as they are.
9. Be brief: 2 to 5 sentences or a short list. Do not write citations or section numbers; the sources are shown to the user separately.

CONTEXT:
```
(The Python string ends with `CONTEXT:` and a newline.)

```python
OFF_TOPIC_DISTANCE = 1.0
OFF_TOPIC_REPLY = "I can only help with small business and livelihood questions for Baguio City and Benguet."
```

- `chunk_status(text)`: section 6.
- `clean_context(text)`: removes status labels and cross-references, in this order:
```python
text = re.sub(r"\n?\(Status:[^)]*\)", "", text)
text = re.sub(r"\*?\((?:VERIFIED|FOR VALIDATION|INTERVIEW-DERIVED|UNVERIFIED|PENDING|GENERAL GUIDANCE)[^)]*\)\*?", "", text)
text = re.sub(r"\(\s*see [^)]*\)", "", text, flags=re.I)
text = re.sub(r"\s*see \d\d(?:\.\d+[A-Z]?)*(?:(?:,\s*|,?\s*and\s+)\d\d(?:\.\d+[A-Z]?)*)*\.?", "", text, flags=re.I)
text = re.sub(r"\(\s*\d\d\.\d[^)]*\)", "", text)
text = re.sub(r"[ \t]+\n", "\n", text)
return re.sub(r"\n{3,}", "\n\n", text).strip()
```
- `build_prompt(question, chunks)`: `RULES` + chunks as `### {title}\n{clean_context(text)}` joined by blank lines + `\n\nANSWER LANGUAGE: English.`
- `stream_answer(question, chunks)`: generator over
```python
ollama.chat(
    model=CHAT_MODEL,
    messages=[
        {"role": "system", "content": build_prompt(question, chunks)},
        {"role": "user", "content": question + "\n\n(Answer in English.)"},
    ],
    stream=True,
    options={"temperature": 0.1, "num_predict": 300, "num_ctx": 4096},
)
```
yielding `part["message"]["content"]`.

### 7.5 `ask.py` (terminal)
One `Retriever`. `ask(retriever, question)`: search → if best distance > `OFF_TOPIC_DISTANCE`: print `\nAnswer: {OFF_TOPIC_REPLY}` and `\n(off-topic: closest passage distance {d:.3f}, model not called)`, return. Else print `\nAnswer: ` and stream pieces (`end="", flush=True`), then `\n\nSources:` with `  - {title}` + `  [{status}]` if any, then `\n(first words after {x:.1f} s, full answer in {y:.1f} s)`. With argv: one question; without: prints `Small Business and Livelihood Assistant. Type a question, or press Enter to quit.` and loops on `input("\nYou: ")` until an empty line.

### 7.6 `api.py` (Flask)
```python
MAX_QUESTION_LENGTH = 500
app = Flask(__name__)
retriever = Retriever()  # loaded once at startup, shared by every request
...
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
```
Input for both endpoints: JSON `{"question": "..."}`, read with `request.get_json(silent=True) or {}`, `str(...).strip()`.

**`POST /ask`** (whole answer at once)
| Case | Response |
|---|---|
| empty | 400 `{"error": "Please type a question."}` |
| > 500 chars | 400 `{"error": "Please keep your question under 500 characters."}` |
| off-topic (best distance > 1.0) | 200 `{"answer": OFF_TOPIC_REPLY, "sources": [], "off_topic": true, "seconds": 0.1}` |
| success | 200 `{"answer": "...", "sources": [{"id", "title", "status"}], "off_topic": false, "seconds": 13.0}` |
| `ollama.ResponseError` 404 | 503 `{"error": "A model is not installed in Ollama: ..."}` |
| other `ollama.ResponseError` | 502 `{"error": "The model returned an error: ..."}` |
| `ConnectionError` or `httpx.ConnectError` | 503 `{"error": "Cannot reach Ollama. Is it running on localhost:11434?"}` |

Search is inside the same `try` (it calls Ollama for the embedding). Both connection exceptions are needed: the **streaming** chat call raises `httpx.ConnectError`, not `ConnectionError`; catching only the latter crashed with a 500 in testing.

**`POST /ask/stream`** (always HTTP 200, `mimetype="application/x-ndjson"`, one JSON object per line, `json.dumps(fields) + "\n"`):
```
{"type": "text", "text": "Any"}
{"type": "text", "text": " Filipino"}
...
{"type": "done", "sources": [{"id": "K003", "title": "...", "status": "VERIFIED"}], "off_topic": false, "seconds": 8.9}
```
Off-topic: one `text` line with `OFF_TOPIC_REPLY`, then `done` with `"sources": [], "off_topic": true`. Any failure (same cases and messages as `/ask`): a single `{"type": "error", "error": "..."}` line. Errors are lines, not status codes, because the status is already sent once streaming starts.

---

## 8. PHP web app

### 8.1 `config/dbconn.php`
`$host = "localhost"`, `$user = "root"`, `$password = ""`, `$dbname = "sbl_chatbot_db"`, `$charset = "utf8mb4"`, DSN `mysql:host=$host;dbname=$dbname;charset=$charset`, options `ERRMODE_EXCEPTION`, `FETCH_ASSOC`, `EMULATE_PREPARES => false`; `$pdo` created in `try/catch(PDOException $e){ echo $e->getMessage(); }`.

### 8.2 `model/chatbot.php` — class `Chatbot`
- `private $pdo;` `private $ragUrl = 'http://localhost:5000';`
- `saveMessage($sessionId, $role, $content, $sources = null, $responseTime = null)`: `INSERT INTO messages(session_id, role, content, sources, response_time) VALUES(?,?,?,?,?)`
- `getMessages($sessionId)`: `SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC`
- `callRag($endpoint, $payload)`: cURL POST JSON to `$this->ragUrl . $endpoint`, `CURLOPT_RETURNTRANSFER`, `CURLOPT_TIMEOUT => 120`; on cURL failure returns `['error' => curl_error(...)]`, else `json_decode($result, true)`.
- `ask($sessionId, $question)` (non-streaming, kept for testing): empty → failed `'Please type a question'`; save user message; `callRag('/ask', ['question' => $question])`; time with `microtime`; no `answer` → failed `'Could not get an answer. ' . ($data['error'] ?? '')`; save bot message with sources; return `['answer', 'sources', 'time', 'status' => 'success']`.
- `askStream($sessionId, $question, $send)` (used by the page):
  1. empty → `$send(json_encode(['type' => 'error', 'error' => 'Please type a question']) . "\n")`, return
  2. save user message, start timer, `$body = ''`
  3. cURL to `/ask/stream` with `CURLOPT_WRITEFUNCTION => function($ch, $chunk) use (&$body, $send){ $body .= $chunk; $send($chunk); return strlen($chunk); }` (no RETURNTRANSFER; `&$body` must be a reference)
  4. cURL failure → `$send` an `error` line `'Could not get an answer. ' . $error`, return
  5. parse `explode("\n", $body)`: concatenate `text` pieces; on `done` set `$done = true` and take sources
  6. only if `$done`: save bot message `trim($answer)`, sources, time. Failed streams save no bot message.
- **Sources storage**: `json_encode($sources, JSON_UNESCAPED_UNICODE)` into the `sources` TEXT column; an empty list is stored as `NULL` (not `"[]"`).

### 8.3 `controller/chatbot_action.php`
1. include `dbconn.php` and `chatbot.php`
2. `session_start(); $sessionId = session_id(); session_write_close();` (release the session lock so a slow answer doesn't block other requests)
3. `set_time_limit(180);`
4. **GET `?action=get`**: one bubble per message:
```php
		foreach ($messages as $msg) { ?>
			<div class="<?= $msg['role'] ?>">
				<?= nl2br(htmlspecialchars($msg['content'])) ?>
				<?php if ($msg['role'] == 'bot' && !empty($msg['sources'])) { ?>
					<div class="sources">
						Sources:
						<?php foreach (json_decode($msg['sources'], true) as $source) { ?>
							<br>- <?= htmlspecialchars($source['title']) ?>
							<?php if (!empty($source['status'])) { ?>
								[<?= htmlspecialchars($source['status']) ?>]
							<?php } ?>
						<?php } ?>
					</div>
				<?php } ?>
				<?php if ($msg['role'] == 'bot' && !empty($msg['response_time'])) { ?>
					<div class="sources"><?= $msg['response_time'] ?> s</div>
				<?php } ?>
			</div>
		<?php }
```
   then `exit;`
5. **POST `?action=stream`**: `header('Content-Type: application/x-ndjson');` close every output buffer (`while (ob_get_level() > 0) { ob_end_flush(); }`), then `$chatbot->askStream($sessionId, $question, function($chunk){ echo $chunk; flush(); });` and `exit;`. Without this PHP buffers the stream into one reply. (Tested: XAMPP Apache does not buffer after this.)
6. **plain POST**: `echo json_encode($chatbot->ask($sessionId, $question));`

### 8.4 `views/index.php`
Markup: `.card` (700 px, 1 px black border, radius 25 px) containing a centered `<h2>Small Business and Livelihood Assistant</h2>`, `#chatbox` (flex column, gap 10 px, min-height 300 px, max-height 500 px, scroll), `#askForm` with a `.align` row of `<textarea name="question" placeholder="Type your question...">` and `<button name="submit">Send</button>`, and `#message` for errors.
CSS: `.user` right-aligned, background `#1f6f50`, white text; `.bot` left-aligned, `#f0f0f0`; both padding `10px 14px`, radius 12 px, max-width 80%; `.sources` 12 px, `#555`, margin-top 8 px; body flex column centered, sans-serif.

JS:
- `ask()`: on submit, `preventDefault`; `FormData`; empty → `Please type a question` in `#message`; else clear `#message`, `form.reset()`, append `<div class="user">${escapeHtml(question)}</div><div class="bot">Thinking...</div>`, scroll down, `const bubble = chatbox.lastElementChild;`
  - fetch `../controller/chatbot_action.php?action=stream` (POST, FormData); read `response.body.getReader()` with a `TextDecoder`; keep a line `buffer` (split on `\n`, keep the last unfinished piece); for each line: `text` → append to `answer`, `bubble.innerHTML = escapeHtml(answer).replace(/\n/g, '<br>')`, scroll; `error` → show in `#message`. When the stream ends → `loadMessages()`.
  - `.catch`: `console.error`, `Server error` in `#message`, `loadMessages()`.
- `loadMessages()`: fetch `?action=get` as text into `#chatbox`, scroll down.
- `escapeHtml(text)`: `&` → `&amp;` first, then `<`, `>`, `"`, `'`.
- On load: `loadMessages(); ask();`

---

## 9. Database (MySQL)

```sql
CREATE DATABASE sbl_chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE sbl_chatbot_db;

CREATE TABLE messages (
	id INT AUTO_INCREMENT PRIMARY KEY,
	session_id VARCHAR(128) NOT NULL,
	role ENUM('user','bot') NOT NULL,
	content TEXT NOT NULL,
	sources TEXT NULL,
	response_time DECIMAL(6,2) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	INDEX (session_id)
);
```
`sources` = JSON list of `{"id", "title", "status"}`, or NULL. Chat history is per PHP session (per browser).

The Chroma knowledge base (`rag-service/chroma_db/`) is generated by `build_index.py` on each machine; it is never committed.

---

## 10. Decisions and why

| Decision | Why |
|---|---|
| gemma3:4b on CPU | 8b is 20–30 s+, 12b too slow on the team's laptops |
| bge-m3 embeddings | multilingual: Filipino/Taglish/Ilocano questions still find English passages |
| Hybrid search (meaning + BM25 + RRF), 2 meaning + 3 hybrid picks | meaning-only missed exact-wording passages (K004); this mix is the tested configuration |
| English-only answers | LLM language detection was unreliable (qwen3:8b 20–27/36, gemma3:4b 18–30/36); neither model writes Ilocano (gemma: broken; qwen: wrote Waray); gemma ignores "write Taglish" |
| "(Answer in English.)" after the question | the ANSWER LANGUAGE line alone lost to an Ilocano question; repeating it next to the question fixed it |
| Status labels and "see 01.6" removed from the prompt | the model copied them into answers; sources are shown separately |
| Off-topic cutoff 1.0 in code + rule 5 | instant reply without the model; on-topic 0.48–0.97 vs off-topic 0.99–1.44. Do not go below 0.98 ("Negosyo Center in La Trinidad" = 0.973) |
| Sources from the retriever | the model can't make up sources |
| Flask, not FastAPI | fewer concepts; one endpoint pair; no async needed |
| NDJSON streaming, errors as lines | the browser can show words as they come; status code is already sent once streaming starts |
| One Retriever per process | loading chunks + BM25 + Chroma takes seconds |
| Flask on 127.0.0.1 only | only PHP on the same machine should call it |
| Repo cloned outside htdocs + junction | Apache must not serve the Python code and data |

---

## 11. Expected results (use for testing)

| Check | Expected |
|---|---|
| `python build_index.py` | ends `Done. The collection has 143 chunks.` (also on re-run) |
| `search.py` default question | distance ≈ 0.521; meaning top 5 `K003, K031, K057, K009, K011`; keyword top starts `K004`; hybrid picks `K003, K031, K009, K004` |
| `search.py "How much is the DTI business name registration fee?"` | distance ≈ 0.584; hybrid picks `K035, K008, K005, K003` |
| weather question | distance ≈ 1.03 → off-topic reply, model not called, ~0.1 s |
| "Tell me a joke." | ≈ 1.07 → off-topic |
| "Where is the Negosyo Center in La Trinidad?" | 0.973 → answered (not blocked) |
| DTI fee answer | ₱200 barangay, ₱500 city/municipality, ₱1,000 regional, ₱2,000 national, + ₱30 documentary stamp tax |
| sari-sari store permit fee | no invented amount; refers to City Treasurer's Office / eBPLS |
| Filipino or Ilocano question | answer in English |
| Flask down, web page | "Could not get an answer. Failed to connect to localhost port 5000 ..." under the form |
| Ollama down, API | 503 "Cannot reach Ollama. Is it running on localhost:11434?" |
| Streaming | words arrive ~0.14 s apart through Flask and through PHP |

---

## 12. Known limitations (leave them unless an issue says otherwise)
- "Ano ang magandang pasyalan sa Baguio?" (0.988) passes the cutoff; the model may say "I don't have that information" instead of the off-topic sentence.
- When the RAG service is down, the page shows cURL's technical message.
- A failed request leaves the user's question saved without a bot reply.
- One CPU = one answer at a time; simultaneous users wait.
- No authentication on the Flask API (it only listens on 127.0.0.1).

## 13. Not built yet (future work, not in the current issues)
Request queue, rate limiting, Lab 4.2 `<user_data>` prompt-injection wrapping, friendlier offline error, API secret key, going live with a Cloudflare Tunnel or ngrok, agency filter, LangChain rebuild (Lab 2.1), Lab 4.3 risk register.

## 14. Build order (GitHub issues)
| # | Task | Blocked by |
|---|---|---|
| 1 | Read first (rules + setup) | — |
| 2 | Build the knowledge index | — |
| 3 | Meaning search | #2 |
| 4 | Keyword + hybrid search | #3 |
| 5 | Answer in the terminal | #3 |
| 6 | Off-topic check | #5 |
| 7 | Flask API `POST /ask` | #6 |
| 8 | Web chat page (temporarily calls Ollama directly) | — |
| 9 | Connect web to API + sources | #7, #8 |
| 10 | Streaming | #9 |

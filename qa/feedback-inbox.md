# Feedback inbox

Verbatim user feedback, appended by any session, never edited. `/checker` folds items into
`qa/contracts/` (criticality-gated). The maker never edits a contract directly.

Format: `## <ISO datetime> — <source>` then the feedback verbatim, then `**Status:** unfolded | folded → <contract> | GATED`.

---

## 2026-09-03 — Umesh, initial vision (goal.md, Hinglish, transcribed)

> auto testing tool banane ka … AI based system banayenge, jisme UI bhi rahega … user us project ki
> saari details provide kar de … user apne product ki video bhi daal sakta hai, email daal sakta hai
> ki process kaise hona chahiye … Gemini ki API vagera bhi use kar lenge … un testing videos se
> Gemini vision model se step by step flow samajh lenge aur iske basis par eval methods bana denge …
> issue sabse zyada yahi rehta hai ki naye features banate waqt, ship karte waqt, purane features,
> purani API break ho jaati hai … jab bhi testers ya developer develop karenge, test karenge, uske
> baad hamara system run karega aur wo saare eval check … agar wo sab nahi hain to system video maang
> lega, video ke basis par workflow diagram kind of bana le, screen by screen … isme saare best case,
> worst case, edge cases cover hone chahiye, usually AI ka nature ye rehta hai ki wo best case
> scenario se portal explore karke nikal jaata hai, but is project ka worst case scenario, edge cases
> ko bhi test karna hai … real visible browser mein testing kare … cloud sign in … ya koi advance
> model use kar lenge jiska user API key de dega

**Status:** folded → plan v2 §1/§4/§5, `qa/contracts/core-invariants.md`, `qa/contracts/browser-and-secrets.md`

## 2026-09-03 — Umesh, on schema and system design

> sabse important iska schema aisa rakhna jo scalable ho and system design ko bhi pehle plan kar le
> properly … kyunki ye scalable hoga toh DRY principle use ho … humne abhi recent mein ek ERP product
> banaya … usme schema aur system design kaise flow hoga, wo kuch nahi decide hua, aur uske baad ye ho
> gaya ki jab main cloud chalata hoon toh cloud itne zyada tokens khaata hai just for holding the
> context … uska koi schema, koi structure hi nahi, har jagah code repeated hai … na main acche se
> khud se read kar paata hoon, na kuch wo kar paata hoon, toh human agar kuch karna chahe toh at the
> end wo control hi nahi le paayega … human engineer bhi usko samajh paaye, uske hisaab se kaam kar paaye

**Status:** folded → `qa/contracts/core-invariants.md` C1–C4, C6 (the whole contract exists because of this)

## 2026-09-03 — Umesh, on credentials

> isme ek file aur place credentials daalne ki bhi honge jo .env file mein aayenge and it must need to
> be highly secure so that our system and /portal-explorer and all can use the portal in live visible browser

**Status:** folded → `core-invariants.md` C5, `browser-and-secrets.md` B1–B4

## 2026-09-03 — Umesh, north star

> end goal ye hai jo tu north star rakhna ki at the end we will conduct a competition like google and
> all jahan ek taraf ek manual tester hoga who is expert in the field aur ek taraf hamara tester hoga
> and dono ko same document and flows and videos ya jo kuch material milenge and our system should beat them

**Status:** folded → `.goal` north star, `schema/bench.py` (BenchCorpus/BenchTrial/score), task T-120

## 2026-09-03 — Umesh, mid-cycle (chat)

> nhi place .env too in the root directory of d/autoTesting/.env

**Status:** folded → `browser-and-secrets.md` B1 + `core-invariants.md` C5 (2026-09-03, /checker
cycle-2 check of t011-secret-store; routine, non-safety-weakening — see each contract's amendment
log; commit: the cycle-2 verdict commit). Code side (`core/paths.py::env_file` → repo root) verified.

## 2026-09-03 — Umesh, on DB (chat)

> isme db and all bhi tho hoga naa mongo and all ka dunga mai tujhe tere .env mai

**Status:** SUPERSEDED (2026-09-04, see the Mongo/login entry below and
`browser-and-secrets.md` amendment log) — Umesh's later instruction reversed this proposal:
`PATHLYNKS_MONGO_URI` was removed rather than formalised as a `SecretRef`. `EvidenceKind.DB` for
backend assertions remains a real future idea (`browser/db.py` still exists, unwired) but is no
longer tied to this proposal's shape; re-propose fresh if/when an `execute` contract needs it.
*/checker 2026-09-03 (cycle-2 check): deliberately left unfolded — no B1–B9 or C1–C8 criterion
covers backend assertions; fold when the `execute` contract is initialised. Recorded in the
browser-and-secrets amendment log so it is not lost.*

## 2026-09-03 — checker AT-004, contract tension (browser-and-secrets B1 vs B4)

B1 "undeclared keys are ignored" vs B4 "masks every secret value". **Maker resolved in code toward
B4** (undeclared values are masked and prompt-guarded, never resolvable). Checker to confirm and
amend B1 wording to "ignored for use, still masked". Especially relevant now that `.env` is
repo-root and shared across projects.

**Status:** folded → `browser-and-secrets.md` B1 ("ignored for use, still masked"; 2026-09-03,
/checker cycle-2; routine — tightens B4, does not weaken B1; commit: the cycle-2 verdict commit).
Code behaviour independently reproduced, AT-004 marked fixed.

## 2026-09-03 — maker (T-005 cycle 1), defect found in a protocol tool

`scripts/append_decision.ps1` (copied from `D:/ai_os/templates/lab-protocol/`) reads the entry file with
Windows-PowerShell default encoding, so D-005's `·` and `—` landed in `docs/DECISIONS.md` as `Â·` / `â€”`.
DECISIONS is append-only, so D-005 stays as written; a `session` entry (D-006) records the fix.
Maker is correcting the script's read/write encoding to UTF-8 under D-000 `Changes-authorized`
(`scripts/append_decision.ps1` is listed). Checker: please verify the fix and consider filing the
template-level defect upstream (`D:/ai_os/templates/lab-protocol/scripts/append_decision.ps1`) — that is
outside this project's root, so the maker does not touch it.

**Status:** unfolded (tooling defect, not a contract change)
*/checker 2026-09-03 (T-005 cycle-1 check): the in-repo fix is verified - ran the working-tree `scripts/append_decision.ps1` (`-Encoding UTF8` on the entry read, the live-file read, and the raw read before append) against a scratch copy of `docs/DECISIONS.md`; the appended entry carried `·` and `—` as clean UTF-8 (`c2 b7`, `e2 80 94`), no `Â·`/`â€”`. Authorization: D-000 `Changes-authorized` lists `scripts/append_decision.ps1` with `Approved-by: Umesh`; D-006 records the change. The template-level copy at `D:/ai_os/templates/lab-protocol/scripts/append_decision.ps1` is outside this root - left unfolded here on purpose; it is a note for Umesh / the AIOS session, not a contract item for this project.*

## 2026-09-03 — Umesh, on provider architecture (mid T-050 build)
**Source:** chat, this session, while T-050 was blocked on ANTHROPIC_API_KEY being empty.
**Verbatim:** "मैं पहले से ही यह discuss करके confirm कराया, right? कि किसी भी एक model पे कभी dependency नहीं होगी, it should be lang chain system और whatever की, हम जब चाहेंगे, हम anthropic में भी shift होंगे, अगर गो नहीं होगा, Gemini यहीं पे होंगे, Gemini नहीं होगा, तो Olama में होंगे, Chat, GPT में होंगे, तो there should be either fallback system और lang chain का use कर ले, ताकि कोई भी API. चलो वो अलब sign up process है, तो वो बन जाएगा conditional, otherwise बाती सब का lang chain भी तुरू कर ले,"
**Reading:** no single-provider dependency; a fallback chain across Anthropic → Gemini → Ollama →
ChatGPT; built on LangChain rather than a hand-rolled per-vendor Provider class.
**Status:** folded → `qa/contracts/langchain-fallback.md` (T-055, new contract) — delivered and
checker-PASSed (`qa/verdicts/t055-langchain-fallback.md`, PASS). The automatic
Anthropic → Gemini → Ollama → ChatGPT fallback chain now exists; see that contract for the
criteria actually shipped.
*/checker 2026-09-04 (sweep): reconciled — this entry sat at "unfolded (deliberate)" after T-055
had already shipped and PASSed.*

## 2026-09-03 — Umesh, on Docker + live-watch + UI polish
**Source:** chat, this session.
**Verbatim (Hinglish):** "mai khaa dekh sakta hu. live runn krr aur system mai docker mai runn
krr and ui ko user friendly bnaana hai bss functionalty nhi bnaani hai" — "Where can I watch?
Run it live, run the system in Docker, and make the UI user-friendly — just don't build new
functionality."
**Reading:** three infra/presentation asks, explicitly scoped away from pipeline logic: (1)
dockerize the system, (2) a live-watch view for the headed browser inside Docker (clarified with
Umesh: noVNC embedded in the browser, local dev machine only — no remote/cloud hardening in
scope), (3) CSS-only UI polish across existing routes.
**Status:** folded → `qa/contracts/docker.md` (D1-D6, new) + `qa/contracts/ui.md` amendment log
(2026-09-03, /checker, docker-live-ui unit) — shared-layout invariant and `/live` route now
recorded. Verified: `qa/verdicts/docker-live-ui.md` (PASS, cycle 1).

*/maker 2026-09-03 (housekeeping pass): this item's status text still reads "unfolded" but the
proposal was actually delivered by T-090 -- `qa/contracts/db-assert.md` exists,
`browser/db.py::ReadOnlyCollection` is built, `EvidenceKind.DB` is a real enum member, and
`PATHLYNKS_MONGO_URI` is declared as a `SecretRef` in `projects/pathlynks/project.json`. Flagging
for the checker to reconcile the status line to "folded -> db-assert.md" -- not editing it myself
since contract/ledger status is checker-owned.*

## 2026-09-04 — Umesh, on Mongo/DB access and login credentials
**Source:** chat, this session, looking at the live credentials page.
**Verbatim (Hinglish):** "ye btaa mongo db ya mongo uri kyu chaiye tujhe db kyu chaiye hoga
tester ko. jaise ek tester test krna hai live browser mi jaake vese krega naa tu browser prr aur
ek project k liye tujhe bss login id and password hi tho chaiye vo bhi user se ya tho le lee ya
better ki usre ko browser khol kr bolo ki login krkee de dee." Follow-up on login options: "hamare
paas bhi rakho but only in specific cases after the user somehow ignore the first 2 jaise
pathlynsk test krna hoga tujhe tho mai tujhe system mai filll kreke de dunga bss like teeeno rakho
option."
**Reading:** (1) why does the system need Mongo DB access — a tester should just watch the real
browser, like a human would; (2) for login, prefer NOT storing a password at all — open the
visible browser and let the human log in manually once (the persistent profile means this only
ever needs to happen once per project); (3) keep all three mechanisms available: manual login,
.env auto-fill (Umesh will keep providing this for Pathlynks specifically), and the existing
OTP/2FA pause — never remove any of them, just make manual login the no-password-needed default
path for new projects.
**Status:** folded → `qa/contracts/browser-and-secrets.md` amendment log (2026-09-04 row) —
investigated and confirmed `PATHLYNKS_MONGO_URI` was declared in `projects/pathlynks/project.json`
(added by T-090) but genuinely unused by any real case (`browser/db.py` exists and is
unit-tested in isolation, never wired into an actual test case); removed the declaration since
Pathlynks doesn't currently need it, keeping `browser/db.py` available for a future case that
specifically needs backend verification. Built the new `autotester login <slug>` command for
manual one-time login. Shipped and checker-PASSed as unit `manual-login` (cycle 1,
`qa/verdicts/manual-login.md`; ledger F-020) — all three mechanisms (manual login, `.env`
auto-fill, OTP/2FA HITL pause) confirmed still present per Umesh's "teeeno rakho option."
*/checker 2026-09-04 (sweep): reconciles the maker's 2026-09-03 housekeeping flag on the older DB
entry above too — that entry's T-090 delivery is now itself superseded by this one.*

## 2026-09-04 — Umesh, on report-export: a flow diagram idea
**Source:** chat, this session, right after report-export (Excel + HTML) shipped.
**Verbatim (Hinglish):** "tu chahee tho testing report mai ek binary tree flow bhi dikha sakta hai
ek mindmap wise screen by screen kya kya hai and branch by branch reporting too. getting user k
liye bhi flow easy to understand rhegaa. aur tere liye bhi. getting. note it accha hai yee."
**Reading:** the HTML tester report (`stages/report_export.py::export_html`) could additionally
show a tree/mindmap-style visualization of the flow -- screen by screen, branch by branch (worst/
edge/best cases sharing a common entry screen, diverging from there) -- so the overall shape of
what was tested is easy to grasp at a glance, for Umesh and for a future Claude session reading
the same report. Explicitly framed as optional ("tu chahee tho") and asked to be noted, not
necessarily built immediately.
**Status:** unfolded — a real, well-scoped enhancement for a future report-export cycle. Natural
data source: `FlowSpec.flows[].steps` (entry/exit screens) plus each `Case.case_class`/`kind` as
the branch label, rendered as an inline SVG or a simple nested-list tree in the same
self-contained HTML file (no new JS library, matching RE3's "one portable file" constraint).
Deferred, not started this cycle.

**Refinement (2026-09-04, later in the same session, per plan §4):** rendering the *full* branch
tree (every worst/edge/best path, BFS-style — "covering all branches") is the expensive,
worst-case version. What Umesh actually wants is simpler and cheaper: **trace the one path a
given run actually took, DFS-style** — the literal sequence of screens/steps that case followed,
not every hypothetical branch. Re-scoped for whenever this is picked up: a linear step-by-step
trace per case (cheap, always renderable) rather than a full FlowSpec tree (expensive, only
meaningful once a project has many recorded flows). Still not scheduled this cycle — this is a
scoping refinement to the same deferred idea, not a new task.
*/checker 2026-09-04 (sweep): folded in per the plan's own note that this refinement belongs
here; was written into the plan file but not yet mirrored into this inbox until now.*

## 2026-09-04 — Umesh, on report/run-view UI quality (verbatim)

Screenshot of `/projects/pathlynks/report`: "still very bad ui and very non professional, test
dekho kesa dikh rhaa hai, no summary, no overview" — the report page's run-history list has no
at-a-glance summary/overview, just a raw table of run ids and badges.

Screenshot of `/projects/pathlynks/runs/run-01M1NF7RP82ADB72JDW4B47DKF`: "jo ye reporting hai vo
bhi very bad hai non informational too, big images and all" — the run-detail page's per-case
screenshots render oversized and the surrounding info (what was checked, why it passed/failed,
criteria) is thin/non-informative.

Source: direct chat message with an attached screenshot, not a manifest/checker finding.

*Resolved 2026-09-04: qa/manifests/ui-report-informativeness-fix.md, checker-PASSed cycle 1
(qa/verdicts/ui-report-informativeness-fix.md), ledgered docs/FEATURES.jsonl F-027. Report page
now leads with a real overview (total runs, overall pass rate, cases in latest run) and compact
per-run badges; run-detail cards show scoreboard/grader/failure info and screenshots render in a
responsive thumbnail grid instead of native size.*

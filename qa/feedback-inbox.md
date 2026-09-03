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

**Status:** unfolded — proposal: `PATHLYNKS_MONGO_URI` as a `SecretRef`; new `EvidenceKind.DB` for
read-only backend assertions after UI actions. Production Mongo stays read-only by construction.
Needs a contract criterion in a future `execute` contract, not this unit.
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

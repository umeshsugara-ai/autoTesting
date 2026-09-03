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

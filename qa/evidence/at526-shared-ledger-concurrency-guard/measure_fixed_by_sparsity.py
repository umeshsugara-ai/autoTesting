import json, re, os

root = "."
issues = []
with open("qa/issues.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        issues.append(json.loads(line))

fixed = [r for r in issues if r.get("status") == "fixed"]
print(f"total rows: {len(issues)}  fixed rows: {len(fixed)}")

no_fixed_by = [r["id"] for r in fixed if not r.get("fixed_by")]
print(f"fixed rows with NO fixed_by field: {len(no_fixed_by)}")
print(no_fixed_by[:20])

# For those that have fixed_by, try to find a referenced verdict file and check it exists / PASS
verdict_dir = "qa/verdicts"
verdicts_on_disk = set(os.listdir(verdict_dir))

missing_verdict_ref = []
mismatched_cycle = []
for r in fixed:
    fb = r.get("fixed_by", "")
    if not fb:
        continue
    m = re.search(r'qa/verdicts/([\w.-]+\.md)', fb)
    if not m:
        continue
    fname = m.group(1)
    if fname not in verdicts_on_disk:
        missing_verdict_ref.append((r["id"], fname))

print(f"fixed rows whose fixed_by names a verdict file NOT present on disk: {len(missing_verdict_ref)}")
for x in missing_verdict_ref[:20]:
    print(x)

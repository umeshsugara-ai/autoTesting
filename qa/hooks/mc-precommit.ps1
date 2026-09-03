# maker-checker Layer 3 — commit guard (warn, not deny)
# Context-only output. NEVER emit "permissionDecision":"allow" — that skips the permission
# prompt and turns this warn into an auto-approver for anything containing "git commit".
$in = [Console]::In.ReadToEnd()
if ($in -match 'git\s+commit') {
  $u = 0
  if (Test-Path 'qa/manifests') {
    $u = (Get-ChildItem 'qa/manifests' -Filter *.md -ErrorAction SilentlyContinue | Select-String -Pattern 'Status: ready-for-check' -List | Measure-Object).Count
  }
  if ($u -gt 0) { Write-Output ("WARN maker-checker: $u unit(s) still awaiting /checker verdict. Commit should follow a PASS.") }
}
exit 0

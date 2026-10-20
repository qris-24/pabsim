# CP30 — .gitattributes: byte-exact clones on any machine (2026-10-20)

Base: master 52ff9aa (rp-CP29 = 2b5470e). No kernel, test, deck or card-data file changed; test count unchanged (857).

## Summary
- Finding (kernel soak setup): a fresh clone on Codie fails the gate preflight ("frozen baseline changed"). Git for
  Windows sets core.autocrlf=true in C:/Program Files/Git/etc/gitconfig; the repo's own `false` is local config and is
  not cloned, so clones get CRLF and every frozen-file sha256 check fails. The GitHub backup was not restorable as-is.
- Fix: new `.gitattributes` with `* -text`: Git never converts line endings in this repo, whatever the machine setting.
- Verified: fresh clone with default machine settings (no -c core.autocrlf) passes the full gate (see stage-end check).
- The working checkout is unchanged (already LF). The manifest now pins `.gitattributes`.
- Follow-up: C:\pabsim-git backup clone predates this file; re-clone it.

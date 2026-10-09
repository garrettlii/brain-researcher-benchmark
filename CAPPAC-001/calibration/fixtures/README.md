# Verifier calibration fixtures

`python tools/check_verifier.py <TASK>` runs `tests/test_outputs.py` once per fixture
directory, with `OUTPUT_DIR` set to `_base/` overlaid with that fixture's files, and
checks each test's outcome against the fixture's `expect.toml`.

- `_base/`: the real numeric outputs from an oracle run (`harbor run ... --artifact
  /app/output`, or `solution/solve.sh` run locally). Copy the small files only
  (CSV/JSON/small .npy). Leave it empty until the oracle has run; until then, assert
  only the prose-graded test(s).
- `<name>/`: the files that differ from `_base`, usually just `findings.md`, plus
  `expect.toml`:

  ```toml
  note = "where this text came from (reference / adversarial / real run <job id>)"
  [expect]
  test_reproduction_recognises_x = "fail"  # list only the tests you are asserting
  "*" = "pass"                              # optional: every other test
  ```

Build the FAIL set from real agent runs. The sentence in which a real agent described its
pipeline is your hardest negative (the SOCIALBRAIN-001 / DEVCONN-001 false passes).
Every fixture's `note` must say where its text came from.

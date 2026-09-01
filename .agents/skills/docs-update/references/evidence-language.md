# Evidence language

Use the narrowest accurate status:

- **Implemented:** the current source contains the behavior or structure.
- **Automated-test verified:** named automated checks passed in the current
  session and cover the stated claim.
- **Manually verified:** the stated manual or browser check was performed in the
  current session.
- **Pending:** approved or planned work that is not implemented yet.
- **Unverified:** plausible current behavior that was not established by the
  inspected evidence.
- **Historical:** a dated record of earlier state; do not present it as current.

Before finalizing a documentation change, check:

- Does each test, Ruff, browser, provider, or readiness claim name evidence that
  actually exists?
- Are implementation and verification described separately?
- Are limitations and pending work clearly distinct from current behavior?
- Are planned paths labeled as planned?
- Are exact counts and dates necessary and current?
- Does the edit preserve authoritative historical evidence?

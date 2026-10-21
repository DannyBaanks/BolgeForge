# Correction to the frozen M0/M3 experiment contract

The 2026-10-20 audit found that the VM frozen in `CONTRACT_CAT_QUINE.md` was a permissive dialect. It omitted address-dependent loader validation and advanced past nonprintable program-counter words. These are not Classic Malbolge semantics.

The M3 selector candidate is rejected by the original strict loader on both input branches. Its saved hashes attest file integrity, not Classic conformance. The historical reports, frozen contract and raw evidence remain unchanged. Any later Classic milestone must use the corrected strict oracle, require actual HALT, and record fresh evidence.

See [the E2E audit](../../docs/audits/2026-10-20-e2e/REPORT.md), [repair report](../../docs/repairs/2026-10-20/REPORT.md) and current [README](../../README.md). A valid Classic Q/C selector remains **NOT_DEMONSTRATED** for this candidate.

Status update (closure pass, 2026-10-20): the Q/C selector is retired as a
published claim; the audit's NOT_DEMONSTRATED result for the preserved candidate
stands. The contract's CAT payload echo remains open research. See
`docs/CLAIMS.md`.

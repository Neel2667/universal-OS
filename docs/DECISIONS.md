# Architecture decision record index

Architecture decisions are immutable once accepted; a later ADR supersedes rather than silently edits an earlier one.

## Status legend

- **Proposed:** needs evidence/review; implementation must not depend on it.
- **Accepted:** approved with recorded rationale and consequences.
- **Superseded:** replaced by a named later decision.
- **Rejected:** considered and declined; retain rationale to avoid repeating research.

## Decisions to resolve

| ID | Title | Status | Decision needed before |
| --- | --- | --- | --- |
| ADR-001 | Select the reference device | Proposed | bootstrap implementation |
| ADR-002 | Select the initial system/hardware base | Accepted — see `adr/ADR-002-system-and-hardware-base.md` | native Discovery Base implementation |
| ADR-003 | Select the application compatibility strategy | Proposed | application-runtime work |
| ADR-004 | Adopt signed update metadata and key roles | Proposed | update-agent implementation |
| ADR-005 | Define privacy, telemetry, and account policy | Accepted — see `adr/ADR-005-privacy-diagnostics-account-policy.md` | any cloud-connected preview |
| ADR-006 | Approve design-system direction from Stitch concepts | Proposed | UI-shell implementation |
| ADR-007 | Define supported-device admission and retirement policy | Accepted — see `adr/ADR-007-device-lifecycle-policy.md` | second device port |

## ADR template

```md
# ADR-NNN — concise title

- Status: Proposed | Accepted | Superseded | Rejected
- Date: YYYY-MM-DD
- Owners: @...
- Related issues: #...

## Context
What constraint or question requires a decision?

## Options considered
| Option | Benefits | Costs / risks | Evidence |
| --- | --- | --- | --- |

## Decision
State precisely what is selected and its boundaries.

## Consequences
List implementation work, security/privacy effects, migration/reversal cost, and what is explicitly not decided.

## Acceptance evidence
Tests, documents, prototype results, source/license review, or independent review required before acceptance.
```

# Definition of done

## Every issue

- Problem, scope, non-goals, acceptance criteria, dependencies, and risk label are recorded.
- The work is linked to a milestone and has an owner or explicitly says it is seeking an owner.
- Security/privacy and license impact have been considered; `security` issues use the private reporting route where disclosure would be harmful.
- Documentation and test-matrix changes are included where behavior/support changes.

## Every pull request

- Links its issue using `Refs #N` or `Fixes #N` only when fully complete.
- States user/device impact, test environment, commands/results, and rollback/recovery impact where applicable.
- Contains no credentials, private keys, production signing materials, unique device identifiers, or unredacted logs.
- Is reviewable: focused scope, clear commit history, generated artifacts excluded unless intentionally versioned.
- Updates source/license/provenance records if it introduces external code, firmware, or binaries.

## A device-support claim

- Names the exact model, hardware revision where relevant, bootloader prerequisites, and tested image versions.
- Documents restore/recovery path tested on real hardware.
- Lists functional, partial, untested, and unsupported hardware features separately.
- Includes normal update, failed update, rollback, and power-loss evidence.
- Has an assigned security-maintenance policy and a known issue list.

## A release candidate

- Is built from a tagged/traceable commit with artifact digest, SBOM/provenance record, and signed metadata.
- Passes the target milestone's security, compatibility, recovery, performance, accessibility, and documentation gates.
- Has release notes, known issues, support matrix, rollback instructions, and incident contact process.
- Is independently installed and recovered by at least one person/environment not used for its original build, before public preview.

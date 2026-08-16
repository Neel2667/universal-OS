# UniversalOS initial threat model

## Scope

This model covers the Discovery Base, Bootstrap Capsule selection, hardware profiles, signed registry metadata, package artifacts, local service IPC, update journaling, staging, first-boot health, recovery, and build/provenance paths. It is public by design and excludes weaponized exploit details.

## Assets to protect

```text
boot integrity and known-good recovery path
trusted root and signing-role configuration
package/profile/capsule authenticity and freshness
user data and identifiers
local service authority boundaries
source/firmware/model provenance
release build integrity and traceability
availability of safe recovery/update paths
```

## Trust boundaries

```text
immutable boot ROM / bootloader
  → Bootstrap Capsule
  → Discovery Base and local profile facts
  → signed metadata / untrusted mirrors
  → verified manifests and staged payloads
  → service IPC and health authority
  → user apps / user data
```

## Threat and control map

| ID | Threat | Required control | Current reference evidence | Remaining gate |
| --- | --- | --- | --- | --- |
| T-01 | Malicious or mismatched bootstrap selected | exact board/SoC/architecture/partition/transport match; no wildcard bootstrap; local revalidation | bootstrap resolver tests | real bootloader and recovery proof |
| T-02 | Registry/mirror sends tampered metadata | Ed25519 threshold verification, expiry, root roles | registry tests | offline production key ceremony and mirror design |
| T-03 | Replay of older signed metadata | per-role accepted-version state | rollback test | persistent authenticated state on device |
| T-04 | Package/manifest substitution | signed target binds manifest and payload bytes | artifact binding tests | real downloader and image writer |
| T-05 | Power loss or failed first boot bricks device | staging, current/previous journal, inactive/transactional target, health rollback | install/persistence tests | physical interruption tests |
| T-06 | Untrusted app/UI commits update | capability-gated service protocol and peer-authenticated local IPC | protocol/Unix IPC tests | native service manager and MAC policy |
| T-07 | Fake/stale health report commits bad system | profile/target/freshness/required-service check | health tests | verified-boot-bound health authentication |
| T-08 | Firmware/blob license violation | component provenance and release policy | provenance tests | legal review per real component |
| T-09 | Unique device data enters profile/log/Git | strict profile/discovery/provenance schemas; redacted recovery output | schema/protocol tests | device log review process |
| T-10 | Vendor kernel contains unpatchable critical defect | support tiers and target lifecycle policy | risk register | per-device CVE/maintenance owner |
| T-11 | Recovery unavailable during outage | offline recovery is preflight/bootstrap requirement | preflight/capsule contracts | real USB/factory restore test |
| T-12 | Build compromise produces untraceable image | pinned toolchain, SBOM/provenance plan, reproducible image comparison | build strategy | clean Yocto/Rust build environment |

## Security invariants

1. No online service is the root of trust.
2. A cloud response is a candidate, not permission to execute code.
3. No normal update overwrites the only known-good target.
4. A first boot does not become permanent until a bounded local health condition succeeds.
5. A local app cannot grant itself update, health, recovery, or hardware privileges.
6. A profile never uses IMEI, serial number, account identity, or MAC address.
7. A component without lawful provenance cannot enter a public release.
8. A blocked/unknown condition fails safe and produces a recoverable diagnostic, not a best-effort flash.

## Review process

- Every new Bootstrap Capsule, hardware profile, runtime backend, service method, downloader, or real-device integration updates this model.
- Public issues should describe impact and mitigations, not unpublished exploit chains.
- Sensitive vulnerabilities use `SECURITY.md`, not a public issue.
- Red risks in `RISK_REGISTER.md` require explicit maintainer decision and test evidence before a release.

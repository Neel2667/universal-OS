# UniversalOS experience principles and core journeys

> **Status:** product/UX specification for later shell work. No UI implementation is authorized to imply unsupported device behavior.

## Experience principles

```text
Purposeful, not addictive
One workspace for a goal, not an app-grid-first maze
System state is visible and explainable
Privacy/security choices use plain language
Offline/recovery states are first-class screens
Accessibility and low-end performance are default constraints
```

## Distinct UniversalOS interaction model

UniversalOS should organize activity around **workspaces**:

```text
Study workspace
Travel workspace
Creator workspace
Focus workspace
Private workspace
Recovery workspace
```

A workspace surfaces tasks, content, devices, and system controls relevant to a goal. Apps remain tools inside a workspace; they are not the whole navigation model.

## Required v0.1 journeys

| Journey | Start | Required safe outcome |
| --- | --- | --- |
| USB installation | computer + locked/unlocked check | clear device match/recovery/data-loss information; no arbitrary flash |
| Discovery Base | first boot | visible hardware/profile status; offline path remains available |
| Update available | normal system | release summary, size, power/storage state, user decision |
| Update blocked | low battery/storage/no recovery | understandable reason and remediation; no partial install |
| First boot failed | pending new target | automatic rollback or visible recovery choice |
| Offline use | no network | normal core UI remains usable; update state says offline rather than error loop |
| Privacy review | settings | show network purpose, diagnostics/export controls, account-free status |
| Accessibility | large text/screen reader/reduced motion | no critical control depends only on tiny touch target or animation |

## Explicit UX prohibitions

```text
No fake device support screen
No unexplained loading spinner during recovery
No hidden network transfer
No dark pattern blocking offline use
No “AI assistant” core feature in current scope
No required account wall
```

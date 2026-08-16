# Google Stitch to UniversalOS workflow

1. Choose a documented journey: workspace, update, recovery, offline, privacy, or installation.
2. Generate visual alternatives in Stitch.
3. Record the source/design reference and intended user goal.
4. Translate chosen output into `design-tokens-v1` and workspace/shell state contracts.
5. Add accessibility states: text scaling, high contrast, reduced motion, screen reader, switch navigation.
6. Bind visible actions only to established local service APIs.
7. Test no-network, failure, rollback, and recovery states before visual acceptance.

Stitch output is inspiration and design input; it must never imply unsupported hardware or bypass safe update/recovery policy.

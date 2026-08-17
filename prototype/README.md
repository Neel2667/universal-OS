# UniversalOS shell prototype

A static, non-production visual prototype for the workspace shell, update safety, privacy/accessibility controls, and recovery flow.

```sh
python3 -m http.server 4173 --directory prototype --bind 0.0.0.0
```

It is not connected to device services, cannot stage an update, and makes no hardware claim. It demonstrates the UI contracts in `docs/UI_FOUNDATION.md` and the Stitch workflow.

# UniversalOS network provisioning contract

Network is optional during first installation. USB host transfer and offline bundles are first-class local artifact paths. Wi-Fi is enabled only after a compatible local network stack exists and the user explicitly approves a saved/entered network.

## Five rules

1. No automatic unknown Wi-Fi join.
2. No plaintext password in provisioning manifest, logs, transfer state, or Git; only an opaque reference to a platform credential vault is accepted.
3. Captive portals block artifact fetch until visibly resolved; they never downgrade package verification.
4. Cellular bootstrap is unavailable until a device profile has verified radio support.
5. Network availability is transport only; signed metadata/profile/target checks remain mandatory.

`core/universal_core/network.py` models the states without connecting to a real network. Native Discovery Base later provides the credential vault and actual Wi-Fi/Ethernet adapters.

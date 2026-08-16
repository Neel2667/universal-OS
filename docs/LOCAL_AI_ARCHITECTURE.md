# UniversalOS Local Intelligence architecture

> **Status: proposed research architecture.** Local Intelligence is an optional UniversalOS capability, not a required account, cloud dependency, or boot requirement. The operating system must remain fully usable when no AI model is installed.

## Product goal

UniversalOS should use small local models to make the phone more useful without turning private user data into cloud prompts. The differentiator is not an always-open chatbot. It is a private, low-latency **action and understanding layer** that works with user-approved local information.

```text
Local selection / user voice / explicit task
  → Local Intelligence Broker
  → permission and resource policy
  → task-specific on-device model
  → proposed result or action
  → user review / confirmation for consequential changes
```

## Rules that cannot be bypassed

1. **Offline by default.** The model, index, prompts, and output stay on device unless a user explicitly chooses an external service for a named task.
2. **No ambient authority.** An AI component has no direct access to contacts, files, microphone, messages, location, camera, network, or system-update services. It receives narrowly scoped, temporary inputs through the existing capability system.
3. **No autonomous consequential actions.** The AI may draft, classify, search, explain, or propose. Sending a message, deleting data, changing permissions, spending money, sharing content, or installing an update requires a separate user-confirmed system action.
4. **No hidden continuous recording.** Version 1 uses push-to-talk or an obvious user-enabled listening mode. Background microphone use requires a visible indicator and revocable permission.
5. **Resource-aware operation.** Inference respects battery, charging state, thermal state, memory pressure, active workspace, and accessibility settings. It stops or downgrades rather than making the phone hot, slow, or unusable.
6. **Model provenance.** Model weights are packages: signed metadata, exact hashes, license/reuse record, version, supported languages, runtime requirements, and user-visible size are required before installation.
7. **Human-readable boundaries.** The UI must state what local data was used, which model ran, whether anything leaves the device, and how to erase its local index/history.

## Use the smallest model that solves the task

A language model is not the answer to every problem. Small deterministic or specialist models are faster, cheaper, more private, and easier to validate.

| Capability | Recommended first approach | Why |
| --- | --- | --- |
| System commands | Intent classifier + structured action grammar | More reliable than free-form LLM commands; easy to confirm. |
| File/note search | Local embeddings + encrypted semantic index | Fast natural-language retrieval without sending files to cloud. |
| Notification grouping | Small local classifier/rules | Low memory and predictable behavior. |
| Text rewrite/summarize | Optional 0.3–1.7B quantized local LLM | Helpful for selected text; bounded context and output. |
| Voice commands | Offline keyword spotter + speech-to-text | Works without network; use push-to-talk first. |
| OCR / document scan | Small vision/OCR model | Useful, task-specific, and lower cost than a vision LLM. |
| Image organization | Local image embedding/classifier | User controls which albums are indexed. |
| Personal routine suggestions | Opt-in local event/rule engine | Must be inspectable and never silently automate actions. |

## Hardware tiers

The model manager selects from signed **capability profiles**, not from a marketing promise. Approximate weight memory for 4-bit language models is only a starting point; context cache, runtime buffers, GPU allocation, and model architecture add material overhead.

| Tier | Typical device conditions | Default local intelligence |
| --- | --- | --- |
| Lite | constrained RAM/storage, no usable accelerator | command classifier, keyword spotting, lightweight embeddings, OCR on demand; no general LLM by default |
| Standard | 4 GB+ RAM, sufficient storage, healthy battery | embeddings/search, offline speech, small 135M–360M quantized language helper for explicit tasks |
| Plus | 6 GB+ RAM or proven GPU/NPU capacity | optional 1–2B quantized assistant with bounded context and charging/thermal limits |
| Accelerator | verified compatible GPU/NPU driver and benchmark evidence | same capabilities with a faster backend; never required for basic operation |

A 6 GB Mi A2-class lab device should initially run Lite/Standard tasks, then benchmark an optional small model while charging. It must not be treated as proof that every phone can sustain a 1–2B model.

## Runtime strategy

UniversalOS should use an abstraction so model packages do not become tied to one chip vendor.

```text
Local Intelligence Broker (Rust service)
  ├─ Policy / permissions / resource governor
  ├─ Model Manager / signed model packages
  ├─ Text and embedding adapter
  ├─ Speech adapter
  ├─ Vision/OCR adapter
  └─ Backend selection
       ├─ portable CPU backend (baseline)
       ├─ GPU backend (optional)
       └─ NPU backend (optional and profile-specific)
```

### Baseline runtime choices to evaluate

| Workload | Primary candidate | Why | Fallback |
| --- | --- | --- | --- |
| Small LLM | `llama.cpp` behind a narrow Rust FFI boundary | broad local CPU/GPU support, quantized GGUF models, ARM-oriented optimizations | CPU-only restricted model |
| Embeddings / OCR / classifiers | ONNX Runtime with minimal selected operators | portable model interchange and multiple CPU/mobile execution providers | CPU/XNNPACK path |
| Speech-to-text / TTS / VAD | sherpa-onnx after license/security review | offline speech model ecosystem and ONNX interoperability | text-only commands |
| UniversalOS components | Wasm runtime for untrusted extensions, not for privileged inference host | capability sandboxing and portable third-party components | no extension execution |

The inference host is privileged because it manages model bytes and resource limits, so it is implemented in Rust and exposes only capability-gated local IPC. A model or app component never receives unrestricted OS access.

## Model package contract

A future `uos-ai-model` package must include:

```text
model ID and version
model task: embedding / OCR / STT / TTS / classifier / LLM
runtime and ABI requirements
architecture / accelerator compatibility
minimum RAM and storage
maximum context / input limits
battery and thermal policy
language coverage
exact artifact hashes and signed metadata
model-weight license and redistribution status
privacy statement
index data format and deletion method
benchmark evidence per hardware capability profile
```

The model manager must reject a model whose memory, runtime, signature, license status, or profile requirements are unsuitable.

## AI permission model

```text
App or UI
  → asks Intelligence Broker for a named task
  → broker asks the Capability Service for a temporary scoped input
  → model receives only the approved text/image/audio slice
  → broker returns a result with provenance
  → Action Broker requires user confirmation for a real change
```

Examples:

- A notes app can ask, “summarize the text the user selected,” but not read all notes.
- A mail/message composer can ask for a rewrite of the current draft, but not send it.
- A files search surface can query an opted-in local semantic index, but not export matching filenames/content.
- A voice command service gets microphone audio only after the user activates it and can propose an action, not execute it.

## First release: useful without pretending to be human

1. **Universal Command Palette** — explicit typed/voice commands mapped to safe structured actions.
2. **Private Semantic Search** — opt-in search across selected local files, notes, settings, and app content providers.
3. **Selected-text tools** — summarize, translate, rewrite, explain, or extract tasks from text the user actively selected.
4. **Offline voice input** — push-to-talk speech recognition, local transcription, and visible listening state.
5. **OCR Inbox** — scan an image/document locally, extract text, and let the user decide where it goes.
6. **Resource dashboard** — show model size, RAM use, battery/thermal cost, accelerator backend, model license, and delete controls.

A general chat assistant is an optional Plus-tier feature, never the launch requirement.

## Explicit non-goals for version 1

- Always-on cloud assistant.
- Hidden behavior profiling or advertising targeting.
- Autonomous communication, purchases, permission changes, updates, or file deletion.
- Training a large foundation model from scratch.
- Claiming identical AI speed/quality on every device.
- Installing model weights without user-visible storage and license information.

## Phased implementation

| Phase | Deliverable | Gate |
| --- | --- | --- |
| AI-0 | Model package/profile schema, broker permission contract, resource policy simulator | no model binary, no data collection |
| AI-1 | Local embeddings + semantic search benchmark | encrypted/local index; explicit source selection and deletion |
| AI-2 | Structured command classifier and action-confirmation flow | no ambient system authority |
| AI-3 | Offline speech/OCR adapters | push-to-talk, visible recording state, benchmarked device profiles |
| AI-4 | Optional small quantized LLM | charging/thermal/memory policy and model license review |
| AI-5 | Optional third-party Wasm intelligence extensions | sandbox, capability gating, package signing, abuse review |

## Evidence sources to validate during implementation

- [llama.cpp project](https://github.com/ggml-org/llama.cpp) — local quantized LLM runtime candidate; evaluate CPU, Vulkan/OpenCL, licensing, ABI, and reproducibility per build.
- [ONNX Runtime execution providers](https://onnxruntime.ai/docs/execution-providers/) — candidate portable inference abstraction; benchmark CPU and any device-specific provider rather than assuming acceleration.
- [WASI](https://wasi.dev/) — capability-based Wasm sandbox model for untrusted components.
- [sherpa-onnx offline CTC models](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-ctc/index.html) — possible offline speech inputs; each model requires separate language/license/quality review.
- [SmolLM compact model family](https://github.com/huggingface/smollm/blob/main/text/README.md) — example small-model size family for benchmarks, not a UniversalOS model endorsement.

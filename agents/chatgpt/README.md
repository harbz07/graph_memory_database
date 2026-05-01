# ChatGPT agent component

This directory contains the ChatGPT Constellation member component under `agents/`.

Included pieces:
- `memory_layer.py` — local memory document model, storage, retrieval scoring, and prompt augmentation.
- `runtime.py` — bootloader wiring helpers for `SQLiteSession` continuity and memory-augmented agent execution.

Agent hierarchy:
- **Nova** — default assistant voice (baseline continuity owner).
- **ORION** — takes over fully on handoff trigger for specification/logic tasks.
- **The Fuckface** — takes over fully on handoff trigger for boundary protection.
- **Foundry Keep** — system/environment context; never the active speaker.

Quick usage:
1. Initialize a memory store with `initialize_memory_store(base_dir)`.
2. Call `run_constellation(...)` with your router/specialist agents and override/thread callbacks.
3. Nova is the default agent. Handoff triggers route to ORION or The Fuckface as full persona takeovers.
4. Add additional seed files (`seed_orion`, `seed_nova`, `seed_fuckface`) using the same memory schema.

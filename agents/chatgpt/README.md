# ChatGPT agent component

This directory contains the first Constellation member component under `agents/`.

Included pieces:
- `memory_layer.py` — local memory document model, storage, retrieval scoring, and prompt augmentation.
- `runtime.py` — bootloader wiring helpers for `SQLiteSession` continuity and memory-augmented agent execution.

Quick usage:
1. Initialize a memory store with `initialize_memory_store(base_dir)`.
2. Call `run_constellation(...)` with your router/specialist agents and override/thread callbacks.
3. Add additional seed files (`seed_orion`, `seed_nova`, `seed_fuckface`) using the same memory schema.

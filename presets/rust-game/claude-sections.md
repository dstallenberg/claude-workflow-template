# Rust Game Preset — CLAUDE.md Sections

## CONVENTIONS
- All components derive `Debug, Clone, Copy` and `serde::Serialize, serde::Deserialize`
- Systems are functions: `fn system_name(world: &mut World, ...)` — no `Rc<RefCell<>>`
- Keep game logic in systems, not in component structs
- Fixed timestep for game updates, variable framerate for rendering
- Use `f32` for game coordinates, positions, velocities
- Renderer isolated from ECS: game logic testable without GPU
- Sparse-set storage: O(1) insert/remove/lookup, packed iteration
- **Collect-before-mutate**: When iterating component storage and needing to mutate, collect updates into a Vec first, then apply in a second pass. Avoids borrow conflicts.
- **`Default` trait**: Implement for key types. Used in tests and initialization.
- **Marker components**: Zero-sized structs stored in `ComponentStorage<T>` same as data-bearing components.
- **Numeric type conventions**: `f32` for world positions/velocities, `u32` for entity indices/generations, `i32` for chunk/tile coordinates, `usize` for array indexing.

## CODE_STANDARDS
- **Every system gets tests immediately**: When creating a new system, write `#[cfg(test)] mod tests` in the same session. Minimum: one happy-path test + one edge case.
- **Name every number**: Define `const` values at file top before using them. Exception: obvious math values (0.0, 1.0, 2.0).
- **Add logging with the feature**: When creating a new system, include logging calls inline. State transitions = `debug`, per-tick data = `trace`, anomalies = `warn`.
- **Run `cargo test` after every code change**: Don't batch test runs — verify continuously.

## ERROR_HANDLING
- **Systems**: Return early on missing components — never panic on game state.
- **Initialization** (renderer, window): `.expect("descriptive message")` is fine.
- **Tests**: `.unwrap()` is fine — panicking is the point.
- **No `anyhow`/`thiserror` yet**: Keep error handling simple. Plain `Option`/`Result` with early returns.
- **Never panic in game loop code**: A missing entity or component is not an error — it's a valid state.

## TESTING
- **What to test**: Systems, collision logic, ECS operations, component storage invariants, math helpers.
- **What not to test**: Rendering, window events, GPU init — these require hardware.
- **Test style**: Unit tests in `#[cfg(test)] mod tests` at the bottom of each file.
- **New systems must have tests**: At minimum, test the happy path and one edge case.
- **Run `cargo test` before committing code changes**: All tests must pass.

## DEPENDENCY_PHILOSOPHY
- **Bias toward fewer crates**: This is a from-scratch project for learning and control. Don't add a crate for something achievable in <100 lines.
- **When to add a crate**: When it solves a genuinely hard problem, not for convenience.
- **No `unsafe`**: Keep it that way unless there's a compelling, measured performance need.

## LOGGING
- Log **state transitions**, not state. Event-based, not per-frame.
- `error`: Unrecoverable failures. `warn`: Frame spikes, stale entity ops. `info`: Startup, entity lifecycle. `debug`: Key presses, periodic stats. `trace`: Per-tick data.
- Every new system must include appropriate logging.

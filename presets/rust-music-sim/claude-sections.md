# Rust Music-Reactive Sim Preset — CLAUDE.md Sections

## CONVENTIONS
- Audio analysis is the input, simulation is the output — audio features drive universe behavior, not the other way around
- `f64` for simulation (positions, velocities, masses), `f32` for audio (samples, FFT bins, analysis features)
- Audio analysis runs on a dedicated thread with lock-free communication to the simulation
- Fixed simulation timestep, decoupled from audio analysis rate and render framerate
- Audio features must be smoothed before reaching the simulation — no raw FFT jitter driving physics
- All audio-to-simulation mappings are configurable — hardcoded mappings are temporary placeholders

## CODE_STANDARDS
- **Every system gets tests immediately**: When creating a new simulation system or analysis function, write `#[cfg(test)] mod tests` in the same session. Minimum: one happy-path test + one edge case.
- **Name every number**: FFT sizes, smoothing factors, frequency band boundaries, scaling factors — all named `const` at file top. Exception: 0.0, 1.0, 2.0 in obvious math.
- **Add logging with the feature**: Audio feature events (beat detected, onset) = `debug`, per-frame analysis values = `trace`, audio device issues = `warn`.
- **Run `cargo test` after every code change**: Verify continuously.

## ERROR_HANDLING
- **Simulation systems**: Return early on missing entities — never panic on simulation state.
- **Audio analysis**: Must never block the audio capture thread. Log warnings for edge cases, skip frames if analysis falls behind.
- **Initialization** (audio device, window, GPU): `.expect("descriptive message")` is fine.
- **Tests**: `.unwrap()` is fine.
- **No `anyhow`/`thiserror` yet**: Keep error handling simple. Plain `Option`/`Result` with early returns.

## TESTING
- **What to test**: Audio analysis functions (FFT, onset detection, beat tracking), simulation physics, audio-to-simulation parameter mapping, feature smoothing.
- **What not to test**: Audio device capture, GPU rendering, window events.
- **Test style**: Unit tests in `#[cfg(test)] mod tests` at the bottom of each file.
- **Audio analysis tests**: Generate synthetic waveforms (sine, impulse, white noise), run analysis, verify expected features (e.g., sine at 440Hz → spectral peak at 440Hz).
- **Simulation tests**: Feed known audio feature values, run N timesteps, assert expected simulation behavior.
- **Run `cargo test` before committing**: All tests must pass.

## DEPENDENCY_PHILOSOPHY
- **Bias toward fewer crates**: Don't add a crate for something achievable in <100 lines.
- **Justified crates**: `cpal` (audio capture), `wgpu`/`winit` (rendering), `serde`/`bincode` (serialization), `bytemuck` (buffer casting), `rustfft` (FFT analysis). These solve hard problems.
- **When to add a crate**: When it solves a genuinely hard problem (audio device abstraction, FFT, GPU rendering), not for convenience.
- **No `unsafe`** unless measured profiling shows a hot path that requires it (e.g., SIMD for FFT or particle updates).

## LOGGING
- Log **events and state transitions**, not per-sample data.
- `error`: Audio device failure, GPU errors. `warn`: Audio underruns, dropped analysis frames, buffer issues. `info`: Startup, audio device selection, entity lifecycle, config changes. `debug`: Beat detection events, onset events, periodic stats (FPS, entity count, audio latency). `trace`: Per-frame audio feature values, per-tick simulation state.
- Every new system and analysis stage must include appropriate logging.

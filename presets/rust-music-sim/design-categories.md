### Audio-to-Simulation Mapping
- Is the **mapping between audio features and simulation behavior** clearly defined? (which audio properties drive which simulation parameters?)
- Are mappings **visually coherent**? Does bass → gravity feel intuitive? Does tempo → orbital speed make sense?
- How are different **frequency bands** used? (sub-bass, bass, mids, highs, presence)
- What happens during **silence or quiet passages**? Does the universe go dormant, drift, decay?
- How do **transients and beats** differ from sustained tones? (impulse events vs. continuous modulation)

### Audio Analysis Pipeline
- What **audio features** are extracted? (RMS energy, spectral centroid, spectral flux, onset detection, beat tracking, pitch detection, chromagram, MFCCs)
- What's the **analysis window size** and hop size? Tradeoff between time resolution and frequency resolution
- How is **latency** handled? Analysis introduces delay — is the simulation behind the music or is there lookahead?
- Does the system handle **live audio input** (microphone/line-in), file playback, or both?
- How are raw audio features **smoothed and scaled** before they reach the simulation? (exponential smoothing, normalization, range mapping)

### Simulation Behaviors
- What **universe elements** exist? (stars, planets, particles, nebulae, black holes, galaxies)
- Which simulation properties are **music-driven** vs. **autonomous**? (gravity always runs, but spawning only happens on beats?)
- Are there **emergent behaviors** worth preserving? (orbital resonance, clustering, collisions) — how does music input interact with them?
- How does **time scale** work? Can the user slow down or speed up independent of the music?
- What's the **visual style**? Realistic astrophysics, abstract particle art, stylized cosmic, or configurable?

### User Experience
- What **audio sources** are supported? (system audio capture, microphone, file drag-and-drop, streaming APIs)
- Can the user **customize mappings** in real-time? (reassign which audio feature drives which simulation parameter)
- Are there **presets** for different music genres? (ambient, electronic, orchestral, hip-hop behave differently)
- **Recording/export** — can the user capture video of the reactive simulation?
- **Performance mode** — is this meant for live VJ use, personal listening visualization, or art installation?
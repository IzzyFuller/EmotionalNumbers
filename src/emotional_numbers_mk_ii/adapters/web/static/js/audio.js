/**
 * Audio Engine Module
 *
 * Provides ambient leitmotifs for number behaviors using Web Audio API.
 * Pure configuration functions are testable; actual audio playback
 * requires browser context.
 *
 * Tests: tests/js/audio.test.js
 */

// ============================================================================
// Leitmotif Patterns
// ============================================================================

/**
 * Frequency patterns for different leitmotif types.
 * Ratios are applied to baseFrequency.
 */
const PATTERNS = {
  ambient: {
    // Gentle fifth intervals for neutral, pleasant drone
    ratios: [1, 1.5, 2, 1.5],
    noteDuration: 2000,
    overlap: 0.8,
  },
};

// ============================================================================
// Leitmotif Factory
// ============================================================================

/**
 * Creates a leitmotif configuration.
 * @param {Object} config - Leitmotif configuration
 * @param {string} config.name - Leitmotif name
 * @param {number} config.baseFrequency - Base frequency in Hz
 * @param {string} config.pattern - Pattern name from PATTERNS
 * @returns {Object} Leitmotif object
 */
export function createLeitmotif(config = {}) {
  const name = config.name ?? 'default';
  const baseFrequency = config.baseFrequency ?? 220;
  const pattern = config.pattern ?? 'ambient';

  const patternConfig = PATTERNS[pattern] ?? PATTERNS.ambient;
  const frequencies = patternConfig.ratios.map((r) => baseFrequency * r);

  return {
    name,
    baseFrequency,
    pattern,
    frequencies,
    noteDuration: patternConfig.noteDuration,
    overlap: patternConfig.overlap,
  };
}

// ============================================================================
// Audio Engine Factory
// ============================================================================

/**
 * Creates an audio engine for playing leitmotifs.
 * Uses Web Audio API when available.
 * @returns {Object} Audio engine interface
 */
export function createAudioEngine() {
  let playing = false;
  let volume = 0.3;
  let audioContext = null;
  let oscillators = [];
  let gainNode = null;
  let currentLeitmotif = null;
  let intervalId = null;

  function initContext() {
    if (!audioContext && typeof AudioContext !== 'undefined') {
      audioContext = new AudioContext();
      gainNode = audioContext.createGain();
      gainNode.connect(audioContext.destination);
      gainNode.gain.value = volume;
    }
  }

  function playNote(frequency, duration) {
    if (!audioContext || !gainNode) return;

    const osc = audioContext.createOscillator();
    const noteGain = audioContext.createGain();

    osc.type = 'sine';
    osc.frequency.value = frequency;

    osc.connect(noteGain);
    noteGain.connect(gainNode);

    // Gentle envelope
    const now = audioContext.currentTime;
    noteGain.gain.setValueAtTime(0, now);
    noteGain.gain.linearRampToValueAtTime(0.5, now + 0.1);
    noteGain.gain.linearRampToValueAtTime(0, now + duration / 1000);

    osc.start(now);
    osc.stop(now + duration / 1000);

    oscillators.push(osc);
    osc.onended = () => {
      oscillators = oscillators.filter((o) => o !== osc);
    };
  }

  function startLeitmotif(leitmotif) {
    if (!leitmotif) return;
    currentLeitmotif = leitmotif;

    let noteIndex = 0;
    const playNext = () => {
      if (!playing || !currentLeitmotif) return;

      const freq = currentLeitmotif.frequencies[noteIndex];
      playNote(freq, currentLeitmotif.noteDuration);

      noteIndex = (noteIndex + 1) % currentLeitmotif.frequencies.length;
    };

    playNext();
    const interval = currentLeitmotif.noteDuration * currentLeitmotif.overlap;
    intervalId = setInterval(playNext, interval);
  }

  function stopLeitmotif() {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    oscillators.forEach((osc) => {
      try {
        osc.stop();
      } catch (e) {
        // Already stopped
      }
    });
    oscillators = [];
    currentLeitmotif = null;
  }

  return {
    start(leitmotif) {
      initContext();
      if (audioContext?.state === 'suspended') {
        audioContext.resume();
      }
      playing = true;
      startLeitmotif(leitmotif);
    },

    stop() {
      playing = false;
      stopLeitmotif();
    },

    setVolume(v) {
      volume = Math.max(0, Math.min(1, v));
      if (gainNode) {
        gainNode.gain.value = volume;
      }
    },

    isPlaying() {
      return playing;
    },
  };
}

/**
 * Audio Engine Module
 *
 * Provides ambient leitmotifs for number behaviors using Web Audio API.
 * Assumes AudioContext is available - caller should check before using.
 *
 * Tests: tests/js/audio.test.js
 */

// ============================================================================
// Leitmotif Patterns
// ============================================================================

const PATTERNS = {
  ambient: {
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
 */
export function createLeitmotif(config) {
  const { name, baseFrequency, pattern } = config;
  const patternConfig = PATTERNS[pattern];
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
 * Requires AudioContext to be available.
 */
export function createAudioEngine() {
  let playing = false;
  let volume = 0.3;
  const audioContext = new AudioContext();
  const gainNode = audioContext.createGain();
  gainNode.connect(audioContext.destination);
  gainNode.gain.value = volume;

  let oscillators = [];
  let currentLeitmotif = null;
  let intervalId = null;

  function playNote(frequency, duration) {
    const osc = audioContext.createOscillator();
    const noteGain = audioContext.createGain();

    osc.type = 'sine';
    osc.frequency.value = frequency;

    osc.connect(noteGain);
    noteGain.connect(gainNode);

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
      if (audioContext.state === 'suspended') {
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
      gainNode.gain.value = volume;
    },

    isPlaying() {
      return playing;
    },
  };
}

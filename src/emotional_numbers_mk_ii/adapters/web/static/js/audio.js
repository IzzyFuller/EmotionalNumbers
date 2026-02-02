/**
 * Audio Engine Module
 *
 * Provides ambient leitmotifs for number behaviors using Web Audio API.
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
// Tone Configurations - Each bucket has a distinct sound
// ============================================================================

export const TONE_CONFIGS = {
  tone_00: { baseFrequency: 220, pattern: 'ambient' },  // Default (non-region)
  tone_01: { baseFrequency: 165, pattern: 'ambient' },  // Low E - grounded, stable
  tone_02: { baseFrequency: 196, pattern: 'ambient' },  // G - warm, hopeful
  tone_03: { baseFrequency: 247, pattern: 'ambient' },  // B - tense, unsettled
  tone_04: { baseFrequency: 294, pattern: 'ambient' },  // D - bright, alert
  tone_05: { baseFrequency: 330, pattern: 'ambient' },  // E - high, ethereal
};

/**
 * Gets the tone configuration for a sound_id.
 * @param {string} soundId - The sound_id (e.g., "tone_01")
 * @returns {Object} Tone configuration with baseFrequency and pattern
 */
export function getToneConfig(soundId) {
  if (!soundId || !TONE_CONFIGS[soundId]) {
    return TONE_CONFIGS.tone_00;
  }
  return TONE_CONFIGS[soundId];
}

// ============================================================================
// Leitmotif Factory
// ============================================================================

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

const VOLUME = 0.3;

export function createAudioEngine(audioContext) {
  let playing = false;

  const gainNode = audioContext.createGain();
  gainNode.connect(audioContext.destination);
  gainNode.gain.value = VOLUME;

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
    oscillators.forEach((osc) => osc.stop());
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

    isPlaying() {
      return playing;
    },

    getCurrentLeitmotif() {
      return currentLeitmotif;
    },

    switchLeitmotif(leitmotif) {
      if (!playing) return;
      stopLeitmotif();
      playing = true;
      startLeitmotif(leitmotif);
    },
  };
}

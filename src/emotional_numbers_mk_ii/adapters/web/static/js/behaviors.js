/**
 * Number Behaviors Module
 *
 * Defines behaviors for numbers in the MDR terminal.
 * Each behavior has an associated CSS animation and audio leitmotif.
 *
 * Tests: tests/js/behaviors.test.js
 */

// ============================================================================
// Constants
// ============================================================================

export const DEFAULT_BEHAVIOR = 'jiggle_n_giggle';

// ============================================================================
// Behavior Definitions
// ============================================================================

const BEHAVIORS = {
  jiggle_n_giggle: {
    cssClass: 'jiggle',
    audio: {
      type: 'leitmotif',
      name: 'neutral',
      baseFrequency: 220,
      pattern: 'ambient',
    },
  },
};

// ============================================================================
// Behavior Accessors
// ============================================================================

/**
 * Gets the CSS class for a behavior.
 * @param {string} behavior - Behavior name
 * @returns {string} CSS class name, or empty string if unknown
 */
export function getBehaviorClass(behavior) {
  if (!behavior) return '';
  const config = BEHAVIORS[behavior];
  return config?.cssClass ?? '';
}

/**
 * Gets the audio configuration for a behavior.
 * @param {string} behavior - Behavior name
 * @returns {Object|null} Audio config object, or null if unknown
 */
export function getBehaviorAudioConfig(behavior) {
  if (!behavior) return null;
  const config = BEHAVIORS[behavior];
  return config?.audio ?? null;
}

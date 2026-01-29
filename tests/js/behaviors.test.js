import { describe, it, expect } from 'vitest';
import {
  DEFAULT_BEHAVIOR,
  getBehaviorClass,
  getBehaviorAudioConfig,
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/behaviors.js';

describe('DEFAULT_BEHAVIOR', () => {
  it('is jiggle_n_giggle', () => {
    expect(DEFAULT_BEHAVIOR).toBe('jiggle_n_giggle');
  });
});

describe('getBehaviorClass', () => {
  it('returns jiggle class for jiggle_n_giggle behavior', () => {
    const cssClass = getBehaviorClass('jiggle_n_giggle');

    expect(cssClass).toBe('jiggle');
  });

  it('returns empty string for unknown behavior', () => {
    const cssClass = getBehaviorClass('unknown_behavior');

    expect(cssClass).toBe('');
  });

  it('returns empty string for null/undefined', () => {
    expect(getBehaviorClass(null)).toBe('');
    expect(getBehaviorClass(undefined)).toBe('');
  });
});

describe('getBehaviorAudioConfig', () => {
  it('returns neutral leitmotif config for jiggle_n_giggle', () => {
    const config = getBehaviorAudioConfig('jiggle_n_giggle');

    expect(config).toEqual({
      type: 'leitmotif',
      name: 'neutral',
      baseFrequency: 220,
      pattern: 'ambient',
    });
  });

  it('returns null for unknown behavior', () => {
    const config = getBehaviorAudioConfig('unknown_behavior');

    expect(config).toBeNull();
  });

  it('returns null for null/undefined', () => {
    expect(getBehaviorAudioConfig(null)).toBeNull();
    expect(getBehaviorAudioConfig(undefined)).toBeNull();
  });
});

import { describe, it, expect } from 'vitest';
import {
  DEFAULT_BEHAVIOR,
  getBehaviorClass,
  getBehaviorAudioConfig,
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/behaviors.js';

describe('DEFAULT_BEHAVIOR', () => {
  it('exists and is a string', () => {
    expect(typeof DEFAULT_BEHAVIOR).toBe('string');
    expect(DEFAULT_BEHAVIOR.length).toBeGreaterThan(0);
  });
});

describe('getBehaviorClass', () => {
  it('returns a CSS class for the default behavior', () => {
    const cssClass = getBehaviorClass(DEFAULT_BEHAVIOR);

    expect(typeof cssClass).toBe('string');
    expect(cssClass.length).toBeGreaterThan(0);
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
  it('returns audio config for the default behavior', () => {
    const config = getBehaviorAudioConfig(DEFAULT_BEHAVIOR);

    expect(config).not.toBeNull();
    expect(typeof config).toBe('object');
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

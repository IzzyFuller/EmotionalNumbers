import { describe, it, expect } from 'vitest';
import {
  createAudioEngine,
  createLeitmotif,
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/audio.js';

describe('createAudioEngine', () => {
  it('returns an engine with start/stop/volume interface', () => {
    const engine = createAudioEngine();

    expect(typeof engine.start).toBe('function');
    expect(typeof engine.stop).toBe('function');
    expect(typeof engine.setVolume).toBe('function');
    expect(typeof engine.isPlaying).toBe('function');
  });

  it('starts in stopped state', () => {
    const engine = createAudioEngine();

    expect(engine.isPlaying()).toBe(false);
  });
});

describe('createLeitmotif', () => {
  it('produces frequencies from config', () => {
    const leitmotif = createLeitmotif({ baseFrequency: 440 });

    expect(Array.isArray(leitmotif.frequencies)).toBe(true);
    expect(leitmotif.frequencies.length).toBeGreaterThan(0);
    expect(leitmotif.frequencies.every((f) => typeof f === 'number')).toBe(true);
  });

  it('handles empty config gracefully', () => {
    const leitmotif = createLeitmotif({});

    expect(Array.isArray(leitmotif.frequencies)).toBe(true);
    expect(leitmotif.frequencies.length).toBeGreaterThan(0);
  });
});

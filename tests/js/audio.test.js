import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  createAudioEngine,
  createLeitmotif,
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/audio.js';

describe('createAudioEngine', () => {
  it('returns an audio engine object', () => {
    const engine = createAudioEngine();

    expect(engine).toBeDefined();
    expect(typeof engine.start).toBe('function');
    expect(typeof engine.stop).toBe('function');
    expect(typeof engine.setVolume).toBe('function');
  });

  it('starts in stopped state', () => {
    const engine = createAudioEngine();

    expect(engine.isPlaying()).toBe(false);
  });
});

describe('createLeitmotif', () => {
  it('creates a leitmotif configuration', () => {
    const config = {
      name: 'neutral',
      baseFrequency: 220,
      pattern: 'ambient',
    };

    const leitmotif = createLeitmotif(config);

    expect(leitmotif).toBeDefined();
    expect(leitmotif.name).toBe('neutral');
    expect(leitmotif.baseFrequency).toBe(220);
    expect(leitmotif.pattern).toBe('ambient');
  });

  it('provides default values for missing config', () => {
    const leitmotif = createLeitmotif({});

    expect(leitmotif.name).toBe('default');
    expect(leitmotif.baseFrequency).toBe(220);
    expect(leitmotif.pattern).toBe('ambient');
  });

  it('returns frequencies array for the pattern', () => {
    const leitmotif = createLeitmotif({
      baseFrequency: 220,
      pattern: 'ambient',
    });

    expect(Array.isArray(leitmotif.frequencies)).toBe(true);
    expect(leitmotif.frequencies.length).toBeGreaterThan(0);
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createLeitmotif, createAudioEngine } from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/audio.js';

describe('createLeitmotif', () => {
  it('produces frequencies from config', () => {
    const leitmotif = createLeitmotif({ baseFrequency: 440, pattern: 'ambient' });

    expect(Array.isArray(leitmotif.frequencies)).toBe(true);
    expect(leitmotif.frequencies.length).toBeGreaterThan(0);
    expect(leitmotif.frequencies.every((f) => typeof f === 'number')).toBe(true);
  });
});

describe('createAudioEngine', () => {
  function createFakeAudioContext() {
    return {
      currentTime: 0,
      state: 'running',
      destination: {},
      resume: vi.fn(),
      createGain: () => ({
        connect: vi.fn(),
        gain: { value: 0, setValueAtTime: vi.fn(), linearRampToValueAtTime: vi.fn() },
      }),
      createOscillator: () => ({
        connect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn(),
        type: 'sine',
        frequency: { value: 0 },
        onended: null,
      }),
    };
  }

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts in stopped state', () => {
    const engine = createAudioEngine(createFakeAudioContext());

    expect(engine.isPlaying()).toBe(false);
  });

  it('isPlaying returns true after start', () => {
    const engine = createAudioEngine(createFakeAudioContext());
    const leitmotif = createLeitmotif({ baseFrequency: 220, pattern: 'ambient' });

    engine.start(leitmotif);

    expect(engine.isPlaying()).toBe(true);
  });

  it('isPlaying returns false after stop', () => {
    const engine = createAudioEngine(createFakeAudioContext());
    const leitmotif = createLeitmotif({ baseFrequency: 220, pattern: 'ambient' });

    engine.start(leitmotif);
    engine.stop();

    expect(engine.isPlaying()).toBe(false);
  });

  it('resumes suspended audio context on start', () => {
    const ctx = createFakeAudioContext();
    ctx.state = 'suspended';
    const engine = createAudioEngine(ctx);
    const leitmotif = createLeitmotif({ baseFrequency: 220, pattern: 'ambient' });

    engine.start(leitmotif);

    expect(ctx.resume).toHaveBeenCalled();
  });
});

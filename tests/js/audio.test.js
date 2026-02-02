import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createLeitmotif, createAudioEngine, getToneConfig, TONE_CONFIGS } from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/audio.js';

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

  it('switches to new leitmotif while playing', () => {
    const engine = createAudioEngine(createFakeAudioContext());
    const leitmotif1 = createLeitmotif({ baseFrequency: 220, pattern: 'ambient' });
    const leitmotif2 = createLeitmotif({ baseFrequency: 330, pattern: 'ambient' });

    engine.start(leitmotif1);
    engine.switchLeitmotif(leitmotif2);

    expect(engine.isPlaying()).toBe(true);
    expect(engine.getCurrentLeitmotif()).toBe(leitmotif2);
  });

  it('getCurrentLeitmotif returns current leitmotif', () => {
    const engine = createAudioEngine(createFakeAudioContext());
    const leitmotif = createLeitmotif({ baseFrequency: 220, pattern: 'ambient' });

    engine.start(leitmotif);

    expect(engine.getCurrentLeitmotif()).toBe(leitmotif);
  });

  it('getCurrentLeitmotif returns null when stopped', () => {
    const engine = createAudioEngine(createFakeAudioContext());

    expect(engine.getCurrentLeitmotif()).toBe(null);
  });
});

describe('TONE_CONFIGS', () => {
  it('has configs for tone_00 through tone_05', () => {
    expect(TONE_CONFIGS).toHaveProperty('tone_00');
    expect(TONE_CONFIGS).toHaveProperty('tone_01');
    expect(TONE_CONFIGS).toHaveProperty('tone_02');
    expect(TONE_CONFIGS).toHaveProperty('tone_03');
    expect(TONE_CONFIGS).toHaveProperty('tone_04');
    expect(TONE_CONFIGS).toHaveProperty('tone_05');
  });

  it('each tone has a different base frequency', () => {
    const frequencies = Object.values(TONE_CONFIGS).map((c) => c.baseFrequency);
    const uniqueFrequencies = new Set(frequencies);

    expect(uniqueFrequencies.size).toBe(frequencies.length);
  });

  it('each tone has required properties', () => {
    for (const [name, config] of Object.entries(TONE_CONFIGS)) {
      expect(config).toHaveProperty('baseFrequency');
      expect(config).toHaveProperty('pattern');
      expect(typeof config.baseFrequency).toBe('number');
      expect(typeof config.pattern).toBe('string');
    }
  });
});

describe('getToneConfig', () => {
  it('returns config for valid tone_id', () => {
    const config = getToneConfig('tone_01');

    expect(config).toBe(TONE_CONFIGS.tone_01);
  });

  it('returns tone_00 config for unknown tone_id', () => {
    const config = getToneConfig('unknown');

    expect(config).toBe(TONE_CONFIGS.tone_00);
  });

  it('returns tone_00 config for null', () => {
    const config = getToneConfig(null);

    expect(config).toBe(TONE_CONFIGS.tone_00);
  });

  it('returns tone_00 config for undefined', () => {
    const config = getToneConfig(undefined);

    expect(config).toBe(TONE_CONFIGS.tone_00);
  });
});

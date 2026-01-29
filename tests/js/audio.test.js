import { describe, it, expect } from 'vitest';
import { createLeitmotif } from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/audio.js';

// createAudioEngine requires AudioContext (browser-only)
// It will crash in Node, which is correct - caller must check for AudioContext

describe('createLeitmotif', () => {
  it('produces frequencies from config', () => {
    const leitmotif = createLeitmotif({ baseFrequency: 440, pattern: 'ambient' });

    expect(Array.isArray(leitmotif.frequencies)).toBe(true);
    expect(leitmotif.frequencies.length).toBeGreaterThan(0);
    expect(leitmotif.frequencies.every((f) => typeof f === 'number')).toBe(true);
  });
});

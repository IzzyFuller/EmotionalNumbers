import { describe, it, expect, beforeEach } from 'vitest';
import {
  generateGrid,
  createInitialGameState,
  classifySurroundedToBin,
  calculateProgress,
  toggleCellSelection,
  clearSelection,
  formatHexCoord,
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/terminal.js';

describe('generateGrid', () => {
  it('creates a grid with specified dimensions', () => {
    const grid = generateGrid(10, 15);

    expect(grid).toHaveLength(10);
    expect(grid[0]).toHaveLength(15);
  });

  it('creates cells with correct coordinates', () => {
    const grid = generateGrid(3, 4);

    expect(grid[0][0]).toMatchObject({ x: 0, y: 0 });
    expect(grid[2][3]).toMatchObject({ x: 3, y: 2 });
  });

  it('creates cells with values between 0 and 9', () => {
    const grid = generateGrid(5, 5);

    for (const row of grid) {
      for (const cell of row) {
        expect(cell.value).toBeGreaterThanOrEqual(0);
        expect(cell.value).toBeLessThanOrEqual(9);
      }
    }
  });

  it('creates cells with default state (not selected, not classified)', () => {
    const grid = generateGrid(2, 2);

    for (const row of grid) {
      for (const cell of row) {
        expect(cell.selected).toBe(false);
        expect(cell.classified).toBe(false);
        expect(cell.size).toBe(1);
      }
    }
  });

  it('uses default dimensions when none provided', () => {
    const grid = generateGrid();

    expect(grid).toHaveLength(25);
    expect(grid[0]).toHaveLength(40);
  });
});

describe('createInitialGameState', () => {
  it('creates game state with empty bins', () => {
    const state = createInitialGameState();

    expect(state.bins).toEqual({
      '01': 0,
      '02': 0,
      '03': 0,
      '04': 0,
      '05': 0,
    });
  });

  it('creates game state with zero progress', () => {
    const state = createInitialGameState();

    expect(state.progress).toBe(0);
  });

  it('creates game state with a grid', () => {
    const state = createInitialGameState(5, 5);

    expect(state.grid).toHaveLength(5);
    expect(state.grid[0]).toHaveLength(5);
  });
});

describe('toggleCellSelection', () => {
  let gameState;

  beforeEach(() => {
    gameState = createInitialGameState(3, 3);
  });

  it('selects an unselected cell', () => {
    const result = toggleCellSelection(gameState, 1, 1);

    expect(result.grid[1][1].selected).toBe(true);
  });

  it('deselects a selected cell', () => {
    gameState.grid[1][1].selected = true;

    const result = toggleCellSelection(gameState, 1, 1);

    expect(result.grid[1][1].selected).toBe(false);
  });

  it('does not modify classified cells', () => {
    gameState.grid[1][1].classified = true;

    const result = toggleCellSelection(gameState, 1, 1);

    expect(result.grid[1][1].selected).toBe(false);
  });

  it('increases size when selecting', () => {
    const result = toggleCellSelection(gameState, 1, 1);

    expect(result.grid[1][1].size).toBeGreaterThan(1);
  });

  it('resets size when deselecting', () => {
    gameState.grid[1][1].selected = true;
    gameState.grid[1][1].size = 3;

    const result = toggleCellSelection(gameState, 1, 1);

    expect(result.grid[1][1].size).toBe(1);
  });

  it('returns a new state object (immutability)', () => {
    const result = toggleCellSelection(gameState, 1, 1);

    expect(result).not.toBe(gameState);
  });
});

describe('clearSelection', () => {
  it('clears all selected cells', () => {
    const gameState = createInitialGameState(3, 3);
    gameState.grid[0][0].selected = true;
    gameState.grid[1][1].selected = true;
    gameState.grid[2][2].selected = true;

    const result = clearSelection(gameState);

    for (const row of result.grid) {
      for (const cell of row) {
        expect(cell.selected).toBe(false);
      }
    }
  });

  it('resets all sizes to 1', () => {
    const gameState = createInitialGameState(3, 3);
    gameState.grid[0][0].size = 2;
    gameState.grid[1][1].size = 3;

    const result = clearSelection(gameState);

    for (const row of result.grid) {
      for (const cell of row) {
        expect(cell.size).toBe(1);
      }
    }
  });

  it('does not affect classified cells', () => {
    const gameState = createInitialGameState(3, 3);
    gameState.grid[0][0].classified = true;

    const result = clearSelection(gameState);

    expect(result.grid[0][0].classified).toBe(true);
  });
});

describe('classifySurroundedToBin (Go-style capture)', () => {
  let gameState;

  beforeEach(() => {
    gameState = createInitialGameState(5, 5);
  });

  it('classifies a cell surrounded on all 4 sides (N/S/E/W)', () => {
    // Create a cross of selected cells around center (2,2)
    //     S
    //   S . S
    //     S
    gameState.grid[1][2].selected = true; // North
    gameState.grid[3][2].selected = true; // South
    gameState.grid[2][1].selected = true; // West
    gameState.grid[2][3].selected = true; // East

    const result = classifySurroundedToBin(gameState, '01');

    expect(result.grid[2][2].classified).toBe(true);
    expect(result.classifiedCount).toBe(1);
  });

  it('does NOT classify cells on the edge (they touch boundary)', () => {
    // Try to surround corner cell (0,0) - impossible since it's on edge
    gameState.grid[0][1].selected = true;
    gameState.grid[1][0].selected = true;

    const result = classifySurroundedToBin(gameState, '01');

    expect(result.grid[0][0].classified).toBe(false);
    expect(result.classifiedCount).toBe(0);
  });

  it('does NOT classify when diagonal opening exists (Go rules)', () => {
    // Diagonal opening should allow escape
    //   S .
    //   . S
    // Cell at (1,1) has diagonal opening to edge
    gameState.grid[0][1].selected = true;
    gameState.grid[1][2].selected = true;
    gameState.grid[2][1].selected = true;
    // Missing (1,0) - but diagonal to (0,0) doesn't close it

    const result = classifySurroundedToBin(gameState, '01');

    // (1,1) can escape via (1,0) -> edge
    expect(result.grid[1][1].classified).toBe(false);
  });

  it('classifies multiple cells in a surrounded region together', () => {
    // Create a 2x2 surrounded region in center of 5x5
    // Surround cells (2,2) and (2,3) and (3,2) and (3,3)
    // Wall around them:
    gameState.grid[1][2].selected = true;
    gameState.grid[1][3].selected = true;
    gameState.grid[2][1].selected = true;
    gameState.grid[2][4].selected = true;
    gameState.grid[3][1].selected = true;
    gameState.grid[3][4].selected = true;
    gameState.grid[4][2].selected = true;
    gameState.grid[4][3].selected = true;

    const result = classifySurroundedToBin(gameState, '02');

    expect(result.grid[2][2].classified).toBe(true);
    expect(result.grid[2][3].classified).toBe(true);
    expect(result.grid[3][2].classified).toBe(true);
    expect(result.grid[3][3].classified).toBe(true);
    expect(result.classifiedCount).toBe(4);
  });

  it('does NOT classify the wall cells themselves', () => {
    gameState.grid[1][2].selected = true;
    gameState.grid[3][2].selected = true;
    gameState.grid[2][1].selected = true;
    gameState.grid[2][3].selected = true;

    const result = classifySurroundedToBin(gameState, '01');

    // Wall cells should not be classified
    expect(result.grid[1][2].classified).toBe(false);
    expect(result.grid[3][2].classified).toBe(false);
    expect(result.grid[2][1].classified).toBe(false);
    expect(result.grid[2][3].classified).toBe(false);
  });

  it('clears selection after classification', () => {
    gameState.grid[1][2].selected = true;
    gameState.grid[3][2].selected = true;
    gameState.grid[2][1].selected = true;
    gameState.grid[2][3].selected = true;

    const result = classifySurroundedToBin(gameState, '01');

    expect(result.grid[1][2].selected).toBe(false);
    expect(result.grid[2][2].selected).toBe(false);
  });

  it('increments bin count by number of surrounded cells', () => {
    gameState.grid[1][2].selected = true;
    gameState.grid[3][2].selected = true;
    gameState.grid[2][1].selected = true;
    gameState.grid[2][3].selected = true;

    const result = classifySurroundedToBin(gameState, '03');

    expect(result.bins['03']).toBe(1); // Only center cell
  });

  it('returns zero when no cells are surrounded', () => {
    // Just select some cells but don't surround anything
    gameState.grid[0][0].selected = true;
    gameState.grid[4][4].selected = true;

    const result = classifySurroundedToBin(gameState, '01');

    expect(result.classifiedCount).toBe(0);
  });

  it('does not re-classify already classified cells', () => {
    gameState.grid[2][2].classified = true; // Already classified
    gameState.grid[1][2].selected = true;
    gameState.grid[3][2].selected = true;
    gameState.grid[2][1].selected = true;
    gameState.grid[2][3].selected = true;

    const result = classifySurroundedToBin(gameState, '01');

    expect(result.classifiedCount).toBe(0);
  });
});

describe('calculateProgress', () => {
  it('returns 0 when no cells are classified', () => {
    const gameState = createInitialGameState(5, 5);

    const progress = calculateProgress(gameState);

    expect(progress).toBe(0);
  });

  it('returns 100 when all cells are classified', () => {
    const gameState = createInitialGameState(2, 2);
    for (const row of gameState.grid) {
      for (const cell of row) {
        cell.classified = true;
      }
    }

    const progress = calculateProgress(gameState);

    expect(progress).toBe(100);
  });

  it('returns correct percentage for partial classification', () => {
    const gameState = createInitialGameState(2, 2); // 4 cells
    gameState.grid[0][0].classified = true; // 1 of 4 = 25%

    const progress = calculateProgress(gameState);

    expect(progress).toBe(25);
  });

  it('rounds to nearest integer', () => {
    const gameState = createInitialGameState(3, 3); // 9 cells
    gameState.grid[0][0].classified = true; // 1 of 9 = 11.11%

    const progress = calculateProgress(gameState);

    expect(progress).toBe(11);
  });
});

describe('formatHexCoord', () => {
  it('formats coordinates as hex strings', () => {
    const result = formatHexCoord(0, 0);

    expect(result.hexX).toMatch(/^0x[0-9A-F]+$/);
    expect(result.hexY).toMatch(/^0x[0-9A-F]+$/);
  });

  it('produces different values for different coordinates', () => {
    const result1 = formatHexCoord(0, 0);
    const result2 = formatHexCoord(5, 10);

    expect(result1.hexX).not.toBe(result2.hexX);
    expect(result1.hexY).not.toBe(result2.hexY);
  });

  it('produces consistent values for same coordinates', () => {
    const result1 = formatHexCoord(3, 7);
    const result2 = formatHexCoord(3, 7);

    expect(result1.hexX).toBe(result2.hexX);
    expect(result1.hexY).toBe(result2.hexY);
  });
});

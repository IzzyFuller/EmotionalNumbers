/**
 * MDR Terminal Game Logic
 *
 * Functions for game state management.
 *
 * Tests: tests/js/terminal.test.js
 */

// ============================================================================
// Constants
// ============================================================================

const HEX_OFFSET_X = 0xfff00000;
const HEX_OFFSET_Y = 0xfffa0000;
const HEX_MULTIPLIER = 0x1000;

// ============================================================================
// Cell Factory
// ============================================================================

/**
 * Creates a single cell with default state.
 * @param {number} x - Column position
 * @param {number} y - Row position
 * @returns {Object} Cell object
 */
function createCell(x, y) {
  return {
    x,
    y,
    value: Math.floor(Math.random() * 10),
    selected: false,
    classified: false,
    size: 1,
  };
}

// ============================================================================
// Grid Generation
// ============================================================================

/**
 * Generates a grid of cells with random values.
 * @param {number} rows - Number of rows (default 25)
 * @param {number} cols - Number of columns (default 40)
 * @returns {Array<Array<Object>>} 2D array of cells
 */
export function generateGrid(rows = 25, cols = 40) {
  const grid = [];

  for (let y = 0; y < rows; y++) {
    const row = [];
    for (let x = 0; x < cols; x++) {
      row.push(createCell(x, y));
    }
    grid.push(row);
  }

  return grid;
}

// ============================================================================
// Game State Factory
// ============================================================================

/**
 * Creates initial game state with all defaults.
 * @param {number} rows - Grid rows (default 25)
 * @param {number} cols - Grid columns (default 40)
 * @returns {Object} Initial game state
 */
export function createInitialGameState(rows = 25, cols = 40) {
  return {
    grid: generateGrid(rows, cols),
    bins: {
      '01': 0,
      '02': 0,
      '03': 0,
      '04': 0,
      '05': 0,
    },
    progress: 0,
  };
}

// ============================================================================
// Cell Selection
// ============================================================================

/**
 * Toggles selection state of a cell at given coordinates.
 *
 * @param {Object} gameState - Current game state
 * @param {number} x - Column position
 * @param {number} y - Row position
 * @returns {Object} Game state with toggled cell
 */
export function toggleCellSelection(gameState, x, y) {
  const cell = gameState.grid[y][x];

  if (cell.classified) {
    return gameState;
  }

  cell.selected = !cell.selected;
  cell.size = cell.selected ? 2 + Math.floor(Math.random() * 2) : 1;

  return gameState;
}

/**
 * Clears all cell selections and resets sizes.
 *
 * @param {Object} gameState - Current game state
 * @returns {Object} Game state with cleared selections
 */
export function clearSelection(gameState) {
  for (const row of gameState.grid) {
    for (const cell of row) {
      cell.selected = false;
      cell.size = 1;
    }
  }

  return gameState;
}

// ============================================================================
// Classification (Go-style capture)
// ============================================================================

/**
 * Finds all cells that can reach the grid edge without crossing selected cells.
 * Uses flood-fill from edges, only moving N/S/E/W (no diagonals).
 *
 * @param {Array<Array<Object>>} grid - The game grid
 * @returns {Set<string>} Set of "x,y" coordinates that can reach edge
 */
function findCellsReachingEdge(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  const canReachEdge = new Set();
  const visited = new Set();

  function floodFill(x, y) {
    const key = `${x},${y}`;
    if (visited.has(key)) return;
    if (x < 0 || x >= cols || y < 0 || y >= rows) return;

    const cell = grid[y][x];
    if (cell.selected) return; // Wall - can't pass through

    visited.add(key);
    canReachEdge.add(key);

    // Only N/S/E/W - no diagonals (Go rules)
    floodFill(x, y - 1); // North
    floodFill(x, y + 1); // South
    floodFill(x - 1, y); // West
    floodFill(x + 1, y); // East
  }

  // Start flood fill from all edge cells
  for (let x = 0; x < cols; x++) {
    floodFill(x, 0); // Top edge
    floodFill(x, rows - 1); // Bottom edge
  }
  for (let y = 0; y < rows; y++) {
    floodFill(0, y); // Left edge
    floodFill(cols - 1, y); // Right edge
  }

  return canReachEdge;
}

/**
 * Classifies cells that are surrounded by selected cells (Go-style capture).
 * A cell is surrounded if it cannot reach the grid edge via N/S/E/W
 * without crossing a selected cell.
 *
 * The selected cells form the "wall" - they are NOT classified themselves.
 * Only the trapped cells inside are classified.
 *
 * @param {Object} gameState - Current game state
 * @param {string} bin - Bin identifier ('01' through '05')
 * @returns {Object} Game state with classifiedCount property
 */
export function classifySurroundedToBin(gameState, bin) {
  const canReachEdge = findCellsReachingEdge(gameState.grid);
  let classifiedCount = 0;

  for (const row of gameState.grid) {
    for (const cell of row) {
      const key = `${cell.x},${cell.y}`;

      // Classify if: can't reach edge, not selected (wall), not already classified
      if (!canReachEdge.has(key) && !cell.selected && !cell.classified) {
        cell.classified = true;
        classifiedCount++;
      }

      // Clear all selections
      cell.selected = false;
    }
  }

  gameState.bins[bin] += classifiedCount;
  gameState.classifiedCount = classifiedCount;

  return gameState;
}

// ============================================================================
// Progress Calculation
// ============================================================================

/**
 * Calculates completion percentage based on classified cells.
 *
 * @param {Object} gameState - Current game state
 * @returns {number} Progress percentage (0-100, rounded)
 */
export function calculateProgress(gameState) {
  let total = 0;
  let classified = 0;

  for (const row of gameState.grid) {
    for (const cell of row) {
      total++;
      if (cell.classified) {
        classified++;
      }
    }
  }

  if (total === 0) {
    return 0;
  }

  return Math.round((classified / total) * 100);
}

// ============================================================================
// Display Formatting
// ============================================================================

/**
 * Formats grid coordinates as hex strings for display.
 *
 * @param {number} x - Column position
 * @param {number} y - Row position
 * @returns {Object} Formatted hex strings { hexX, hexY }
 */
export function formatHexCoord(x, y) {
  const hexX = '0x' + (x * HEX_MULTIPLIER + HEX_OFFSET_X).toString(16).toUpperCase();
  const hexY = '0x' + (y * HEX_MULTIPLIER + HEX_OFFSET_Y).toString(16).toUpperCase();

  return { hexX, hexY };
}

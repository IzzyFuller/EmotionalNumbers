/**
 * MDR Terminal - DOM Integration
 *
 * Wires the pure game logic (terminal.js) to the browser DOM.
 * This layer handles rendering, event listeners, and user interaction.
 */

import {
  createInitialGameState,
  toggleCellSelection,
  clearSelection,
  classifySurroundedToBin,
  calculateProgress,
  formatHexCoord,
} from './terminal.js';

// ============================================================================
// Application State
// ============================================================================

let gameState = createInitialGameState();

// ============================================================================
// DOM References
// ============================================================================

const gridEl = document.getElementById('grid');
const progressEl = document.getElementById('progress-percent');
const hexXEl = document.getElementById('hex-x');
const hexYEl = document.getElementById('hex-y');
const messageArea = document.getElementById('message-area');

// ============================================================================
// Rendering
// ============================================================================

function render() {
  const cols = gameState.grid[0]?.length || 40;
  gridEl.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

  let html = '';
  for (const row of gameState.grid) {
    for (const cell of row) {
      const classes = ['cell'];
      if (cell.selected) classes.push('selected');
      if (cell.classified) classes.push('classified');
      if (cell.size === 2) classes.push('size-medium');
      if (cell.size === 3) classes.push('size-large');

      html += `<div class="${classes.join(' ')}" data-x="${cell.x}" data-y="${cell.y}">${cell.value}</div>`;
    }
  }
  gridEl.innerHTML = html;

  updateProgressDisplay();
  updateBinDisplays();
}

function updateProgressDisplay() {
  const progress = calculateProgress(gameState);
  gameState.progress = progress;
  progressEl.textContent = progress;
}

function updateBinDisplays() {
  const maxPerBin = 20;
  for (const [bin, count] of Object.entries(gameState.bins)) {
    const fill = document.getElementById(`bin-${bin}-fill`);
    if (fill) {
      const percent = Math.min((count / maxPerBin) * 100, 100);
      fill.style.width = `${percent}%`;
    }
  }
}

function updateHexDisplay(x, y) {
  const { hexX, hexY } = formatHexCoord(x, y);
  hexXEl.textContent = hexX;
  hexYEl.textContent = hexY;
}

function showMessage(text, type = 'info') {
  messageArea.innerHTML = `<div class="message ${type}">${text}</div>`;
  setTimeout(() => {
    messageArea.innerHTML = '';
  }, 3000);
}

// ============================================================================
// Event Handlers - Cell Interaction
// ============================================================================

gridEl.addEventListener('mouseover', (e) => {
  const cell = e.target.closest('.cell');
  if (cell && !cell.classList.contains('classified')) {
    const x = parseInt(cell.dataset.x);
    const y = parseInt(cell.dataset.y);
    updateHexDisplay(x, y);
  }
});

document.addEventListener('click', (e) => {
  // Cell click - toggle selection
  if (e.target.classList.contains('cell') && !e.target.classList.contains('classified')) {
    const x = parseInt(e.target.dataset.x);
    const y = parseInt(e.target.dataset.y);

    gameState = toggleCellSelection(gameState, x, y);
    render();
  }

  // Bin click - classify selected
  const bin = e.target.closest('.bin');
  if (bin) {
    const binId = bin.dataset.bin;
    const result = classifySurroundedToBin(gameState, binId);
    gameState = result;

    if (result.classifiedCount > 0) {
      showMessage(`${result.classifiedCount} numbers refined to bin ${binId}`, 'success');
    }
    render();
  }
});

// ============================================================================
// Event Handlers - Keyboard
// ============================================================================

document.addEventListener('keydown', (e) => {
  // Number keys 1-5 classify to bins
  if (e.key >= '1' && e.key <= '5') {
    const binId = '0' + e.key;
    const result = classifySurroundedToBin(gameState, binId);
    gameState = result;

    if (result.classifiedCount > 0) {
      showMessage(`${result.classifiedCount} numbers refined to bin ${binId}`, 'success');
    }
    render();
  }

  // C clears selection
  if (e.key === 'c' || e.key === 'C') {
    gameState = clearSelection(gameState);
    render();
  }
});

// ============================================================================
// Initialize
// ============================================================================

render();
console.log('MDR Terminal initialized');

/**
 * MDR Terminal - DOM Integration
 *
 * Wires the pure game logic to the browser DOM.
 * Manages screen transitions: Welcome → Onboarding → Game
 */

import {
  createInitialGameState,
  toggleCellSelection,
  clearSelection,
  classifySurroundedToBin,
  calculateProgress,
  formatHexCoord,
} from './terminal.js';

import {
  createOnboardingState,
  getCurrentQuestion,
  submitAnswer,
  isComplete,
  getAnswers,
  getProgress,
} from './onboarding.js';

import { selectQuestions } from './questions.js';
import { DEFAULT_BEHAVIOR, getBehaviorClass, getBehaviorAudioConfig } from './behaviors.js';
import { createAudioEngine, createLeitmotif } from './audio.js';

// ============================================================================
// Application State
// ============================================================================

const AppScreen = {
  WELCOME: 'welcome',
  ONBOARDING: 'onboarding',
  GAME: 'game',
};

let currentScreen = AppScreen.WELCOME;
let onboardingState = null;
let gameState = null;
let audioEngine = null;

// ============================================================================
// DOM References - Screens
// ============================================================================

const welcomeScreen = document.getElementById('welcome-screen');
const onboardingScreen = document.getElementById('onboarding-screen');
const gameScreen = document.getElementById('game-screen');

// DOM References - Welcome
const beginBtn = document.getElementById('begin-btn');

// DOM References - Onboarding
const qCurrentEl = document.getElementById('q-current');
const qTotalEl = document.getElementById('q-total');
const questionTextEl = document.getElementById('question-text');
const questionHintEl = document.getElementById('question-hint');
const answerInput = document.getElementById('answer-input');
const submitBtn = document.getElementById('submit-btn');
const onboardingProgressEl = document.getElementById('onboarding-progress');

// DOM References - Game
const gridEl = document.getElementById('grid');
const progressEl = document.getElementById('progress-percent');
const hexXEl = document.getElementById('hex-x');
const hexYEl = document.getElementById('hex-y');
const messageArea = document.getElementById('message-area');

// ============================================================================
// Screen Management
// ============================================================================

function showScreen(screen) {
  currentScreen = screen;

  welcomeScreen.style.display = screen === AppScreen.WELCOME ? 'flex' : 'none';
  onboardingScreen.style.display = screen === AppScreen.ONBOARDING ? 'flex' : 'none';
  gameScreen.style.display = screen === AppScreen.GAME ? 'flex' : 'none';
}

// ============================================================================
// Welcome Screen
// ============================================================================

function handleBeginOrientation() {
  const questions = selectQuestions(5);
  onboardingState = createOnboardingState(questions);
  showScreen(AppScreen.ONBOARDING);
  renderOnboarding();
  answerInput.focus();
}

// ============================================================================
// Onboarding Screen
// ============================================================================

function renderOnboarding() {
  const question = getCurrentQuestion(onboardingState);
  const progress = getProgress(onboardingState);

  qCurrentEl.textContent = progress.current + 1;
  qTotalEl.textContent = progress.total;

  if (question) {
    questionTextEl.textContent = question.text;

    // Set hint based on answer type
    let hint = 'Enter your response';
    if (question.answerType === 'number') hint = 'Enter a number';
    if (question.answerType === 'scale') hint = 'Enter a number from 1 to 10';
    questionHintEl.textContent = `[${hint}]`;
  }

  // Update progress bar
  const percent = progress.total > 0
    ? (progress.current / progress.total) * 100
    : 0;
  onboardingProgressEl.style.width = `${percent}%`;
}

function handleSubmitAnswer() {
  const answer = answerInput.value.trim();
  if (!answer) return;

  onboardingState = submitAnswer(onboardingState, answer);
  answerInput.value = '';

  if (isComplete(onboardingState)) {
    // Transition to game with collected answers
    const answers = getAnswers(onboardingState);
    console.log('Onboarding complete. Answers:', answers);
    startGame(answers);
  } else {
    renderOnboarding();
    answerInput.focus();
  }
}

// ============================================================================
// Game Screen
// ============================================================================

function startGame(answers) {
  // TODO: Use answers to seed puzzle generation
  console.log('Starting game with seed answers:', answers);
  gameState = createInitialGameState();
  showScreen(AppScreen.GAME);
  renderGame();

  // Start the default behavior's leitmotif
  const audioConfig = getBehaviorAudioConfig(DEFAULT_BEHAVIOR);
  if (audioConfig) {
    audioEngine = createAudioEngine();
    const leitmotif = createLeitmotif(audioConfig);
    audioEngine.start(leitmotif);
  }
}

function renderGame() {
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

      // Apply default behavior animation to unclassified cells
      let style = '';
      if (!cell.classified) {
        const behaviorClass = getBehaviorClass(DEFAULT_BEHAVIOR);
        if (behaviorClass) {
          classes.push(behaviorClass);
          // Random delay so they don't jiggle in unison
          const delay = (Math.random() * 0.8).toFixed(2);
          style = `animation-delay: ${delay}s;`;
        }
      }

      html += `<div class="${classes.join(' ')}" style="${style}" data-x="${cell.x}" data-y="${cell.y}">${cell.value}</div>`;
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
// Event Handlers - Welcome Screen
// ============================================================================

beginBtn.addEventListener('click', handleBeginOrientation);

// ============================================================================
// Event Handlers - Onboarding Screen
// ============================================================================

submitBtn.addEventListener('click', handleSubmitAnswer);

answerInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && currentScreen === AppScreen.ONBOARDING) {
    e.preventDefault();
    handleSubmitAnswer();
  }
});

// ============================================================================
// Event Handlers - Game Screen (Cell Interaction)
// ============================================================================

gridEl.addEventListener('mouseover', (e) => {
  if (currentScreen !== AppScreen.GAME) return;

  const cell = e.target.closest('.cell');
  if (cell && !cell.classList.contains('classified')) {
    const x = parseInt(cell.dataset.x);
    const y = parseInt(cell.dataset.y);
    updateHexDisplay(x, y);
  }
});

document.addEventListener('click', (e) => {
  if (currentScreen !== AppScreen.GAME) return;

  // Cell click - toggle selection
  if (e.target.classList.contains('cell') && !e.target.classList.contains('classified')) {
    const x = parseInt(e.target.dataset.x);
    const y = parseInt(e.target.dataset.y);

    gameState = toggleCellSelection(gameState, x, y);
    renderGame();
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
    renderGame();
  }
});

// ============================================================================
// Event Handlers - Keyboard
// ============================================================================

document.addEventListener('keydown', (e) => {
  if (currentScreen !== AppScreen.GAME) return;

  // Don't intercept if typing in an input
  if (e.target.tagName === 'INPUT') return;

  // Number keys 1-5 classify to bins
  if (e.key >= '1' && e.key <= '5') {
    const binId = '0' + e.key;
    const result = classifySurroundedToBin(gameState, binId);
    gameState = result;

    if (result.classifiedCount > 0) {
      showMessage(`${result.classifiedCount} numbers refined to bin ${binId}`, 'success');
    }
    renderGame();
  }

  // C clears selection
  if (e.key === 'c' || e.key === 'C') {
    gameState = clearSelection(gameState);
    renderGame();
  }
});

// ============================================================================
// Initialize
// ============================================================================

showScreen(AppScreen.WELCOME);
console.log('MDR Terminal initialized');

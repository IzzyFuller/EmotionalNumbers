/**
 * MDR Terminal - DOM Integration
 *
 * Wires the Python API to the browser DOM.
 * Manages screen transitions: Welcome → Onboarding → Game
 */

import * as api from './api.js';
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
let questions = [];
let answers = [];
let currentQuestionIndex = 0;
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

async function handleBeginOrientation() {
  // Show loading state
  beginBtn.disabled = true;
  beginBtn.textContent = 'INITIALIZING...';

  const response = await api.startGame();
  questions = response.questions;
  answers = [];
  currentQuestionIndex = 0;

  // Restore button for next time
  beginBtn.disabled = false;
  beginBtn.textContent = 'BEGIN ORIENTATION';

  showScreen(AppScreen.ONBOARDING);
  renderOnboarding();
  answerInput.focus();
}

// ============================================================================
// Onboarding Screen
// ============================================================================

function renderOnboarding() {
  const question = questions[currentQuestionIndex];

  qCurrentEl.textContent = currentQuestionIndex + 1;
  qTotalEl.textContent = questions.length;

  if (question) {
    questionTextEl.textContent = question.text;
    questionHintEl.textContent = '[Enter your response]';
  }

  const percent = questions.length > 0
    ? (currentQuestionIndex / questions.length) * 100
    : 0;
  onboardingProgressEl.style.width = `${percent}%`;
}

async function handleSubmitAnswer() {
  const answer = answerInput.value.trim();
  if (!answer) return;

  const question = questions[currentQuestionIndex];
  answers.push({ questionId: question.id, answer });
  answerInput.value = '';
  currentQuestionIndex++;

  if (currentQuestionIndex >= questions.length) {
    // Show loading state while LLM generates rules
    questionTextEl.textContent = 'CALIBRATING EXPERIENCE...';
    questionHintEl.textContent = '[Please wait while your data file is prepared]';
    submitBtn.disabled = true;
    answerInput.disabled = true;
    onboardingProgressEl.style.width = '100%';

    // Submit to API and start game
    const response = await api.submitAnswers(answers);
    gameState = {
      grid: response.grid,
      bins: { '01': 0, '02': 0, '03': 0, '04': 0, '05': 0 },
      progress: 0,
    };

    // Start audio first, then show grid after brief delay
    startAudio();
    await new Promise(resolve => setTimeout(resolve, 400));
    showScreen(AppScreen.GAME);
    renderGame();
  } else {
    renderOnboarding();
    answerInput.focus();
  }
}

// ============================================================================
// Game Screen
// ============================================================================

function startAudio() {
  if (typeof AudioContext !== 'undefined') {
    const audioConfig = {
      type: 'leitmotif',
      name: 'neutral',
      baseFrequency: 220,
      pattern: 'ambient',
    };
    const audioContext = new AudioContext();
    audioEngine = createAudioEngine(audioContext);
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

      let style = '';
      if (!cell.classified) {
        classes.push('jiggle');
        const delay = (Math.random() * 0.8).toFixed(2);
        // Region cells use their LLM-assigned behavior, non-region use defaults from API
        const scale = 1 + (cell.jiggle_intensity * 0.5); // 1.0 to 1.5
        const duration = (2.4 / cell.jiggle_frequency).toFixed(2); // Higher freq = faster
        style = `animation-delay: ${delay}s; --jiggle-scale: ${scale}; --jiggle-duration: ${duration}s;`;
      }

      html += `<div class="${classes.join(' ')}" style="${style}" data-x="${cell.x}" data-y="${cell.y}">${cell.value}</div>`;
    }
  }
  gridEl.innerHTML = html;

  progressEl.textContent = gameState.progress;
  updateBinDisplays();
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
  const HEX_OFFSET_X = 0xfff00000;
  const HEX_OFFSET_Y = 0xfffa0000;
  const HEX_MULTIPLIER = 0x1000;

  const hexX = '0x' + (x * HEX_MULTIPLIER + HEX_OFFSET_X).toString(16).toUpperCase();
  const hexY = '0x' + (y * HEX_MULTIPLIER + HEX_OFFSET_Y).toString(16).toUpperCase();

  hexXEl.textContent = hexX;
  hexYEl.textContent = hexY;
}

function showMessage(text, type = 'info') {
  messageArea.innerHTML = `<div class="message ${type}">${text}</div>`;
  setTimeout(() => {
    messageArea.innerHTML = '';
  }, 3000);
}

function clearGridSelection() {
  for (const row of gameState.grid) {
    for (const cell of row) {
      cell.selected = false;
    }
  }
}

async function handleClassification(bucket) {
  const response = await api.classify(bucket);

  if (response.success) {
    showMessage(`${response.classified_count} numbers refined to ${bucket}`, 'success');
    gameState.bins = response.bins;
    gameState.progress = response.progress;
    const state = await api.getState();
    gameState.grid = state.grid;
  } else {
    showMessage('Classification failed - wrong bucket', 'error');
    clearGridSelection();
  }
  renderGame();
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

document.addEventListener('click', async (e) => {
  if (currentScreen !== AppScreen.GAME) return;

  // Cell click - toggle selection
  if (e.target.classList.contains('cell') && !e.target.classList.contains('classified')) {
    const x = parseInt(e.target.dataset.x);
    const y = parseInt(e.target.dataset.y);

    const response = await api.selectCell(x, y);
    // Update local state with selected positions
    for (const row of gameState.grid) {
      for (const cell of row) {
        cell.selected = response.selected.some(([sx, sy]) => sx === cell.x && sy === cell.y);
      }
    }
    renderGame();
  }

  // Bin click - classify selected
  const bin = e.target.closest('.bin');
  if (bin) {
    await handleClassification(bin.dataset.bin);
  }
});

// ============================================================================
// Event Handlers - Keyboard
// ============================================================================

document.addEventListener('keydown', async (e) => {
  if (currentScreen !== AppScreen.GAME) return;
  if (e.target.tagName === 'INPUT') return;

  // 1-5 keys classify to bins
  const keyToBucket = { '1': '01', '2': '02', '3': '03', '4': '04', '5': '05' };
  const bucket = keyToBucket[e.key];

  if (bucket) {
    await handleClassification(bucket);
  }

  // C clears selection
  if (e.key === 'c' || e.key === 'C') {
    await api.clearSelection();
    clearGridSelection();
    renderGame();
  }

  // H shows hint
  if (e.key === 'h' || e.key === 'H') {
    const hint = await api.getHint();
    if (hint.region) {
      showMessage(`Try bucket ${hint.region.bucket}`, 'info');
    }
  }
});

// ============================================================================
// Initialize
// ============================================================================

showScreen(AppScreen.WELCOME);
console.log('MDR Terminal initialized (API mode)');

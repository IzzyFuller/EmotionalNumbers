/**
 * API Client for MDR Terminal
 *
 * Thin wrapper over fetch calls to the Python backend.
 */

const API_BASE = '/api';

async function post(endpoint, data = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function get(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`);
  return response.json();
}

export async function startGame() {
  return post('/start');
}

export async function submitAnswers(answers) {
  return post('/answers', { answers });
}

export async function getState() {
  return get('/state');
}

export async function selectCell(x, y) {
  return post('/select', { x, y });
}

export async function clearSelection() {
  return post('/clear');
}

export async function classify(bucket) {
  return post('/classify', { bucket });
}

export async function getHint() {
  return get('/hint');
}

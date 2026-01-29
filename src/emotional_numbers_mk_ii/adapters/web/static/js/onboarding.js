/**
 * Onboarding module - Pure functions for managing onboarding questionnaire state.
 *
 * Severance-inspired employee orientation protocol.
 * All functions are pure - no side effects, no DOM manipulation.
 */

/**
 * Create initial onboarding state.
 * @param {Array<{id: string, text: string, category: string, answerType: string}>} questions
 * @returns {{questions: Array, currentIndex: number, answers: Array}}
 */
export function createOnboardingState(questions) {
    return {
        questions: [...questions],
        currentIndex: 0,
        answers: []
    }
}

/**
 * Get the current question to display.
 * @param {{questions: Array, currentIndex: number}} state
 * @returns {Object|null} Current question or null if complete/empty
 */
export function getCurrentQuestion(state) {
    if (state.questions.length === 0) {
        return null
    }
    if (state.currentIndex >= state.questions.length) {
        return null
    }
    return state.questions[state.currentIndex]
}

/**
 * Submit an answer and advance to next question.
 * @param {{questions: Array, currentIndex: number, answers: Array}} state
 * @param {string} answer
 * @returns {{questions: Array, currentIndex: number, answers: Array}} New state
 */
export function submitAnswer(state, answer) {
    const trimmedAnswer = answer.trim()

    // Reject empty answers
    if (trimmedAnswer === '') {
        return state
    }

    // Don't accept answers when complete
    if (state.currentIndex >= state.questions.length) {
        return state
    }

    const currentQuestion = state.questions[state.currentIndex]

    return {
        ...state,
        currentIndex: state.currentIndex + 1,
        answers: [
            ...state.answers,
            { questionId: currentQuestion.id, answer: trimmedAnswer }
        ]
    }
}

/**
 * Check if all questions have been answered.
 * @param {{questions: Array, answers: Array}} state
 * @returns {boolean}
 */
export function isComplete(state) {
    return state.answers.length >= state.questions.length
}

/**
 * Get all collected answers.
 * @param {{answers: Array}} state
 * @returns {Array<{questionId: string, answer: string}>} Copy of answers array
 */
export function getAnswers(state) {
    return [...state.answers]
}

/**
 * Get progress through the questionnaire.
 * @param {{questions: Array, answers: Array}} state
 * @returns {{current: number, total: number}}
 */
export function getProgress(state) {
    return {
        current: state.answers.length,
        total: state.questions.length
    }
}

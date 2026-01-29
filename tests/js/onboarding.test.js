import { describe, it, expect } from 'vitest'
import {
    createOnboardingState,
    getCurrentQuestion,
    submitAnswer,
    isComplete,
    getAnswers,
    getProgress
} from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/onboarding.js'
import { selectQuestions } from '../../src/emotional_numbers_mk_ii/adapters/web/static/js/questions.js'

// Test fixtures
const testQuestions = [
    { id: 'q1', text: 'What is the color of silence?', category: 'surreal', answerType: 'text' },
    { id: 'q2', text: 'How many windows in your childhood room?', category: 'demographic', answerType: 'number' },
    { id: 'q3', text: 'Rate your compliance.', category: 'procedural', answerType: 'scale' },
]

describe('createOnboardingState', () => {
    it('creates initial state with questions', () => {
        const state = createOnboardingState(testQuestions)

        expect(state.questions).toEqual(testQuestions)
        expect(state.currentIndex).toBe(0)
        expect(state.answers).toEqual([])
    })

    it('creates empty state with no questions', () => {
        const state = createOnboardingState([])

        expect(state.questions).toEqual([])
        expect(state.currentIndex).toBe(0)
        expect(state.answers).toEqual([])
    })
})

describe('getCurrentQuestion', () => {
    it('returns first question initially', () => {
        const state = createOnboardingState(testQuestions)

        const question = getCurrentQuestion(state)

        expect(question).toEqual(testQuestions[0])
    })

    it('returns null when no questions', () => {
        const state = createOnboardingState([])

        const question = getCurrentQuestion(state)

        expect(question).toBeNull()
    })

    it('returns null when all questions answered', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'answer1')
        state = submitAnswer(state, 'answer2')
        state = submitAnswer(state, 'answer3')

        const question = getCurrentQuestion(state)

        expect(question).toBeNull()
    })
})

describe('submitAnswer', () => {
    it('records answer and advances to next question', () => {
        const state = createOnboardingState(testQuestions)

        const newState = submitAnswer(state, 'blue')

        expect(newState.answers).toEqual([
            { questionId: 'q1', answer: 'blue' }
        ])
        expect(newState.currentIndex).toBe(1)
    })

    it('handles multiple answers in sequence', () => {
        let state = createOnboardingState(testQuestions)

        state = submitAnswer(state, 'blue')
        state = submitAnswer(state, '3')
        state = submitAnswer(state, '7')

        expect(state.answers).toHaveLength(3)
        expect(state.currentIndex).toBe(3)
        expect(state.answers[0]).toEqual({ questionId: 'q1', answer: 'blue' })
        expect(state.answers[1]).toEqual({ questionId: 'q2', answer: '3' })
        expect(state.answers[2]).toEqual({ questionId: 'q3', answer: '7' })
    })

    it('does nothing when already complete', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'a')
        state = submitAnswer(state, 'b')
        state = submitAnswer(state, 'c')

        const finalState = submitAnswer(state, 'extra')

        expect(finalState.answers).toHaveLength(3)
        expect(finalState.currentIndex).toBe(3)
    })

    it('trims whitespace from answers', () => {
        const state = createOnboardingState(testQuestions)

        const newState = submitAnswer(state, '  blue  ')

        expect(newState.answers[0].answer).toBe('blue')
    })

    it('rejects empty answers', () => {
        const state = createOnboardingState(testQuestions)

        const newState = submitAnswer(state, '   ')

        expect(newState.answers).toEqual([])
        expect(newState.currentIndex).toBe(0)
    })
})

describe('isComplete', () => {
    it('returns false initially', () => {
        const state = createOnboardingState(testQuestions)

        expect(isComplete(state)).toBe(false)
    })

    it('returns false when partially complete', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'answer1')
        state = submitAnswer(state, 'answer2')

        expect(isComplete(state)).toBe(false)
    })

    it('returns true when all questions answered', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'answer1')
        state = submitAnswer(state, 'answer2')
        state = submitAnswer(state, 'answer3')

        expect(isComplete(state)).toBe(true)
    })

    it('returns true for empty question list', () => {
        const state = createOnboardingState([])

        expect(isComplete(state)).toBe(true)
    })
})

describe('getAnswers', () => {
    it('returns empty array initially', () => {
        const state = createOnboardingState(testQuestions)

        expect(getAnswers(state)).toEqual([])
    })

    it('returns all collected answers', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'blue')
        state = submitAnswer(state, '3')

        const answers = getAnswers(state)

        expect(answers).toEqual([
            { questionId: 'q1', answer: 'blue' },
            { questionId: 'q2', answer: '3' }
        ])
    })

    it('returns copy, not reference', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'blue')

        const answers = getAnswers(state)
        answers.push({ questionId: 'fake', answer: 'fake' })

        expect(getAnswers(state)).toHaveLength(1)
    })
})

describe('getProgress', () => {
    it('returns 0/total initially', () => {
        const state = createOnboardingState(testQuestions)

        const progress = getProgress(state)

        expect(progress.current).toBe(0)
        expect(progress.total).toBe(3)
    })

    it('tracks progress as answers submitted', () => {
        let state = createOnboardingState(testQuestions)
        state = submitAnswer(state, 'a')
        state = submitAnswer(state, 'b')

        const progress = getProgress(state)

        expect(progress.current).toBe(2)
        expect(progress.total).toBe(3)
    })

    it('handles empty question list', () => {
        const state = createOnboardingState([])

        const progress = getProgress(state)

        expect(progress.current).toBe(0)
        expect(progress.total).toBe(0)
    })
})

describe('selectQuestions', () => {
    it('returns requested number of questions', () => {
        const selected = selectQuestions(5)

        expect(selected).toHaveLength(5)
    })

    it('returns empty array when count is 0', () => {
        const selected = selectQuestions(0)

        expect(selected).toEqual([])
    })

    it('produces variety across categories', () => {
        const selected = selectQuestions(4, 42)
        const categories = new Set(selected.map(q => q.category))

        // With 4 questions and round-robin, should have multiple categories
        expect(categories.size).toBeGreaterThanOrEqual(2)
    })

    it('is reproducible with same seed', () => {
        const first = selectQuestions(5, 12345)
        const second = selectQuestions(5, 12345)

        expect(first.map(q => q.id)).toEqual(second.map(q => q.id))
    })

    it('produces different results with different seeds', () => {
        const first = selectQuestions(5, 111)
        const second = selectQuestions(5, 222)

        // Very unlikely to be identical
        expect(first.map(q => q.id)).not.toEqual(second.map(q => q.id))
    })
})

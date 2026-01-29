/**
 * Question bank for Severance-inspired onboarding questionnaire.
 *
 * Questions span four categories:
 * - personal: sensory, memory, emotion-focused
 * - demographic: oddly specific facts
 * - surreal: absurdist, Severance-style
 * - procedural: corporate compliance absurdity
 */

export const QUESTIONS = [
    // PERSONAL questions (sensory, memory, emotion-focused)
    {
        id: 'personal_1',
        text: 'What was the predominant smell of your childhood kitchen?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_2',
        text: 'Describe the feeling of your most comfortable chair.',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_3',
        text: 'What sound do you associate with safety?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_4',
        text: 'What texture brings you unexpected comfort?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_5',
        text: 'What is the color of your earliest memory?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_6',
        text: 'What meal reminds you of being cared for?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_7',
        text: 'What song would you hum to comfort yourself?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_8',
        text: 'Describe a place where you felt truly at ease.',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_9',
        text: 'What weather makes you feel most like yourself?',
        category: 'personal',
        answerType: 'text'
    },
    {
        id: 'personal_10',
        text: 'What object would you rescue from a fire?',
        category: 'personal',
        answerType: 'text'
    },

    // DEMOGRAPHIC questions (oddly specific facts)
    {
        id: 'demographic_1',
        text: 'How many windows were visible from your bed as a child?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_2',
        text: 'At what hour do you typically feel most productive?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_3',
        text: 'How many houseplants do you currently maintain?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_4',
        text: 'What is your preferred ambient temperature in Fahrenheit?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_5',
        text: 'How many siblings do you have, including step-siblings?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_6',
        text: 'What floor do you prefer to live on?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_7',
        text: 'How many cups of your preferred beverage do you consume daily?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_8',
        text: 'What is your typical wake-up time on non-work days?',
        category: 'demographic',
        answerType: 'text'
    },
    {
        id: 'demographic_9',
        text: 'How many close friends would you say you have?',
        category: 'demographic',
        answerType: 'number'
    },
    {
        id: 'demographic_10',
        text: 'What year were you happiest?',
        category: 'demographic',
        answerType: 'number'
    },

    // SURREAL questions (use sparingly)
    {
        id: 'surreal_1',
        text: 'What color is the silence between your thoughts?',
        category: 'surreal',
        answerType: 'text'
    },
    {
        id: 'surreal_2',
        text: 'If your anxiety were a small animal, what would it eat?',
        category: 'surreal',
        answerType: 'text'
    },
    {
        id: 'surreal_3',
        text: 'What shape is Tuesday?',
        category: 'surreal',
        answerType: 'text'
    },
    {
        id: 'surreal_4',
        text: 'Describe the weight of an unspoken word.',
        category: 'surreal',
        answerType: 'text'
    },
    {
        id: 'surreal_5',
        text: 'What does the number 7 taste like?',
        category: 'surreal',
        answerType: 'text'
    },

    // PROCEDURAL questions (corporate wellness absurdity)
    {
        id: 'procedural_1',
        text: 'On a scale of 1-10, how would you rate your current compliance?',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_2',
        text: 'How satisfied are you with your satisfaction levels?',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_3',
        text: 'Rate your enthusiasm for mandatory enthusiasm programs.',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_4',
        text: 'How would you describe your relationship with fluorescent lighting?',
        category: 'procedural',
        answerType: 'text'
    },
    {
        id: 'procedural_5',
        text: 'Please confirm your agreement with the previous statement.',
        category: 'procedural',
        answerType: 'text'
    },
    {
        id: 'procedural_6',
        text: 'Rate your willingness to participate in team-building exercises.',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_7',
        text: 'How would you rate the cleanliness of your workspace?',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_8',
        text: 'Do you agree that you are adequately hydrated?',
        category: 'procedural',
        answerType: 'text'
    },
    {
        id: 'procedural_9',
        text: 'Rate your confidence in this assessment process.',
        category: 'procedural',
        answerType: 'scale'
    },
    {
        id: 'procedural_10',
        text: 'How often do you experience workplace-appropriate emotions?',
        category: 'procedural',
        answerType: 'text'
    }
]

/**
 * Select questions with category variety using round-robin.
 * @param {number} count - Number of questions to select (default 5)
 * @param {number|null} seed - Optional seed for reproducibility
 * @returns {Array} Selected questions with category variety
 */
export function selectQuestions(count = 5, seed = null) {
    if (count <= 0) return []

    // Simple seeded random (good enough for this use case)
    const random = seed !== null
        ? seededRandom(seed)
        : () => Math.random()

    // Group by category
    const categories = ['personal', 'demographic', 'surreal', 'procedural']
    const byCategory = {}
    for (const cat of categories) {
        byCategory[cat] = shuffle(
            QUESTIONS.filter(q => q.category === cat),
            random
        )
    }

    // Shuffle category order
    const shuffledCategories = shuffle([...categories], random)

    // Round-robin selection
    const selected = []
    const positions = { personal: 0, demographic: 0, surreal: 0, procedural: 0 }
    let catIndex = 0

    while (selected.length < count) {
        const category = shuffledCategories[catIndex % shuffledCategories.length]
        const questions = byCategory[category]
        const pos = positions[category]

        if (pos < questions.length) {
            selected.push(questions[pos])
            positions[category]++
        }

        catIndex++

        // Safety: prevent infinite loop
        if (catIndex > count * categories.length) break
    }

    return selected.slice(0, count)
}

/**
 * Fisher-Yates shuffle with custom random function.
 */
function shuffle(array, random) {
    const result = [...array]
    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1))
        ;[result[i], result[j]] = [result[j], result[i]]
    }
    return result
}

/**
 * Simple seeded random number generator.
 */
function seededRandom(seed) {
    let s = seed
    return function() {
        s = (s * 1103515245 + 12345) & 0x7fffffff
        return s / 0x7fffffff
    }
}

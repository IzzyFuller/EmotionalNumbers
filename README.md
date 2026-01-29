# Emotional Numbers

A game inspired by Macro Data Refinement from the show *Severance*.

## The Experience

You sit at what appears to be an early terminal application - green phosphor text on a dark screen. A grid of single-digit numbers fills the display. The numbers dance subtly, some more than others.

Your instructions are simple but strange: pay attention to how the numbers make you feel. When you find a group that shares a particular emotional quality, select them and assign them to one of five buckets: **01**, **02**, **03**, **04**, **05**.

If your classification is correct, the numbers disappear into the bucket. If wrong, your selection clears and you try again.

## Progress and Rewards

A progress bar tracks completion. At certain milestones, you receive "prizes" - surreal, corporate rewards that feel slightly off:

- 10%: Lumon logo eraser
- 25%: Blue finger trap
- 75%: Music Dance Experience (the whole team celebrates)
- 100%: Caricature portrait of yourself

## The Mystery

Here's what you don't know:

**The rules change every game.** Each session, an AI generates new hidden rules that determine which numbers belong in which buckets. The rules might be based on position, value, neighbors, or something stranger.

**The hints are there, but unexplained.** Numbers give off signals - maybe they jiggle differently, maybe their position matters, maybe something about their neighbors. The signals are consistent within a game, but you have to discover what they mean.

**Onboarding shapes the puzzle.** Before each game, you answer a few strange questions. Your answers influence the puzzle in ways you cannot see. The connection is real but mysterious.

## Aesthetic

The entire experience evokes corporate dread through mundane presentation:
- Retro terminal appearance (phosphor glow, scanlines)
- Sterile, bureaucratic language
- Rewards that feel like workplace compliance incentives
- The unsettling feeling of doing meaningful-seeming work with no visible purpose

---

## Test Seed: All "cake" Answers

For testing and development, answering all 5 questions with "cake" produces a deterministic puzzle (seed: `897605152`) with these hidden regions on the 40x25 grid:

```
     0    5    10   15   20   25   30   35   40
   0 ·····································───···
   1 ·····································│··│··
   2 ·····················111·············│3344··
   3 ·····················111·············│3344··
   4 ·····················111·············33····
   5 ·····································33····
   6 ········································
   7 ········································
     ...
  14 ····························222·········
  15 ····························222·········
  16 ····························222·········
     ...
  24 ········································
```

| Region | Bucket | Position | Size |
|--------|--------|----------|------|
| 1 | 01 | x=23-25, y=2-4 | 3x3 (9 cells) |
| 2 | 02 | x=28-30, y=14-16 | 3x3 (9 cells) |
| 3 | 03 | x=31-32, y=2-5 | 2x4 (8 cells) |
| 4 | 04 | x=31-34, y=2-3 | 4x2 (8 cells) |

Note: Regions 3 and 4 overlap at positions (31,2), (32,2), (31,3), (32,3).

---

## Development

### Setup

```bash
# Install Python dependencies
uv sync --all-extras

# Install JS dependencies
npm install
```

### Running the Server

```bash
uv run uvicorn emotional_numbers_mk_ii.adapters.web.app:app --reload --port 8000
```

Then open http://localhost:8000

### Running Tests

```bash
# All tests
npm test && uv run pytest

# With coverage
npm test -- --coverage && uv run pytest
```

### Test Coverage in VS Code

Coverage is configured for both JS (Vitest) and Python (pytest-cov).

1. Install the **Coverage Gutters** extension
2. Run tests with coverage: `npm test -- --coverage && uv run pytest`
3. Open a source file and click **Watch** in the status bar (or `Cmd+Shift+P` → "Coverage Gutters: Display Coverage")

Coverage files are output to `coverage/`:
- `lcov.info` - JavaScript coverage
- `lcov-python.info` - Python coverage

**Excluded from Python coverage:**
- `__init__.py` files
- `protocols/` directories
- `main.py` files

---

*"The work is mysterious and important."*

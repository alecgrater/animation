# Character Animation

A pygame-based animation featuring two characters that walk toward each other, collide, and have a humorous conversation with realistic text-to-speech audio.

## Features

- **Animated Characters**: Two characters with walking animations and facial expressions
- **Realistic Voice Audio**: Uses OpenAI TTS API with Apple Floodgate authentication
- **Multi-phase Animation**: Complex state machine with multiple dialogue phases
- **Sound Effects**: Procedurally generated walking sounds
- **Clean Architecture**: Modular code structure with separation of concerns

## Project Structure

```
.
├── main.py                 # Entry point
├── src/
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration constants
│   ├── audio.py           # Audio management (TTS and sound effects)
│   ├── character.py       # Character class with drawing and movement
│   └── animation.py       # Animation state machine and controller
├── pyproject.toml         # Project dependencies (uv)
└── README.md              # This file
```

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
# Install dependencies
uv sync

# Run the animation
uv run main.py
```

## Dependencies

- **pygame**: Graphics and audio rendering
- **openai**: Text-to-speech API
- **numpy**: Sound wave generation

## Animation Sequence

1. **Walking In**: Characters enter from opposite sides of the screen
2. **Collision**: Characters collide and yell "WATCH IT!"
3. **Kidding**: First character says "Just kidding, running into people is fun!"
4. **Hey Ya**: Second character responds "Hey ya!"
5. **Collision Loop**: Characters bounce into each other while smiling for 6 seconds
6. **Final Dialogue**: 
   - Character 1: "Okay I have to go to work"
   - Character 2: "I don't care"
7. **Walking Out**: Characters exit in opposite directions

## Configuration

All configuration constants are in [`src/config.py`](src/config.py:1):
- Screen dimensions
- Colors
- Character properties
- Animation timing
- Audio settings
- Apple Floodgate authentication

## Architecture

### [`src/character.py`](src/character.py:1)
Defines the [`Character`](src/character.py:13) class with:
- Position and movement
- Drawing (body, head, eyes, mouth)
- Walking animation
- Facial expressions (smiling/neutral)

### [`src/audio.py`](src/audio.py:1)
Manages audio with the [`AudioManager`](src/audio.py:30) class:
- OpenAI TTS integration with Apple authentication
- Audio caching for performance
- Procedural walking sound generation
- Background audio preloading

### [`src/animation.py`](src/animation.py:1)
Controls animation flow with:
- [`AnimationPhase`](src/animation.py:28) enum for state management
- [`AnimationController`](src/animation.py:41) class for state machine
- Phase transitions and timing
- Dialogue rendering

### [`main.py`](main.py:1)
Entry point that:
- Initializes pygame and audio
- Creates characters and animation controller
- Runs the main game loop
- Handles events and rendering

## Apple Internal Authentication

This project uses Apple's internal Floodgate service for OpenAI API access. The authentication is configured in [`src/config.py`](src/config.py:38) and handled by [`setup_openai_client()`](src/audio.py:18) in [`src/audio.py`](src/audio.py:1).

## License

Internal Apple project.
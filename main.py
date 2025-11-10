"""Main entry point for the character animation."""

import sys

import pygame

from src.animation import AnimationController
from src.audio import AudioManager
from src.character import Character
from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    WHITE,
    BLUE,
    RED,
    AUDIO_SAMPLE_RATE,
    AUDIO_BUFFER_SIZE,
)


def main() -> None:
    """Run the character animation."""
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init(
        frequency=AUDIO_SAMPLE_RATE, size=-16, channels=2, buffer=AUDIO_BUFFER_SIZE
    )

    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Character Animation with Audio")
    clock = pygame.time.Clock()

    # Initialize audio manager
    audio_manager = AudioManager()
    walking_sound = audio_manager.load_walking_sound()

    # Create characters with different voices
    char1 = Character(
        x=-50,
        y=SCREEN_HEIGHT - 200,
        color=BLUE,
        name="Character 1",
        voice="alloy",
    )
    char2 = Character(
        x=SCREEN_WIDTH + 10,
        y=SCREEN_HEIGHT - 200,
        color=RED,
        name="Character 2",
        voice="echo",
    )
    char2.direction = -1  # Moving left

    # Initialize animation controller
    animation = AnimationController(char1, char2, audio_manager, walking_sound)

    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update animation
        current_time = pygame.time.get_ticks()
        animation.update(current_time)

        # Auto-close when animation is finished
        if animation.phase == animation.AnimationPhase.FINISHED:
            # Wait 1 second after finishing, then close
            if animation.finished_time and current_time - animation.finished_time > 1000:
                running = False

        # Clear screen
        screen.fill(WHITE)

        # Draw characters
        char1.draw(screen)
        char2.draw(screen)

        # Draw dialogue
        animation.draw_dialogue(screen)

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    # Clean up
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

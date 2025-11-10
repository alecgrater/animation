"""Export animation as TikTok-optimized video with audio."""

import sys
import os
import subprocess
import numpy as np
import pygame
import cv2

from src.animation import AnimationController
from src.audio import AudioManager
from src.character import Character
from src.config import (
    FPS,
    BLUE,
    RED,
    AUDIO_SAMPLE_RATE,
    AUDIO_BUFFER_SIZE,
)

# TikTok optimal settings
TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920
OUTPUT_FILENAME = "tiktok_animation.mp4"
TEMP_VIDEO_FILENAME = "temp_video_no_audio.avi"


def draw_park_background(screen: pygame.Surface, width: int, height: int) -> None:
    """Draw a park setting background scaled to TikTok dimensions."""
    # Sky gradient (light blue to lighter blue)
    for y in range(height // 2):
        ratio = y / (height // 2)
        r = int(135 + (180 - 135) * ratio)
        g = int(206 + (220 - 206) * ratio)
        b = int(235 + (245 - 235) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))
    
    # Grass (green gradient)
    grass_start_y = height // 2
    for y in range(grass_start_y, height):
        ratio = (y - grass_start_y) / (height - grass_start_y)
        r = int(100 + (80 - 100) * ratio)
        g = int(180 + (150 - 180) * ratio)
        b = int(100 + (80 - 100) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))
    
    # Path/walkway (light gray) - scaled
    path_y = height - int(height * 0.33)
    path_height = int(height * 0.2)
    pygame.draw.rect(screen, (200, 200, 200),
                    (0, path_y, width, path_height))
    
    # Path edge lines
    pygame.draw.line(screen, (150, 150, 150),
                    (0, path_y), (width, path_y), 3)
    pygame.draw.line(screen, (150, 150, 150),
                    (0, path_y + path_height), (width, path_y + path_height), 3)
    
    # Trees in background (scaled positions)
    tree_positions = [int(width * 0.15), int(width * 0.35), 
                     int(width * 0.55), int(width * 0.75)]
    for tree_x in tree_positions:
        # Tree trunk
        trunk_width = int(width * 0.02)
        trunk_height = int(height * 0.08)
        trunk_y = grass_start_y + int(height * 0.05)
        pygame.draw.rect(screen, (101, 67, 33),
                        (tree_x - trunk_width // 2, trunk_y, trunk_width, trunk_height))
        
        # Tree foliage (circles)
        foliage_y = trunk_y - int(height * 0.03)
        foliage_radius = int(width * 0.04)
        pygame.draw.circle(screen, (34, 139, 34), (tree_x, foliage_y), foliage_radius)
        pygame.draw.circle(screen, (50, 150, 50), 
                          (tree_x - foliage_radius // 2, foliage_y + foliage_radius // 4), 
                          int(foliage_radius * 0.75))
        pygame.draw.circle(screen, (50, 150, 50), 
                          (tree_x + foliage_radius // 2, foliage_y + foliage_radius // 4), 
                          int(foliage_radius * 0.75))
    
    # Clouds (scaled)
    cloud_positions = [(int(width * 0.2), int(height * 0.08)), 
                      (int(width * 0.5), int(height * 0.06)), 
                      (int(width * 0.8), int(height * 0.09))]
    for cloud_x, cloud_y in cloud_positions:
        cloud_size = int(width * 0.03)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x, cloud_y), cloud_size)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (cloud_x + int(cloud_size * 0.8), cloud_y), 
                          int(cloud_size * 0.8))
        pygame.draw.circle(screen, (255, 255, 255), 
                          (cloud_x - int(cloud_size * 0.8), cloud_y), 
                          int(cloud_size * 0.8))
        pygame.draw.circle(screen, (255, 255, 255), 
                          (cloud_x + int(cloud_size * 0.3), cloud_y - int(cloud_size * 0.5)), 
                          int(cloud_size * 0.6))
    
    # Sun (scaled)
    sun_x, sun_y = int(width * 0.85), int(height * 0.1)
    sun_radius = int(width * 0.03)
    # Sun glow
    for i in range(5, 0, -1):
        alpha_surf = pygame.Surface((sun_radius * 4, sun_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(alpha_surf, (255, 255, 0, 30), 
                          (sun_radius * 2, sun_radius * 2), 
                          sun_radius + i * int(sun_radius * 0.2))
        screen.blit(alpha_surf, (sun_x - sun_radius * 2, sun_y - sun_radius * 2))
    # Sun core
    pygame.draw.circle(screen, (255, 255, 0), (sun_x, sun_y), sun_radius)
    pygame.draw.circle(screen, (255, 255, 150), (sun_x, sun_y), int(sun_radius * 0.8))
    
    # Flowers/bushes on grass (scaled)
    flower_positions = [(int(width * 0.12), grass_start_y + int(height * 0.03)), 
                       (int(width * 0.35), grass_start_y + int(height * 0.04)),
                       (int(width * 0.58), grass_start_y + int(height * 0.035)), 
                       (int(width * 0.82), grass_start_y + int(height * 0.045))]
    for fx, fy in flower_positions:
        # Bush
        bush_radius = int(width * 0.015)
        pygame.draw.circle(screen, (60, 120, 60), (fx, fy), bush_radius)
        # Flowers
        for i in range(3):
            flower_x = fx + (i - 1) * int(bush_radius * 0.6)
            flower_y = fy - int(bush_radius * 0.6)
            pygame.draw.circle(screen, (255, 100, 150), (flower_x, flower_y), 
                             int(bush_radius * 0.3))
            pygame.draw.circle(screen, (255, 200, 0), (flower_x, flower_y), 
                             int(bush_radius * 0.15))


def export_tiktok_video() -> None:
    """Export the animation as a TikTok-optimized video with audio."""
    print("🎬 Starting TikTok video export...")
    print(f"📐 Resolution: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT} (9:16)")
    print(f"🎞️  Frame rate: {FPS} FPS")
    print("\n💡 TIP: The window will display during export so audio can be captured.")
    print("   Please don't minimize or interact with the window during export.\n")
    
    # Initialize Pygame (with visible window for audio)
    pygame.init()
    pygame.mixer.init(
        frequency=AUDIO_SAMPLE_RATE, size=-16, channels=2, buffer=AUDIO_BUFFER_SIZE
    )

    # Set up display with TikTok dimensions
    screen = pygame.display.set_mode((TIKTOK_WIDTH, TIKTOK_HEIGHT))
    pygame.display.set_caption("Exporting TikTok Video - DO NOT CLOSE")
    clock = pygame.time.Clock()

    # Initialize audio manager
    audio_manager = AudioManager()
    walking_sound = audio_manager.load_walking_sound()
    
    # Load collision sound effect
    try:
        collision_sound = pygame.mixer.Sound("assets/06_collide.wav")
        print("✓ Loaded collision sound effect")
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load collision sound: {e}")
        collision_sound = None
    
    # Load meow sound effect
    try:
        meow_sound = pygame.mixer.Sound("assets/00_00_meow.wav")
        print("✓ Loaded meow sound effect")
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load meow sound: {e}")
        meow_sound = None

    # Create characters with scaled positions
    char1 = Character(
        x=-50,
        y=TIKTOK_HEIGHT - int(TIKTOK_HEIGHT * 0.33),
        color=BLUE,
        name="Character 1",
        voice="alloy",
    )
    char2 = Character(
        x=TIKTOK_WIDTH + 10,
        y=TIKTOK_HEIGHT - int(TIKTOK_HEIGHT * 0.33),
        color=RED,
        name="Character 2",
        voice="echo",
    )
    char2.direction = -1  # Moving left

    # Initialize animation controller
    animation = AnimationController(char1, char2, audio_manager, walking_sound, 
                                   collision_sound, meow_sound)

    # Set up video writer for temporary video (no audio yet)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(
        TEMP_VIDEO_FILENAME,
        fourcc,
        FPS,
        (TIKTOK_WIDTH, TIKTOK_HEIGHT)
    )
    
    if not out.isOpened():
        print("❌ Error: Could not open video writer")
        pygame.quit()
        sys.exit(1)
    
    print("✓ Video writer initialized")
    print("🎥 Recording frames...")
    print("   (Audio is playing - will be added in post-processing)\n")

    frame_count = 0
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

        # Draw park background
        draw_park_background(screen, TIKTOK_WIDTH, TIKTOK_HEIGHT)

        # Draw cat if in cat run phase
        if animation.phase == animation.AnimationPhase.CAT_RUN:
            cat_x = int(animation.cat_x)
            cat_y = TIKTOK_HEIGHT - int(TIKTOK_HEIGHT * 0.25)
            cat_scale = animation.cat_scale
            
            # Calculate scaled dimensions
            base_size = int(TIKTOK_WIDTH * 0.04)
            cat_width = int(base_size * cat_scale)
            cat_height = int(base_size * 0.7 * cat_scale)
            
            # Cat body (oval)
            body_rect = pygame.Rect(cat_x - cat_width // 2, cat_y - cat_height // 2,
                                   cat_width, cat_height)
            pygame.draw.ellipse(screen, (255, 140, 0), body_rect)
            pygame.draw.ellipse(screen, (200, 100, 0), body_rect, max(1, int(2 * cat_scale)))
            
            # Cat head (circle)
            head_size = int(25 * cat_scale * (TIKTOK_WIDTH / 1000))
            head_x = cat_x + int(cat_width // 3)
            head_y = cat_y - int(cat_height // 3)
            pygame.draw.circle(screen, (255, 140, 0), (head_x, head_y), head_size)
            pygame.draw.circle(screen, (200, 100, 0), (head_x, head_y), head_size, 
                             max(1, int(2 * cat_scale)))
            
            # Cat ears (triangles)
            if cat_scale > 0.3:
                ear_size = int(10 * cat_scale * (TIKTOK_WIDTH / 1000))
                # Left ear
                left_ear = [
                    (head_x - int(12 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(15 * cat_scale * (TIKTOK_WIDTH / 1000))),
                    (head_x - int(5 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(5 * cat_scale * (TIKTOK_WIDTH / 1000))),
                    (head_x - int(15 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(5 * cat_scale * (TIKTOK_WIDTH / 1000)))
                ]
                pygame.draw.polygon(screen, (255, 140, 0), left_ear)
                pygame.draw.polygon(screen, (200, 100, 0), left_ear, 
                                  max(1, int(2 * cat_scale)))
                
                # Right ear
                right_ear = [
                    (head_x + int(12 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(15 * cat_scale * (TIKTOK_WIDTH / 1000))),
                    (head_x + int(5 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(5 * cat_scale * (TIKTOK_WIDTH / 1000))),
                    (head_x + int(15 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                     head_y - int(5 * cat_scale * (TIKTOK_WIDTH / 1000)))
                ]
                pygame.draw.polygon(screen, (255, 140, 0), right_ear)
                pygame.draw.polygon(screen, (200, 100, 0), right_ear, 
                                  max(1, int(2 * cat_scale)))
                
                # Eyes (when close)
                if cat_scale > 0.6:
                    eye_size = max(2, int(3 * cat_scale * (TIKTOK_WIDTH / 1000)))
                    pygame.draw.circle(screen, (0, 0, 0),
                                     (head_x - int(6 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                                      head_y), eye_size)
                    pygame.draw.circle(screen, (0, 0, 0),
                                     (head_x + int(6 * cat_scale * (TIKTOK_WIDTH / 1000)), 
                                      head_y), eye_size)
            
            # Cat tail (curved line)
            tail_length = int(30 * cat_scale * (TIKTOK_WIDTH / 1000))
            tail_x = cat_x - int(cat_width // 2)
            tail_y = cat_y
            pygame.draw.line(screen, (255, 140, 0),
                           (tail_x, tail_y),
                           (tail_x - tail_length, tail_y - int(tail_length * 0.7)),
                           max(2, int(4 * cat_scale)))
            
            # Legs (simple lines)
            leg_length = int(15 * cat_scale * (TIKTOK_WIDTH / 1000))
            leg_spacing = int(10 * cat_scale * (TIKTOK_WIDTH / 1000))
            for i in range(2):
                leg_x = cat_x - int(cat_width // 4) + i * leg_spacing
                pygame.draw.line(screen, (255, 140, 0),
                               (leg_x, cat_y + cat_height // 2),
                               (leg_x, cat_y + cat_height // 2 + leg_length),
                               max(2, int(3 * cat_scale)))

        # Draw UFO and abduction beam if in abduction phase
        if animation.phase == animation.AnimationPhase.ALIEN_ABDUCTION:
            # Draw tractor beam
            if animation.beam_alpha > 0:
                beam_color = (150, 255, 150, int(animation.beam_alpha))
                ufo_center_x = int(char2.get_center_x())
                beam_top_width = int(TIKTOK_WIDTH * 0.06)
                beam_bottom_width = int(TIKTOK_WIDTH * 0.12)
                
                for y in range(int(animation.ufo_y + 40), TIKTOK_HEIGHT):
                    progress = (y - (animation.ufo_y + 40)) / (TIKTOK_HEIGHT - (animation.ufo_y + 40))
                    width = int(beam_top_width + (beam_bottom_width - beam_top_width) * progress)
                    alpha = int(animation.beam_alpha * (1 - progress * 0.5))
                    pygame.draw.line(screen, (*beam_color[:3], alpha),
                                   (ufo_center_x - width // 2, y),
                                   (ufo_center_x + width // 2, y), 2)
            
            # Draw UFO (scaled)
            ufo_x = int(char2.get_center_x())
            ufo_y = int(animation.ufo_y)
            ufo_scale = TIKTOK_WIDTH / 1000
            
            # UFO dome (top)
            pygame.draw.ellipse(screen, (200, 200, 200),
                              (ufo_x - int(50 * ufo_scale), ufo_y - int(20 * ufo_scale), 
                               int(100 * ufo_scale), int(40 * ufo_scale)))
            pygame.draw.ellipse(screen, (150, 150, 150),
                              (ufo_x - int(50 * ufo_scale), ufo_y - int(20 * ufo_scale), 
                               int(100 * ufo_scale), int(40 * ufo_scale)), 2)
            
            # UFO base (bottom disc)
            pygame.draw.ellipse(screen, (180, 180, 180),
                              (ufo_x - int(60 * ufo_scale), ufo_y + int(10 * ufo_scale), 
                               int(120 * ufo_scale), int(30 * ufo_scale)))
            pygame.draw.ellipse(screen, (100, 100, 100),
                              (ufo_x - int(60 * ufo_scale), ufo_y + int(10 * ufo_scale), 
                               int(120 * ufo_scale), int(30 * ufo_scale)), 2)
            
            # UFO lights
            light_positions = [-40, -20, 0, 20, 40]
            for i, lx in enumerate(light_positions):
                light_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), 
                              (255, 255, 0), (255, 0, 255)][i]
                lx_scaled = int(lx * ufo_scale)
                # Blinking effect
                if (current_time // 200 + i) % 2 == 0:
                    pygame.draw.circle(screen, light_color, 
                                     (ufo_x + lx_scaled, ufo_y + int(20 * ufo_scale)), 
                                     int(5 * ufo_scale))
                else:
                    pygame.draw.circle(screen, (100, 100, 100), 
                                     (ufo_x + lx_scaled, ufo_y + int(20 * ufo_scale)), 
                                     int(5 * ufo_scale))
            
            # UFO window
            pygame.draw.circle(screen, (100, 150, 200), (ufo_x, ufo_y), int(15 * ufo_scale))
            pygame.draw.circle(screen, (50, 100, 150), (ufo_x, ufo_y), int(15 * ufo_scale), 2)

        # Draw characters
        char1.draw(screen)
        char2.draw(screen)

        # Draw dialogue
        animation.draw_dialogue(screen)

        # Capture frame
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        
        frame_count += 1
        
        if frame_count % 60 == 0:
            print(f"  Recorded {frame_count} frames ({frame_count // FPS}s)")

        pygame.display.flip()
        clock.tick(FPS)

    # Release video writer
    out.release()
    pygame.quit()
    
    print("\n✓ Video frames saved")
    print("🎵 Converting to TikTok format with ffmpeg...")
    
    # Use ffmpeg to convert to MP4 with proper codec
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', TEMP_VIDEO_FILENAME,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-r', str(FPS),
            OUTPUT_FILENAME
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Video converted successfully")
            # Clean up temp file
            if os.path.exists(TEMP_VIDEO_FILENAME):
                os.remove(TEMP_VIDEO_FILENAME)
        else:
            print(f"⚠️  ffmpeg conversion had issues: {result.stderr}")
            print(f"   Temp video saved as: {TEMP_VIDEO_FILENAME}")
            
    except FileNotFoundError:
        print("⚠️  ffmpeg not found. Keeping temp video file.")
        print(f"   Install ffmpeg or use: {TEMP_VIDEO_FILENAME}")
    except Exception as e:
        print(f"⚠️  Error during conversion: {e}")
        print(f"   Temp video saved as: {TEMP_VIDEO_FILENAME}")
    
    print(f"\n✅ Export complete!")
    print(f"📹 Total frames: {frame_count}")
    print(f"⏱️  Duration: {frame_count / FPS:.2f} seconds")
    print(f"💾 Output file: {OUTPUT_FILENAME}")
    print(f"📏 Resolution: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT} (9:16 aspect ratio)")
    print(f"🎞️  Frame rate: {FPS} FPS")
    print(f"\n⚠️  NOTE: This export captures video only.")
    print(f"   To add audio, you can:")
    print(f"   1. Use screen recording software (QuickTime, OBS, etc.)")
    print(f"   2. Run main.py and record with audio capture")
    print(f"   3. Add audio in video editing software")


if __name__ == "__main__":
    export_tiktok_video()
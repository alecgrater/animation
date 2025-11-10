"""Export animation as TikTok video with properly synced audio."""

import sys
import os
import subprocess
import tempfile
import numpy as np
import pygame
import cv2
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
from pathlib import Path

from src.animation import AnimationController
from src.audio import AudioManager
from src.character import Character
from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    BLUE,
    RED,
    AUDIO_SAMPLE_RATE,
    AUDIO_BUFFER_SIZE,
)

# TikTok settings - crop to 9:16 from center
TIKTOK_HEIGHT = 1920
TIKTOK_WIDTH = 1080

# Calculate crop area from original 1000x600
CROP_WIDTH = int(SCREEN_HEIGHT * (TIKTOK_WIDTH / TIKTOK_HEIGHT))
CROP_X = (SCREEN_WIDTH - CROP_WIDTH) // 2

OUTPUT_FILENAME = "tiktok.mp4"


def draw_park_background(screen: pygame.Surface) -> None:
    """Draw a park setting background."""
    # Sky gradient
    for y in range(SCREEN_HEIGHT // 2):
        ratio = y / (SCREEN_HEIGHT // 2)
        r = int(135 + (180 - 135) * ratio)
        g = int(206 + (220 - 206) * ratio)
        b = int(235 + (245 - 235) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # Grass
    grass_start_y = SCREEN_HEIGHT // 2
    for y in range(grass_start_y, SCREEN_HEIGHT):
        ratio = (y - grass_start_y) / (SCREEN_HEIGHT - grass_start_y)
        r = int(100 + (80 - 100) * ratio)
        g = int(180 + (150 - 180) * ratio)
        b = int(100 + (80 - 100) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # Path
    path_y = SCREEN_HEIGHT - 200
    path_height = 120
    pygame.draw.rect(screen, (200, 200, 200), (0, path_y, SCREEN_WIDTH, path_height))
    pygame.draw.line(screen, (150, 150, 150), (0, path_y), (SCREEN_WIDTH, path_y), 3)
    pygame.draw.line(screen, (150, 150, 150), (0, path_y + path_height), (SCREEN_WIDTH, path_y + path_height), 3)
    
    # Trees
    tree_positions = [100, 300, 500, 700]
    for tree_x in tree_positions:
        trunk_width, trunk_height = 20, 60
        trunk_y = grass_start_y + 40
        pygame.draw.rect(screen, (101, 67, 33), (tree_x - trunk_width // 2, trunk_y, trunk_width, trunk_height))
        foliage_y = trunk_y - 20
        pygame.draw.circle(screen, (34, 139, 34), (tree_x, foliage_y), 40)
        pygame.draw.circle(screen, (50, 150, 50), (tree_x - 20, foliage_y + 10), 30)
        pygame.draw.circle(screen, (50, 150, 50), (tree_x + 20, foliage_y + 10), 30)
    
    # Clouds
    cloud_positions = [(150, 80), (400, 60), (650, 90)]
    for cloud_x, cloud_y in cloud_positions:
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x, cloud_y), 30)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x + 25, cloud_y), 25)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x - 25, cloud_y), 25)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x + 10, cloud_y - 15), 20)
    
    # Sun
    sun_x, sun_y = 700, 100
    for i in range(5, 0, -1):
        alpha_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(alpha_surf, (255, 255, 0, 30), (50, 50), 30 + i * 5)
        screen.blit(alpha_surf, (sun_x - 50, sun_y - 50))
    pygame.draw.circle(screen, (255, 255, 0), (sun_x, sun_y), 30)
    pygame.draw.circle(screen, (255, 255, 150), (sun_x, sun_y), 25)
    
    # Flowers
    flower_positions = [(80, grass_start_y + 20), (250, grass_start_y + 30),
                       (450, grass_start_y + 25), (620, grass_start_y + 35)]
    for fx, fy in flower_positions:
        pygame.draw.circle(screen, (60, 120, 60), (fx, fy), 15)
        for i in range(3):
            flower_x = fx + (i - 1) * 10
            flower_y = fy - 10
            pygame.draw.circle(screen, (255, 100, 150), (flower_x, flower_y), 4)
            pygame.draw.circle(screen, (255, 200, 0), (flower_x, flower_y), 2)


def create_audio_track(animation_events, total_duration_s, output_file):
    """Create complete audio track by mixing all sounds at correct timestamps using moviepy."""
    print("🎵 Building audio track with moviepy...")
    
    audio_clips = []
    
    # Add each audio event
    for event in animation_events:
        event_type = event['type']
        timestamp_s = event['timestamp_ms'] / 1000.0
        
        try:
            if event_type == 'meow':
                clip = AudioFileClip("assets/00_00_meow.wav").set_start(timestamp_s)
                audio_clips.append(clip)
                print(f"  Added meow at {timestamp_s:.2f}s")
                
            elif event_type == 'collision':
                clip = AudioFileClip("assets/06_collide.wav").set_start(timestamp_s)
                audio_clips.append(clip)
                print(f"  Added collision at {timestamp_s:.2f}s")
                
            elif event_type == 'dialogue':
                dialogue_file = event['file']
                clip = AudioFileClip(dialogue_file).set_start(timestamp_s)
                audio_clips.append(clip)
                print(f"  Added dialogue at {timestamp_s:.2f}s: {dialogue_file}")
                
            elif event_type == 'walking_start':
                # Loop walking sound for the duration
                walking_clip = AudioFileClip("assets/walking.wav")
                duration_s = event['duration_ms'] / 1000.0
                # Loop the clip
                loops_needed = int(duration_s / walking_clip.duration) + 1
                looped = concatenate_audioclips([walking_clip] * loops_needed)
                looped = looped.subclip(0, duration_s).set_start(timestamp_s)
                audio_clips.append(looped)
                print(f"  Added walking sound at {timestamp_s:.2f}s for {duration_s:.2f}s")
                
        except Exception as e:
            print(f"  Warning: Could not add {event_type}: {e}")
    
    if audio_clips:
        # Composite all audio clips
        final_audio = CompositeAudioClip(audio_clips)
        # Set duration to match video
        final_audio = final_audio.set_duration(total_duration_s)
        # Write to file
        final_audio.write_audiofile(output_file, fps=44100, codec='pcm_s16le')
        
        # Close clips
        for clip in audio_clips:
            clip.close()
        final_audio.close()
        
        return True
    return False


def export_tiktok_video():
    """Export the animation as TikTok video with audio."""
    print("🎬 Starting TikTok video export with audio...")
    print(f"📐 Output: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT} (9:16 vertical)")
    print(f"🎞️  Frame rate: {FPS} FPS")
    print(f"✂️  Cropping from center of {SCREEN_WIDTH}x{SCREEN_HEIGHT}\n")
    
    temp_dir = tempfile.mkdtemp()
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init(frequency=AUDIO_SAMPLE_RATE, size=-16, channels=2, buffer=AUDIO_BUFFER_SIZE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Exporting TikTok Video...")
    clock = pygame.time.Clock()

    # Initialize audio manager
    audio_manager = AudioManager()
    walking_sound = audio_manager.load_walking_sound()
    
    try:
        collision_sound = pygame.mixer.Sound("assets/06_collide.wav")
        print("✓ Loaded collision sound")
    except:
        collision_sound = None
    
    try:
        meow_sound = pygame.mixer.Sound("assets/00_00_meow.wav")
        print("✓ Loaded meow sound")
    except:
        meow_sound = None

    # Create characters
    char1 = Character(x=-50, y=SCREEN_HEIGHT - 200, color=BLUE, name="Character 1", voice="alloy")
    char2 = Character(x=SCREEN_WIDTH + 10, y=SCREEN_HEIGHT - 200, color=RED, name="Character 2", voice="echo")
    char2.direction = -1

    # Initialize animation
    animation = AnimationController(char1, char2, audio_manager, walking_sound, collision_sound, meow_sound)

    # Track audio events with timestamps
    audio_events = []
    frame_count = 0
    running = True
    last_phase = None
    walking_start_time = None
    
    print("🎥 Recording frames and tracking audio events...\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        current_time = pygame.time.get_ticks()
        current_phase = animation.phase
        
        # Track phase changes for audio events
        if current_phase != last_phase:
            if current_phase == animation.AnimationPhase.CAT_RUN and frame_count > 0:
                # Meow happens at ~55% through cat run (around 385ms into 700ms run)
                audio_events.append({'type': 'meow', 'timestamp_ms': current_time + 385})
                
            elif current_phase == animation.AnimationPhase.WALKING_IN:
                walking_start_time = current_time
                
            elif current_phase == animation.AnimationPhase.COLLISION:
                # Stop walking sound
                if walking_start_time:
                    duration = current_time - walking_start_time
                    audio_events.append({'type': 'walking_start', 'timestamp_ms': walking_start_time, 'duration_ms': duration})
                    walking_start_time = None
                # Collision sound
                audio_events.append({'type': 'collision', 'timestamp_ms': current_time})
                # "WATCH IT!" dialogue (both characters)
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/01_01_watch_it.wav'})
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/01_02_watch_it.wav'})
                
            elif current_phase == animation.AnimationPhase.KIDDING_DIALOGUE:
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/02_01_just_kidding.wav'})
                
            elif current_phase == animation.AnimationPhase.HEY_YA_DIALOGUE:
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/03_02_hey_ya.wav'})
                
            elif current_phase == animation.AnimationPhase.BUMP_SEQUENCE:
                walking_start_time = current_time
                
            elif current_phase == animation.AnimationPhase.COLLISION_LOOP:
                if walking_start_time:
                    duration = current_time - walking_start_time
                    audio_events.append({'type': 'walking_start', 'timestamp_ms': walking_start_time, 'duration_ms': duration})
                walking_start_time = current_time
                
            elif current_phase == animation.AnimationPhase.FINAL_DIALOGUE_1:
                if walking_start_time:
                    duration = current_time - walking_start_time
                    audio_events.append({'type': 'walking_start', 'timestamp_ms': walking_start_time, 'duration_ms': duration})
                    walking_start_time = None
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/04_01_go_to_work.wav'})
                
            elif current_phase == animation.AnimationPhase.FINAL_DIALOGUE_2:
                audio_events.append({'type': 'dialogue', 'timestamp_ms': current_time, 'file': 'assets/05_02_i_dont_care.wav'})
                
            elif current_phase == animation.AnimationPhase.WALKING_OUT:
                walking_start_time = current_time
                
            last_phase = current_phase

        # Track collision sounds during bump sequence and collision loop
        if current_phase == animation.AnimationPhase.BUMP_SEQUENCE:
            if char1.get_rect().colliderect(char2.get_rect()):
                audio_events.append({'type': 'collision', 'timestamp_ms': current_time})
        elif current_phase == animation.AnimationPhase.COLLISION_LOOP:
            if char1.get_rect().colliderect(char2.get_rect()):
                audio_events.append({'type': 'collision', 'timestamp_ms': current_time})

        animation.update(current_time)

        if animation.phase == animation.AnimationPhase.FINISHED:
            if animation.finished_time and current_time - animation.finished_time > 1000:
                # Add final walking sound if still active
                if walking_start_time:
                    duration = current_time - walking_start_time
                    audio_events.append({'type': 'walking_start', 'timestamp_ms': walking_start_time, 'duration_ms': duration})
                running = False

        # Draw everything
        draw_park_background(screen)

        # Draw cat
        if animation.phase == animation.AnimationPhase.CAT_RUN:
            cat_x, cat_y = int(animation.cat_x), SCREEN_HEIGHT - 150
            cat_scale = animation.cat_scale
            base_size = 40
            cat_width = int(base_size * cat_scale)
            cat_height = int(base_size * 0.7 * cat_scale)
            
            body_rect = pygame.Rect(cat_x - cat_width // 2, cat_y - cat_height // 2, cat_width, cat_height)
            pygame.draw.ellipse(screen, (255, 140, 0), body_rect)
            pygame.draw.ellipse(screen, (200, 100, 0), body_rect, max(1, int(2 * cat_scale)))
            
            head_size = int(25 * cat_scale)
            head_x = cat_x + int(cat_width // 3)
            head_y = cat_y - int(cat_height // 3)
            pygame.draw.circle(screen, (255, 140, 0), (head_x, head_y), head_size)
            pygame.draw.circle(screen, (200, 100, 0), (head_x, head_y), head_size, max(1, int(2 * cat_scale)))
            
            if cat_scale > 0.3:
                left_ear = [(head_x - int(12 * cat_scale), head_y - int(15 * cat_scale)),
                           (head_x - int(5 * cat_scale), head_y - int(5 * cat_scale)),
                           (head_x - int(15 * cat_scale), head_y - int(5 * cat_scale))]
                pygame.draw.polygon(screen, (255, 140, 0), left_ear)
                pygame.draw.polygon(screen, (200, 100, 0), left_ear, max(1, int(2 * cat_scale)))
                
                right_ear = [(head_x + int(12 * cat_scale), head_y - int(15 * cat_scale)),
                            (head_x + int(5 * cat_scale), head_y - int(5 * cat_scale)),
                            (head_x + int(15 * cat_scale), head_y - int(5 * cat_scale))]
                pygame.draw.polygon(screen, (255, 140, 0), right_ear)
                pygame.draw.polygon(screen, (200, 100, 0), right_ear, max(1, int(2 * cat_scale)))
                
                if cat_scale > 0.6:
                    eye_size = max(2, int(3 * cat_scale))
                    pygame.draw.circle(screen, (0, 0, 0), (head_x - int(6 * cat_scale), head_y), eye_size)
                    pygame.draw.circle(screen, (0, 0, 0), (head_x + int(6 * cat_scale), head_y), eye_size)
            
            tail_length = int(30 * cat_scale)
            tail_x = cat_x - int(cat_width // 2)
            tail_y = cat_y
            pygame.draw.line(screen, (255, 140, 0), (tail_x, tail_y),
                           (tail_x - tail_length, tail_y - int(tail_length * 0.7)), max(2, int(4 * cat_scale)))
            
            leg_length = int(15 * cat_scale)
            leg_spacing = int(10 * cat_scale)
            for i in range(2):
                leg_x = cat_x - int(cat_width // 4) + i * leg_spacing
                pygame.draw.line(screen, (255, 140, 0), (leg_x, cat_y + cat_height // 2),
                               (leg_x, cat_y + cat_height // 2 + leg_length), max(2, int(3 * cat_scale)))

        # Draw UFO
        if animation.phase == animation.AnimationPhase.ALIEN_ABDUCTION:
            if animation.beam_alpha > 0:
                ufo_center_x = int(char2.get_center_x())
                beam_top_width, beam_bottom_width = 60, 120
                for y in range(int(animation.ufo_y + 40), SCREEN_HEIGHT):
                    progress = (y - (animation.ufo_y + 40)) / (SCREEN_HEIGHT - (animation.ufo_y + 40))
                    width = int(beam_top_width + (beam_bottom_width - beam_top_width) * progress)
                    alpha = int(animation.beam_alpha * (1 - progress * 0.5))
                    pygame.draw.line(screen, (150, 255, 150, alpha),
                                   (ufo_center_x - width // 2, y), (ufo_center_x + width // 2, y), 2)
            
            ufo_x, ufo_y = int(char2.get_center_x()), int(animation.ufo_y)
            pygame.draw.ellipse(screen, (200, 200, 200), (ufo_x - 50, ufo_y - 20, 100, 40))
            pygame.draw.ellipse(screen, (150, 150, 150), (ufo_x - 50, ufo_y - 20, 100, 40), 2)
            pygame.draw.ellipse(screen, (180, 180, 180), (ufo_x - 60, ufo_y + 10, 120, 30))
            pygame.draw.ellipse(screen, (100, 100, 100), (ufo_x - 60, ufo_y + 10, 120, 30), 2)
            
            light_positions = [-40, -20, 0, 20, 40]
            for i, lx in enumerate(light_positions):
                light_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)][i]
                if (current_time // 200 + i) % 2 == 0:
                    pygame.draw.circle(screen, light_color, (ufo_x + lx, ufo_y + 20), 5)
                else:
                    pygame.draw.circle(screen, (100, 100, 100), (ufo_x + lx, ufo_y + 20), 5)
            
            pygame.draw.circle(screen, (100, 150, 200), (ufo_x, ufo_y), 15)
            pygame.draw.circle(screen, (50, 100, 150), (ufo_x, ufo_y), 15, 2)

        char1.draw(screen)
        char2.draw(screen)
        animation.draw_dialogue(screen)

        # Capture and crop frame
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2))
        cropped_frame = frame[:, CROP_X:CROP_X + CROP_WIDTH, :]
        resized_frame = cv2.resize(cropped_frame, (TIKTOK_WIDTH, TIKTOK_HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_RGB2BGR)
        
        frame_path = os.path.join(frames_dir, f"frame_{frame_count:05d}.png")
        cv2.imwrite(frame_path, resized_frame)
        
        frame_count += 1
        if frame_count % 60 == 0:
            print(f"  Recorded {frame_count} frames ({frame_count // FPS}s)")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    
    total_duration_s = frame_count / FPS
    print(f"\n✓ Recorded {frame_count} frames ({total_duration_s:.2f}s)")
    
    # Create audio track
    audio_file = os.path.join(temp_dir, "audio.wav")
    audio_created = create_audio_track(audio_events, total_duration_s, audio_file)
    
    if audio_created:
        print("✓ Audio track created")
    else:
        print("⚠️  No audio events found")
    
    # Create video from frames
    print("🎬 Creating video...")
    temp_video = os.path.join(temp_dir, "temp_video.mp4")
    
    cmd = ['ffmpeg', '-y', '-framerate', str(FPS), '-i', os.path.join(frames_dir, 'frame_%05d.png'),
           '-i', audio_file, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUTPUT_FILENAME]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"\n✅ Export complete!")
        print(f"📹 Frames: {frame_count}")
        print(f"⏱️  Duration: {frame_count / FPS:.2f}s")
        print(f"💾 Output: {OUTPUT_FILENAME}")
        print(f"📏 Resolution: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT} (9:16)")
        print(f"🎞️  Frame rate: {FPS} FPS")
        print(f"🎵 Audio: Included and synced!")
    else:
        print(f"❌ Error: {result.stderr}")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


if __name__ == "__main__":
    export_tiktok_video()
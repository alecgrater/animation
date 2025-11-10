"""Configuration constants for the animation."""

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Character settings
CHARACTER_WIDTH = 40
CHARACTER_HEIGHT = 60
CHARACTER_SPEED = 3
HEAD_RADIUS = 20
EYE_SIZE = 3

# Audio settings
AUDIO_SAMPLE_RATE = 22050
AUDIO_BUFFER_SIZE = 512
WALKING_SOUND_FREQUENCY = 200
WALKING_SOUND_DURATION = 0.1

# Animation timing (in milliseconds)
COLLISION_DIALOGUE_DURATION = 2000
KIDDING_DIALOGUE_DURATION = 3000
HEY_YA_DIALOGUE_DURATION = 2000
COLLISION_LOOP_DURATION = 6000
FINAL_DIALOGUE_1_DURATION = 2500
FINAL_DIALOGUE_2_DURATION = 2000

# Walking sound intervals (in milliseconds)
WALKING_SOUND_INTERVAL = 300
COLLISION_LOOP_SOUND_INTERVAL = 200

# Apple Floodgate authentication
APPLE_CONNECT_COMMAND = (
    '/usr/local/bin/appleconnect getToken '
    '-C hvys3fcwcteqrvw3qzkvtk86viuoqv '
    '--token-type=oauth '
    '--interactivity-type=none '
    '-E prod '
    '-G pkce '
    '-o openid,dsid,accountname,profile,groups'
)
FLOODGATE_BASE_URL = 'https://floodgate.g.apple.com/api/openai/v1'
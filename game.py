import pygame
import os
import random
import math
import cv2
import numpy as np
from hand_tracking import HandTracker

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Game Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
CYAN = (0, 255, 255)
GOLD = (255, 215, 0)
ORANGE = (255, 140, 0)
GREEN = (46, 139, 87)
NEON_GREEN = (57, 255, 20)
GRAY = (128, 128, 128)

# Set up Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gesture Fruit Ninja")
clock = pygame.time.Clock()

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

# Load Sound Effects helper
def load_sound(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    print(f"Warning: Sound {filename} not found.")
    return None

# Load Sound Effects
slice_sound = load_sound("slice.wav")
splatter_sound = load_sound("splatter.wav")
explosion_sound = load_sound("explosion.wav")
game_over_sound = load_sound("game_over.wav")

# Set channels/volumes
if slice_sound: slice_sound.set_volume(0.4)
if splatter_sound: splatter_sound.set_volume(0.5)
if explosion_sound: explosion_sound.set_volume(0.7)
if game_over_sound: game_over_sound.set_volume(0.6)

# Load Font Helper
def get_font(size, bold=False):
    try:
        # Try to use standard clean Windows fonts
        return pygame.font.SysFont("Segoe UI", size, bold=bold)
    except:
        return pygame.font.Font(None, size)

# Initialize Fonts
font_title = get_font(72, bold=True)
font_subtitle = get_font(28)
font_hud = get_font(36, bold=True)
font_large = get_font(48, bold=True)
font_floating = get_font(24, bold=True)

# Helper: Load transparent game sprite
def load_game_sprite(filename, scale_to=None):
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        print(f"Error: Sprite {filename} not found.")
        # Return a colored placeholder surface if asset missing
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        surf.fill(RED)
        return surf
        
    img = pygame.image.load(path).convert_alpha()
    
    if scale_to:
        img = pygame.transform.smoothscale(img, scale_to)
    return img

# Helper: Draw transparent circle in Pygame
def draw_transparent_circle(surface, color, center, radius):
    if radius <= 0:
        return
    temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(temp_surf, color, (radius, radius), radius)
    surface.blit(temp_surf, (center[0] - radius, center[1] - radius))

# Split sprite in half for cut fruit effect
def split_sprite_in_half(surface):
    w, h = surface.get_size()
    half_w = w // 2
    
    # Left Half
    left_surf = pygame.Surface((half_w, h), pygame.SRCALPHA)
    left_surf.blit(surface, (0, 0), (0, 0, half_w, h))
    
    # Right Half
    right_surf = pygame.Surface((half_w, h), pygame.SRCALPHA)
    right_surf.blit(surface, (0, 0), (half_w, 0, half_w, h))
    
    return left_surf, right_surf

# Load High Score
def get_high_score():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception as e:
        print(f"Error saving high score: {e}")

# Classes
class Fruit:
    def __init__(self, fruit_type, image, radius, color, splatter_color, points):
        self.type = fruit_type
        self.image = image
        self.radius = radius
        self.color = color
        self.splatter_color = splatter_color
        self.points = points
        
        # Start below screen
        self.x = random.randint(150, SCREEN_WIDTH - 150)
        self.y = SCREEN_HEIGHT + radius
        
        # Physics variables
        # Set launch speeds: fly towards middle/center
        self.vx = random.randint(-4, 4)
        if self.x < SCREEN_WIDTH // 3:
            self.vx = random.randint(2, 6)
        elif self.x > 2 * SCREEN_WIDTH // 3:
            self.vx = random.randint(-6, -2)
            
        # Vertical launch velocity
        self.vy = random.randint(-18, -14)
        
        # Rotation
        self.angle = 0
        self.v_angle = random.randint(-6, 6)
        if self.v_angle == 0: self.v_angle = 2
        
        # Sliced state
        self.is_sliced = False
        self.left_half = None
        self.right_half = None
        self.left_x, self.left_y = 0, 0
        self.right_x, self.right_y = 0, 0
        self.left_vx, self.left_vy = 0, 0
        self.right_vx, self.right_vy = 0, 0
        
        # Gravity toggle (disable for stationary menu elements)
        self.gravity_enabled = True
        
    def update(self, gravity):
        if not self.is_sliced:
            # Move whole fruit
            if self.gravity_enabled:
                self.x += self.vx
                self.y += self.vy
                self.vy += gravity
            self.angle += self.v_angle
        else:
            # Move halves apart
            self.left_x += self.left_vx
            self.left_y += self.left_vy
            self.left_vy += gravity * 1.2  # Halves fall slightly faster
            
            self.right_x += self.right_vx
            self.right_y += self.right_vy
            self.right_vy += gravity * 1.2
            
            self.angle += self.v_angle
            
    def draw(self, surface):
        if not self.is_sliced:
            # Rotate whole image
            rotated_img = pygame.transform.rotate(self.image, self.angle)
            rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated_img, rect.topleft)
        else:
            # Draw left half
            rotated_left = pygame.transform.rotate(self.left_half, self.angle)
            rect_left = rotated_left.get_rect(center=(int(self.left_x), int(self.left_y)))
            surface.blit(rotated_left, rect_left.topleft)
            
            # Draw right half
            rotated_right = pygame.transform.rotate(self.right_half, -self.angle)
            rect_right = rotated_right.get_rect(center=(int(self.right_x), int(self.right_y)))
            surface.blit(rotated_right, rect_right.topleft)

    def slice_fruit(self):
        self.is_sliced = True
        # Split original sprite in two
        left, right = split_sprite_in_half(self.image)
        self.left_half = left
        self.right_half = right
        
        # Position halves initially at the center
        self.left_x, self.left_y = self.x - self.radius // 3, self.y
        self.right_x, self.right_y = self.x + self.radius // 3, self.y
        
        # Give ejection velocities
        self.left_vx = self.vx - random.uniform(3, 6)
        self.left_vy = self.vy - random.uniform(2, 4)
        
        self.right_vx = self.vx + random.uniform(3, 6)
        self.right_vy = self.vy - random.uniform(2, 4)


class Bomb:
    def __init__(self, image, radius):
        self.image = image
        self.radius = radius
        
        self.x = random.randint(150, SCREEN_WIDTH - 150)
        self.y = SCREEN_HEIGHT + radius
        
        self.vx = random.randint(-3, 3)
        if self.x < SCREEN_WIDTH // 3:
            self.vx = random.randint(2, 5)
        elif self.x > 2 * SCREEN_WIDTH // 3:
            self.vx = random.randint(-5, -2)
            
        self.vy = random.randint(-17, -13)
        self.angle = 0
        self.v_angle = random.randint(-4, 4)
        if self.v_angle == 0: self.v_angle = 2
        
    def update(self, gravity):
        self.x += self.vx
        self.y += self.vy
        self.vy += gravity
        self.angle += self.v_angle
        
    def draw(self, surface):
        rotated_img = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_img, rect.topleft)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(4, 10)
        
        # Shoot out radially
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.alpha = 255
        self.decay = random.randint(4, 8)
        
    def update(self, gravity):
        self.x += self.vx
        self.y += self.vy
        self.vy += gravity
        self.alpha -= self.decay
        
    def draw(self, surface):
        if self.alpha > 0:
            c = (self.color[0], self.color[1], self.color[2], self.alpha)
            draw_transparent_circle(surface, c, (int(self.x), int(self.y)), self.radius)


class FloatingText:
    def __init__(self, text, x, y, color, font=font_floating):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        
        self.vy = -2.0  # Drift upwards
        self.vx = random.uniform(-1.0, 1.0)
        self.alpha = 255
        self.decay = 5
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay
        
    def draw(self, surface):
        if self.alpha > 0:
            txt_surf = self.font.render(self.text, True, self.color)
            # Apply alpha fade using surface blitting
            txt_surf_alpha = txt_surf.copy()
            alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, self.alpha))
            txt_surf_alpha.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            rect = txt_surf_alpha.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(txt_surf_alpha, rect.topleft)


# Math Helper: Distance from Point to Line Segment
def distance_point_to_segment(cx, cy, ax, ay, bx, by):
    # Vector AB
    abx = bx - ax
    aby = by - ay
    # Vector AC
    acx = cx - ax
    acy = cy - ay
    
    # Project C onto segment AB
    ab_len_sq = abx**2 + aby**2
    if ab_len_sq == 0:
        # A and B are the same point
        return math.sqrt(acx**2 + acy**2)
        
    t = (acx * abx + acy * aby) / ab_len_sq
    t = max(0, min(1, t))  # Clamp to segment
    
    # Closest point coordinates
    px = ax + t * abx
    py = ay + t * aby
    
    # Return distance
    return math.sqrt((cx - px)**2 + (cy - py)**2)


# Main Game Class
class Game:
    def __init__(self):
        # Load Background Dojo Wall
        self.bg_image = pygame.image.load(os.path.join(ASSETS_DIR, "dojo_background.png")).convert()
        self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Load sprites
        self.fruit_sprites = {
            "watermelon": load_game_sprite("watermelon.png", (95, 95)),
            "apple": load_game_sprite("apple.png", (80, 80)),
            "banana": load_game_sprite("banana.png", (90, 90)),
            "orange": load_game_sprite("orange.png", (80, 80)),
            "pineapple": load_game_sprite("pineapple.png", (85, 95))
        }
        self.bomb_sprite = load_game_sprite("bomb.png", (90, 110))
        
        # Setup Hand Tracker
        self.tracker = HandTracker(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.mouse_mode = not self.tracker.has_webcam
        
        # Persistent Background Splatter Surface (juice overlay on wall)
        self.juice_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Leaderboard state
        self.high_score = get_high_score()
        
        # Menu state
        self.state = "START_MENU"
        self.difficulty = "Medium"  # Default
        
        # Difficulty Selectors (buttons) Rects
        self.easy_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 300, 140, 50)
        self.medium_rect = pygame.Rect(SCREEN_WIDTH // 2 - 70, 300, 140, 50)
        self.hard_rect = pygame.Rect(SCREEN_WIDTH // 2 + 110, 300, 140, 50)
        
        # Fruit properties map (radius, color, splatter_color, points)
        self.fruit_configs = {
            "watermelon": (45, GREEN, RED, 1),
            "apple": (38, RED, (255, 250, 205), 1),
            "banana": (42, GOLD, (255, 253, 208), 1),
            "orange": (38, ORANGE, (255, 220, 100), 1),
            "pineapple": (40, (218, 165, 32), (255, 255, 200), 2)
        }
        
        # Active entities
        self.fruits = []
        self.bombs = []
        self.particles = []
        self.floating_texts = []
        
        # Blade trail
        self.trail = []
        self.max_trail_len = 12
        
        # Scoring & Lives
        self.score = 0
        self.lives = 3
        self.combos_sliced_this_frame = 0
        
        # Spawning Engine variables
        self.spawn_timer = 0
        
        # Menu interactive watermelons
        self.menu_watermelon = None
        self.retry_watermelon = None
        self.setup_menu_watermelon()
        
        # Flash visual feedback
        self.flash_alpha = 0
        
        # Screen shake
        self.shake_timer = 0
        self.shake_intensity = 0
        
    def setup_menu_watermelon(self):
        # Spinning watermelon in start screen to slice to start
        img = self.fruit_sprites["watermelon"]
        self.menu_watermelon = Fruit("watermelon", img, 50, GREEN, RED, 1)
        self.menu_watermelon.gravity_enabled = False
        self.menu_watermelon.x = SCREEN_WIDTH // 2
        self.menu_watermelon.y = SCREEN_HEIGHT // 2 + 100
        self.menu_watermelon.vx = 0
        self.menu_watermelon.vy = 0
        self.menu_watermelon.v_angle = 3
        
    def setup_retry_watermelon(self):
        img = self.fruit_sprites["watermelon"]
        self.retry_watermelon = Fruit("watermelon", img, 50, GREEN, RED, 1)
        self.retry_watermelon.gravity_enabled = False
        self.retry_watermelon.x = SCREEN_WIDTH // 2
        self.retry_watermelon.y = SCREEN_HEIGHT // 2 + 150
        self.retry_watermelon.vx = 0
        self.retry_watermelon.vy = 0
        self.retry_watermelon.v_angle = 3

    def get_difficulty_settings(self):
        if self.difficulty == "Easy":
            return {"gravity": 0.23, "spawn_freq": 110, "bomb_prob": 0.08, "lives": 3, "hard_bomb": False}
        elif self.difficulty == "Medium":
            return {"gravity": 0.30, "spawn_freq": 85, "bomb_prob": 0.18, "lives": 3, "hard_bomb": False}
        else: # Hard
            return {"gravity": 0.40, "spawn_freq": 60, "bomb_prob": 0.32, "lives": 3, "hard_bomb": True}

    def reset_game(self):
        self.fruits.clear()
        self.bombs.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.juice_surface.fill((0, 0, 0, 0)) # Clear juice paint splats
        self.trail.clear()
        self.score = 0
        self.lives = self.get_difficulty_settings()["lives"]
        # Trigger immediate spawn by setting spawn_timer equal to spawn_freq
        self.spawn_timer = self.get_difficulty_settings()["spawn_freq"]
        self.flash_alpha = 0
        self.shake_timer = 0
        self.shake_intensity = 0

    def trigger_explosion(self):
        if explosion_sound:
            explosion_sound.play()
        self.flash_alpha = 255
        self.shake_timer = 30
        self.shake_intensity = 15
        
        # Spawn massive particle blast
        for _ in range(80):
            p = Particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, (255, 200, 50))
            # Increase explosion velocity
            p.vx *= 2.5
            p.vy *= 2.5
            self.particles.append(p)
            
        settings = self.get_difficulty_settings()
        if settings["hard_bomb"]:
            self.lives = 0
            self.floating_texts.append(FloatingText("BOMB EXPLOSED! GAME OVER!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, RED, font_large))
        else:
            self.lives -= 1
            self.score = max(0, self.score - 10)
            self.floating_texts.append(FloatingText("-1 LIFE! -10 PTS", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, RED, font_large))

    def trigger_slice_juice(self, x, y, color):
        # Add background permanent splats
        for _ in range(8):
            rad = random.randint(8, 25)
            # Offset around slash
            ox = x + random.randint(-40, 40)
            oy = y + random.randint(-40, 40)
            c = (color[0], color[1], color[2], random.randint(120, 200))
            pygame.draw.circle(self.juice_surface, c, (ox, oy), rad)
            
            # Draw minor drip splatters
            for _ in range(2):
                drip_ox = ox + random.randint(-15, 15)
                drip_oy = oy + random.randint(10, 45)
                drip_rad = random.randint(3, 8)
                pygame.draw.circle(self.juice_surface, c, (drip_ox, drip_oy), drip_rad)

    def spawn_items(self):
        settings = self.get_difficulty_settings()
        num_items = random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10])[0]
        
        for _ in range(num_items):
            # Choose whether to spawn bomb or fruit
            if random.random() < settings["bomb_prob"]:
                # Spawn Bomb
                bomb = Bomb(self.bomb_sprite, 45)
                self.bombs.append(bomb)
            else:
                # Spawn Fruit
                fruit_name = random.choice(list(self.fruit_sprites.keys()))
                img = self.fruit_sprites[fruit_name]
                radius, color, splatter_color, pts = self.fruit_configs[fruit_name]
                fruit = Fruit(fruit_name, img, radius, color, splatter_color, pts)
                self.fruits.append(fruit)

    def handle_collisions(self):
        if len(self.trail) < 2:
            return
            
        ax, ay = self.trail[-2]
        bx, by = self.trail[-1]
        
        # Check if line segment AB sliced any fruit/bomb
        settings = self.get_difficulty_settings()
        sliced_fruits = []
        
        # 1. Check Menu Watermelons
        if self.state == "START_MENU" and self.menu_watermelon and not self.menu_watermelon.is_sliced:
            dist = distance_point_to_segment(self.menu_watermelon.x, self.menu_watermelon.y, ax, ay, bx, by)
            if dist < self.menu_watermelon.radius:
                self.menu_watermelon.slice_fruit()
                if slice_sound: slice_sound.play()
                if splatter_sound: splatter_sound.play()
                self.trigger_slice_juice(self.menu_watermelon.x, self.menu_watermelon.y, RED)
                # Spawn splatter particles
                for _ in range(25):
                    self.particles.append(Particle(self.menu_watermelon.x, self.menu_watermelon.y, RED))
                # Move to playing state after a small delay to see split animation
                self.state = "TRANSITION_TO_PLAY"
                self.spawn_timer = 50 # Timer before game starts (50 frames)
                
        elif self.state == "GAME_OVER" and self.retry_watermelon and not self.retry_watermelon.is_sliced:
            dist = distance_point_to_segment(self.retry_watermelon.x, self.retry_watermelon.y, ax, ay, bx, by)
            if dist < self.retry_watermelon.radius:
                self.retry_watermelon.slice_fruit()
                if slice_sound: slice_sound.play()
                if splatter_sound: splatter_sound.play()
                self.trigger_slice_juice(self.retry_watermelon.x, self.retry_watermelon.y, RED)
                for _ in range(25):
                    self.particles.append(Particle(self.retry_watermelon.x, self.retry_watermelon.y, RED))
                self.state = "TRANSITION_TO_PLAY"
                self.spawn_timer = 50
                
        # 2. Check Active Gameplay Fruits
        elif self.state == "PLAYING":
            # Fruits slicing check
            for fruit in self.fruits:
                if not fruit.is_sliced:
                    dist = distance_point_to_segment(fruit.x, fruit.y, ax, ay, bx, by)
                    if dist < fruit.radius:
                        fruit.slice_fruit()
                        sliced_fruits.append(fruit)
                        
            # Bombs slicing check
            bombs_to_remove = []
            for bomb in self.bombs:
                dist = distance_point_to_segment(bomb.x, bomb.y, ax, ay, bx, by)
                if dist < bomb.radius:
                    self.trigger_explosion()
                    bombs_to_remove.append(bomb)
            for b in bombs_to_remove:
                self.bombs.remove(b)

            # Process sliced fruits
            if len(sliced_fruits) > 0:
                if slice_sound:
                    slice_sound.play()
                if splatter_sound:
                    splatter_sound.play()
                
                combo_points = 0
                for f in sliced_fruits:
                    combo_points += f.points
                    # Spawn splatter particles
                    for _ in range(20):
                        self.particles.append(Particle(f.x, f.y, f.splatter_color))
                    self.trigger_slice_juice(f.x, f.y, f.splatter_color)
                
                # Combo Scoring
                num_sliced = len(sliced_fruits)
                if num_sliced >= 2:
                    bonus = num_sliced
                    total_pts = combo_points + bonus
                    self.score += total_pts
                    
                    # Floating text
                    combo_desc = f"{num_sliced}x COMBO! +{total_pts}"
                    self.floating_texts.append(FloatingText(combo_desc, sliced_fruits[0].x, sliced_fruits[0].y - 30, GOLD, font_hud))
                else:
                    self.score += combo_points
                    self.floating_texts.append(FloatingText(f"+{combo_points}", sliced_fruits[0].x, sliced_fruits[0].y - 30, WHITE, font_hud))

    def update(self):
        settings = self.get_difficulty_settings()
        
        # 1. Update Shake & Flash effects
        if self.shake_timer > 0:
            self.shake_timer -= 1
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 10)
            
        # 2. Update Interactive Menu Fruits
        if self.state in ["START_MENU", "TRANSITION_TO_PLAY"] and self.menu_watermelon:
            self.menu_watermelon.update(settings["gravity"])
        if self.state in ["GAME_OVER", "TRANSITION_TO_PLAY"] and self.retry_watermelon:
            self.retry_watermelon.update(settings["gravity"])
            
        # 3. Update active gameplay items
        if self.state == "PLAYING":
            # Timer Spawning
            self.spawn_timer += 1
            if self.spawn_timer >= settings["spawn_freq"]:
                self.spawn_timer = 0
                self.spawn_items()
                
            # Update fruits
            fruits_to_keep = []
            for fruit in self.fruits:
                fruit.update(settings["gravity"])
                
                # Check for missed whole fruits falling out
                if not fruit.is_sliced and fruit.y > SCREEN_HEIGHT + fruit.radius + 50 and fruit.vy > 0:
                    # Missed fruit: Deduct life/strike
                    self.lives -= 1
                    if self.lives > 0:
                        self.floating_texts.append(FloatingText("MISS!", fruit.x, SCREEN_HEIGHT - 30, RED, font_hud))
                    # If game over, trigger sound
                    if self.lives <= 0:
                        if game_over_sound: game_over_sound.play()
                        self.state = "GAME_OVER"
                        self.setup_retry_watermelon()
                        if self.score > self.high_score:
                            self.high_score = self.score
                            save_high_score(self.high_score)
                # Keep if it is sliced (halves are falling) or if it's still visible
                elif fruit.y < SCREEN_HEIGHT + 200:
                    fruits_to_keep.append(fruit)
            self.fruits = fruits_to_keep
            
            # Update bombs
            bombs_to_keep = []
            for bomb in self.bombs:
                bomb.update(settings["gravity"])
                if bomb.y < SCREEN_HEIGHT + bomb.radius + 50:
                    bombs_to_keep.append(bomb)
            self.bombs = bombs_to_keep
            
        elif self.state == "TRANSITION_TO_PLAY":
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.reset_game()
                self.state = "PLAYING"
                
        # 4. Update particles
        particles_to_keep = []
        for p in self.particles:
            p.update(settings["gravity"])
            if p.alpha > 0 and p.y < SCREEN_HEIGHT + 100:
                particles_to_keep.append(p)
        self.particles = particles_to_keep
        
        # 5. Update floating texts
        texts_to_keep = []
        for txt in self.floating_texts:
            txt.update()
            if txt.alpha > 0:
                texts_to_keep.append(txt)
        self.floating_texts = texts_to_keep

    def draw_blade_trail(self, surface):
        if len(self.trail) < 2:
            return
            
        # Draw neon glowing line trail
        # Overlap lines with decreasing opacity and thickness
        for i in range(1, len(self.trail)):
            p1 = self.trail[i-1]
            p2 = self.trail[i]
            
            # Calculate width based on position (tapering trail)
            progress = i / len(self.trail)
            core_width = int(3 * progress) + 1
            glow_width = int(9 * progress) + 2
            outer_width = int(16 * progress) + 3
            
            # Transparencies (alpha)
            alpha_glow = int(120 * progress)
            alpha_outer = int(60 * progress)
            
            # Draw outer glow
            draw_transparent_circle(surface, (0, 191, 255, alpha_outer), p2, outer_width)
            pygame.draw.line(surface, (0, 191, 255), p1, p2, outer_width)
            
            # Draw inner neon glow
            draw_transparent_circle(surface, (0, 255, 255, alpha_glow), p2, glow_width)
            pygame.draw.line(surface, (0, 255, 255), p1, p2, glow_width)
            
            # Draw bright core
            pygame.draw.line(surface, WHITE, p1, p2, core_width)

    def draw_hud(self, surface):
        # Draw score
        score_surf = font_hud.render(f"SCORE: {self.score}", True, WHITE)
        surface.blit(score_surf, (20, 20))
        
        # Draw high score
        hs_surf = font_subtitle.render(f"HIGH: {self.high_score}", True, GOLD)
        surface.blit(hs_surf, (20, 60))
        
        # Draw Lives (X's)
        # 3 strikes layout
        strike_start_x = SCREEN_WIDTH - 150
        strike_y = 25
        for i in range(3):
            # Check if this life is lost
            is_lost = i >= self.lives
            color = RED if is_lost else NEON_GREEN
            txt = "X" if is_lost else "O"
            
            strike_surf = font_hud.render(txt, True, color)
            surface.blit(strike_surf, (strike_start_x + i * 40, strike_y))
            
        # Draw Difficulty Overlay
        diff_txt = f"Difficulty: {self.difficulty}"
        diff_surf = font_subtitle.render(diff_txt, True, WHITE)
        surface.blit(diff_surf, (SCREEN_WIDTH // 2 - diff_surf.get_width() // 2, 20))

        # Show input mode
        mode_txt = "Input: Mouse (Fall back)" if self.mouse_mode else "Input: Hand Gestures (Webcam)"
        mode_color = GRAY if self.mouse_mode else NEON_GREEN
        mode_surf = get_font(18).render(mode_txt, True, mode_color)
        surface.blit(mode_surf, (20, SCREEN_HEIGHT - 30))

    def draw_start_menu(self, surface):
        # Elegant Dark Glassmorphism Menu
        menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        menu_bg.fill((15, 15, 25, 180)) # Sleek dark blue tint with transparency
        surface.blit(menu_bg, (0, 0))
        
        # Title
        title_surf = font_title.render("GESTURE NINJA", True, WHITE)
        # Add glow
        title_glow = font_title.render("GESTURE NINJA", True, CYAN)
        surface.blit(title_glow, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + 2, 102))
        surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
        
        if self.state != "TRANSITION_TO_PLAY":
            desc_surf = font_subtitle.render("Move hands in air to slice! Don't touch bombs!", True, GOLD)
            surface.blit(desc_surf, (SCREEN_WIDTH // 2 - desc_surf.get_width() // 2, 180))
            
            # Draw Difficulty buttons
            for r, text, diff_lvl in [(self.easy_rect, "EASY", "Easy"), 
                                       (self.medium_rect, "MEDIUM", "Medium"), 
                                       (self.hard_rect, "HARD", "Hard")]:
                is_active = self.difficulty == diff_lvl
                bg_color = (0, 200, 200, 100) if is_active else (255, 255, 255, 20)
                border_color = CYAN if is_active else WHITE
                
                # Glass container
                btn_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
                btn_surf.fill(bg_color)
                pygame.draw.rect(btn_surf, border_color, (0, 0, r.width, r.height), 2, border_radius=10)
                
                txt_surf = font_subtitle.render(text, True, border_color)
                btn_surf.blit(txt_surf, (r.width // 2 - txt_surf.get_width() // 2, r.height // 2 - txt_surf.get_height() // 2))
                surface.blit(btn_surf, r.topleft)
            
        # Draw Spinning Start Watermelon
        if self.menu_watermelon:
            self.menu_watermelon.draw(surface)
            if self.state != "TRANSITION_TO_PLAY":
                # Text around watermelon
                start_txt = font_hud.render("SLICE TO START", True, NEON_GREEN)
                surface.blit(start_txt, (SCREEN_WIDTH // 2 - start_txt.get_width() // 2, SCREEN_HEIGHT // 2 + 180))
            
        if self.state != "TRANSITION_TO_PLAY":
            # Show mode message
            if self.mouse_mode:
                fallback_surf = font_subtitle.render("No camera found - Play with your mouse!", True, RED)
                surface.blit(fallback_surf, (SCREEN_WIDTH // 2 - fallback_surf.get_width() // 2, SCREEN_HEIGHT - 60))
            else:
                cam_surf = font_subtitle.render("Camera initialized. Place hand in view.", True, NEON_GREEN)
                surface.blit(cam_surf, (SCREEN_WIDTH // 2 - cam_surf.get_width() // 2, SCREEN_HEIGHT - 60))

    def draw_game_over(self, surface):
        menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        menu_bg.fill((25, 5, 5, 210)) # Dark reddish glass tint
        surface.blit(menu_bg, (0, 0))
        
        go_surf = font_title.render("GAME OVER", True, RED)
        surface.blit(go_surf, (SCREEN_WIDTH // 2 - go_surf.get_width() // 2, 100))
        
        if self.state != "TRANSITION_TO_PLAY":
            score_surf = font_large.render(f"FINAL SCORE: {self.score}", True, WHITE)
            surface.blit(score_surf, (SCREEN_WIDTH // 2 - score_surf.get_width() // 2, 200))
            
            # High Score notice
            if self.score >= self.high_score and self.score > 0:
                hs_txt = "NEW HIGH SCORE!"
                hs_color = GOLD
            else:
                hs_txt = f"HIGH SCORE: {self.high_score}"
                hs_color = GRAY
            hs_surf = font_subtitle.render(hs_txt, True, hs_color)
            surface.blit(hs_surf, (SCREEN_WIDTH // 2 - hs_surf.get_width() // 2, 260))
        
        # Spinning Retry Watermelon
        if self.retry_watermelon:
            self.retry_watermelon.draw(surface)
            if self.state != "TRANSITION_TO_PLAY":
                retry_txt = font_hud.render("SLICE TO RETRY", True, NEON_GREEN)
                surface.blit(retry_txt, (SCREEN_WIDTH // 2 - retry_txt.get_width() // 2, SCREEN_HEIGHT // 2 + 230))
            
        if self.state != "TRANSITION_TO_PLAY":
            # Hover slice info
            hover_txt = font_subtitle.render("Hover or slice difficulty button to select, slice fruit to restart", True, WHITE)
            surface.blit(hover_txt, (SCREEN_WIDTH // 2 - hover_txt.get_width() // 2, SCREEN_HEIGHT - 60))

    def render(self):
        # 1. Background Dojo
        # Apply screen shake offsets
        offset_x, offset_y = 0, 0
        if self.shake_timer > 0:
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            
        screen.blit(self.bg_image, (offset_x, offset_y))
        
        # 2. Permanent background juice paint
        screen.blit(self.juice_surface, (offset_x, offset_y))
        
        # 3. Draw active elements
        for fruit in self.fruits:
            fruit.draw(screen)
            
        for bomb in self.bombs:
            bomb.draw(screen)
            
        for p in self.particles:
            p.draw(screen)
            
        for txt in self.floating_texts:
            txt.draw(screen)
            
        # 4. Blade trail
        self.draw_blade_trail(screen)
        
        # 5. Renders according to state
        if self.state == "START_MENU":
            self.draw_start_menu(screen)
        elif self.state == "TRANSITION_TO_PLAY":
            if self.retry_watermelon and self.retry_watermelon.is_sliced:
                self.draw_game_over(screen)
            else:
                self.draw_start_menu(screen)
        elif self.state == "PLAYING":
            self.draw_hud(screen)
        elif self.state == "GAME_OVER":
            self.draw_game_over(screen)
            
        # 6. Webcam overlay (PiP) in bottom-right
        if not self.mouse_mode:
            # We get the processed PiP camera frame from the tracker loop
            pass
            
        # 7. Red Screen Flash (when hitting bomb)
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill(RED)
            flash_surf.set_alpha(self.flash_alpha)
            screen.blit(flash_surf, (0, 0))

    def check_menu_clicks(self, pos):
        # Slice/hover over buttons check (especially for difficulty settings in main menu)
        if self.state in ["START_MENU"]:
            if self.easy_rect.collidepoint(pos):
                self.difficulty = "Easy"
            elif self.medium_rect.collidepoint(pos):
                self.difficulty = "Medium"
            elif self.hard_rect.collidepoint(pos):
                self.difficulty = "Hard"
                
        # Click/hover watermelon check to double-ensure game starts
        if self.state == "START_MENU" and self.menu_watermelon and not self.menu_watermelon.is_sliced:
            dist = math.sqrt((pos[0] - self.menu_watermelon.x)**2 + (pos[1] - self.menu_watermelon.y)**2)
            if dist < self.menu_watermelon.radius:
                self.menu_watermelon.slice_fruit()
                if slice_sound: slice_sound.play()
                if splatter_sound: splatter_sound.play()
                self.trigger_slice_juice(self.menu_watermelon.x, self.menu_watermelon.y, RED)
                for _ in range(25):
                    self.particles.append(Particle(self.menu_watermelon.x, self.menu_watermelon.y, RED))
                self.state = "TRANSITION_TO_PLAY"
                self.spawn_timer = 50
                
        elif self.state == "GAME_OVER" and self.retry_watermelon and not self.retry_watermelon.is_sliced:
            dist = math.sqrt((pos[0] - self.retry_watermelon.x)**2 + (pos[1] - self.retry_watermelon.y)**2)
            if dist < self.retry_watermelon.radius:
                self.retry_watermelon.slice_fruit()
                if slice_sound: slice_sound.play()
                if splatter_sound: splatter_sound.play()
                self.trigger_slice_juice(self.retry_watermelon.x, self.retry_watermelon.y, RED)
                for _ in range(25):
                    self.particles.append(Particle(self.retry_watermelon.x, self.retry_watermelon.y, RED))
                self.state = "TRANSITION_TO_PLAY"
                self.spawn_timer = 50

    def run(self):
        running = True
        
        while running:
            # Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r: # Emergency Reset key
                        self.reset_game()
                        self.state = "START_MENU"
                        self.setup_menu_watermelon()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.mouse_mode:
                        self.check_menu_clicks(pygame.mouse.get_pos())
            
            # Fetch hand tracking position / camera surface
            hand_pos, cam_surface = self.tracker.get_frame()
            
            # Hybrid inputs: Accept hand position if visible, fallback/dual track mouse
            active_pos = None
            if hand_pos is not None:
                active_pos = hand_pos
            else:
                # Track mouse when moving
                mouse_pos = pygame.mouse.get_pos()
                if len(self.trail) == 0 or mouse_pos != self.trail[-1]:
                    active_pos = mouse_pos
            
            if active_pos is not None:
                # Add coordinate to trail
                self.trail.append(active_pos)
                if len(self.trail) > self.max_trail_len:
                    self.trail.pop(0)
                
                # Check clicks or hovers
                self.check_menu_clicks(active_pos)
            else:
                # Decay trail
                if len(self.trail) > 0:
                    self.trail.pop(0)
            
            # Physics updates
            self.update()
            
            # Slicing collisions check
            self.handle_collisions()
            
            # Render screen
            self.render()
            
            # Render PiP Camera Overlay (bottom-right corner)
            if cam_surface is not None:
                # Scale border
                pip_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 170, 200, 150)
                pygame.draw.rect(screen, CYAN, pip_rect.inflate(4, 4), 2, border_radius=6)
                screen.blit(cam_surface, pip_rect.topleft)
                
            pygame.display.flip()
            clock.tick(FPS)
            
        # Clean up resources
        self.tracker.release()
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()

import pygame
import random
import sys
from enum import Enum
import math
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 800  # Increased window size
GRID_SIZE = 20
GRID_COUNT = WINDOW_SIZE // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SNAKE_GREEN = (46, 204, 113)
SNAKE_OUTLINE = (39, 174, 96)
FOOD_RED = (231, 76, 60)
FOOD_GOLD = (241, 196, 15)
FOOD_PURPLE = (155, 89, 182)
FOOD_BLUE = (52, 152, 219)
BACKGROUND_COLOR = (44, 62, 80)
GRID_COLOR = (52, 73, 94)
OBSTACLE_COLOR = (149, 165, 166)
PORTAL_COLOR = (142, 68, 173)
MENU_HIGHLIGHT = (52, 152, 219)  # Light blue highlight
MENU_SELECTED = (46, 204, 113)   # Green for selected item
MENU_HOVER = (41, 128, 185)      # Darker blue for hover

class GameMode(Enum):
    CLASSIC = "Classic"
    MAZE = "Maze"
    TIME_TRIAL = "Time Trial"
    PORTAL = "Portal"

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class PowerUpType(Enum):
    GHOST = "Ghost Mode"
    SHIELD = "Shield"
    DOUBLE_POINTS = "Double Points"
    SLOW_TIME = "Slow Time"

class FoodType:
    def __init__(self, color, points, probability, effect=None):
        self.color = color
        self.points = points
        self.probability = probability
        self.effect = effect

class Food:
    def __init__(self, position, food_type):
        self.position = position
        self.type = food_type
        self.animation_counter = random.uniform(0, 2 * math.pi)

class PowerUp:
    def __init__(self, position, type):
        self.position = position
        self.type = type
        self.duration = 300  # 10 seconds at 30 FPS
        self.animation_counter = 0

class Portal:
    def __init__(self, entrance, exit):
        self.entrance = entrance
        self.exit = exit
        self.cooldown = 0

class SnakeGame:
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Snake Game")
        
        # Initialize fonts
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Initialize food types
        self.food_types = {
            'normal': FoodType(FOOD_RED, 10, 0.7),
            'bonus': FoodType(FOOD_GOLD, 20, 0.15),
            'special': FoodType(FOOD_PURPLE, 15, 0.1),
            'speed': FoodType(FOOD_BLUE, 5, 0.05)
        }
        
        # Initialize high scores
        self.high_scores = self.load_high_scores()
        
        # Initialize game state
        self.selected_mode = GameMode.CLASSIC
        self.game_mode = GameMode.CLASSIC
        self.in_menu = True
        self.game_over = False
        self.score = 0
        
        # Initialize snake and game elements
        self.direction = Direction.RIGHT
        self.snake = []
        self.foods = []
        self.power_ups = []
        self.obstacles = []
        self.portals = []
        self.particles = []
        self.active_power_ups = {}
        self.game_speed = 10
        self.time_left = 60 * 30
        
        # Initialize game
        self.reset_game()

        # Add these new attributes
        self.selected_menu_item = 0
        self.menu_hover = -1

    def load_high_scores(self):
        # Initialize with default values
        return {mode: 0 for mode in GameMode}

    def save_high_score(self):
        if self.score > self.high_scores[self.game_mode]:
            self.high_scores[self.game_mode] = self.score

    def reset_game(self):
        # Store menu state
        current_mode = self.game_mode
        current_selected_mode = self.selected_mode
        current_in_menu = self.in_menu

        # Reset game elements
        self.direction = Direction.RIGHT
        center = GRID_COUNT//2
        self.snake = [(center-i, center) for i in range(3)]
        self.foods = []
        self.power_ups = []
        self.obstacles = []
        self.portals = []
        self.generate_foods(20)
        self.score = 0
        self.game_over = False
        self.particles = []
        self.active_power_ups = {}
        self.game_speed = 10
        self.time_left = 60 * 30

        # Restore menu state
        self.game_mode = current_mode
        self.selected_mode = current_selected_mode
        self.in_menu = current_in_menu

    def generate_maze(self):
        # Generate random maze-like obstacles
        self.obstacles = []
        for _ in range(GRID_COUNT * 2):
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            if pos not in self.snake and pos not in self.obstacles:
                self.obstacles.append(pos)
                
                # Sometimes create small wall segments
                if random.random() < 0.3:
                    for dx, dy in [(1,0), (0,1), (-1,0), (0,-1)]:
                        wall_pos = (pos[0] + dx, pos[1] + dy)
                        if (0 <= wall_pos[0] < GRID_COUNT and 
                            0 <= wall_pos[1] < GRID_COUNT and
                            wall_pos not in self.snake and
                            wall_pos not in self.obstacles):
                            self.obstacles.append(wall_pos)

    def generate_portals(self):
        # Generate pairs of portals
        for _ in range(2):
            while True:
                entrance = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
                exit = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
                if (entrance not in self.snake and exit not in self.snake and
                    entrance not in [p.entrance for p in self.portals] and
                    exit not in [p.exit for p in self.portals]):
                    self.portals.append(Portal(entrance, exit))
                    break

    def generate_power_up(self):
        if random.random() < 0.1 and len(self.power_ups) < 2:  # 10% chance, max 2 power-ups
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            if pos not in self.snake and pos not in [p.position for p in self.power_ups]:
                power_up_type = random.choice(list(PowerUpType))
                self.power_ups.append(PowerUp(pos, power_up_type))

    def handle_menu_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            
                # Menu navigation with arrow keys
                elif event.key == pygame.K_UP:
                    current_index = list(GameMode).index(self.selected_mode)
                    self.selected_mode = list(GameMode)[(current_index - 1) % len(GameMode)]
            
                elif event.key == pygame.K_DOWN:
                    current_index = list(GameMode).index(self.selected_mode)
                    self.selected_mode = list(GameMode)[(current_index + 1) % len(GameMode)]
            
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):  # Added SPACE key
                    self.game_mode = self.selected_mode
                    self.in_menu = False
                    self.reset_game()
        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check if clicked on any mode
                    mouse_pos = pygame.mouse.get_pos()
                    center_x = WINDOW_SIZE // 2
                    center_y = WINDOW_SIZE // 2
                    spacing = 60
                    
                    for i, mode in enumerate(GameMode):
                        # Calculate text rect for collision detection
                        text_surface = self.font.render(mode.value, True, WHITE)
                        text_rect = text_surface.get_rect(center=(center_x, center_y - 50 + i * spacing))
                        # Add padding to make clicking easier
                        click_rect = text_rect.inflate(40, 20)
                        
                        if click_rect.collidepoint(mouse_pos):
                            self.selected_mode = mode
                            self.game_mode = mode
                            self.in_menu = False
                            self.reset_game()
                            break

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Calculate center positions
        center_x = WINDOW_SIZE // 2
        center_y = WINDOW_SIZE // 2
        
        # Draw title
        title_font = pygame.font.Font(None, 74)
        title_surface = title_font.render("SNAKE GAME", True, WHITE)
        title_rect = title_surface.get_rect(center=(center_x, center_y - 200))
        self.screen.blit(title_surface, title_rect)
        
        # Draw mode options
        menu_font = pygame.font.Font(None, 48)
        spacing = 60
        
        for i, mode in enumerate(GameMode):
            text_color = WHITE
            bg_color = None
            padding = 20
            
            # Get text dimensions
            text_surface = menu_font.render(mode.value, True, text_color)
            text_rect = text_surface.get_rect(center=(center_x, center_y - 50 + i * spacing))
            
            # Check if mouse is hovering
            mouse_pos = pygame.mouse.get_pos()
            if text_rect.collidepoint(mouse_pos):
                bg_color = MENU_HOVER
            
            # Highlight selected mode
            if mode == self.selected_mode:
                bg_color = MENU_SELECTED
                # Draw selection indicator (arrow)
                arrow = "→ "
                arrow_surface = menu_font.render(arrow, True, WHITE)
                arrow_rect = arrow_surface.get_rect(right=text_rect.left - 10, centery=text_rect.centery)
                self.screen.blit(arrow_surface, arrow_rect)
            
            # Draw button background if needed
            if bg_color:
                bg_rect = text_rect.inflate(padding * 2, padding)
                pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=10)
            
            self.screen.blit(text_surface, text_rect)
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 32)
        instructions = [
            "Use up/down or mouse to select mode",
            "Press ENTER or click to start",
            "Press ESC to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text_surface = instruction_font.render(instruction, True, (200, 200, 200))
            text_rect = text_surface.get_rect(center=(center_x, WINDOW_SIZE - 150 + i * 30))
            self.screen.blit(text_surface, text_rect)

    def handle_power_up(self, power_up):
        if power_up.type == PowerUpType.GHOST:
            self.active_power_ups[PowerUpType.GHOST] = 300  # 10 seconds
        elif power_up.type == PowerUpType.SHIELD:
            self.active_power_ups[PowerUpType.SHIELD] = 300
        elif power_up.type == PowerUpType.DOUBLE_POINTS:
            self.active_power_ups[PowerUpType.DOUBLE_POINTS] = 300
        elif power_up.type == PowerUpType.SLOW_TIME:
            self.active_power_ups[PowerUpType.SLOW_TIME] = 300
            self.game_speed = 5

    def update_power_ups(self):
        for power_up_type in list(self.active_power_ups.keys()):
            self.active_power_ups[power_up_type] -= 1
            if self.active_power_ups[power_up_type] <= 0:
                del self.active_power_ups[power_up_type]
                if power_up_type == PowerUpType.SLOW_TIME:
                    self.game_speed = 10

    def handle_collision(self, new_head):
        # Check for portal transportation
        for portal in self.portals:
            if new_head == portal.entrance and portal.cooldown == 0:
                new_head = portal.exit
                portal.cooldown = 30  # Set cooldown to prevent immediate return
                self.create_particles(portal.entrance, PORTAL_COLOR)
                self.create_particles(portal.exit, PORTAL_COLOR)
                break

        # Update portal cooldowns
        for portal in self.portals:
            if portal.cooldown > 0:
                portal.cooldown -= 1

        # Check for collisions with obstacles or walls
        if (new_head[0] < 0 or new_head[0] >= GRID_COUNT or
            new_head[1] < 0 or new_head[1] >= GRID_COUNT or
            (new_head in self.obstacles and PowerUpType.GHOST not in self.active_power_ups) or
            (new_head in self.snake and PowerUpType.GHOST not in self.active_power_ups)):
            
            if PowerUpType.SHIELD in self.active_power_ups:
                del self.active_power_ups[PowerUpType.SHIELD]
                return True
            
            self.game_over = True
            self.save_high_score()
            self.create_particles(new_head, SNAKE_GREEN)
            return False
            
        return True

    def update(self):
        if self.game_over:
            self.update_particles()
            return

        # Update various timers and effects
        self.update_power_ups()
        self.generate_power_up()

        if self.game_mode == GameMode.TIME_TRIAL:
            self.time_left -= 1
            if self.time_left <= 0:
                self.game_over = True
                self.save_high_score()
                return

        # Update food animations
        for food in self.foods:
            food.animation_counter = (food.animation_counter + 0.1) % (2 * math.pi)

        head = self.snake[0]
        
        # Calculate new head position
        if self.direction == Direction.UP:
            new_head = (head[0], head[1] - 1)
        elif self.direction == Direction.DOWN:
            new_head = (head[0], head[1] + 1)
        elif self.direction == Direction.LEFT:
            new_head = (head[0] - 1, head[1])
        else:  # Direction.RIGHT
            new_head = (head[0] + 1, head[1])

        # Handle collisions
        if not self.handle_collision(new_head):
            return

        self.snake.insert(0, new_head)

        # Check for power-up collision
        for power_up in self.power_ups[:]:
            if new_head == power_up.position:
                self.handle_power_up(power_up)
                self.create_particles(new_head, PORTAL_COLOR)
                self.power_ups.remove(power_up)

        # Check for food collision
        for food in self.foods[:]:
            if new_head == food.position:
                points = food.type.points
                if PowerUpType.DOUBLE_POINTS in self.active_power_ups:
                    points *= 2
                self.score += points
                self.create_particles(new_head, food.type.color)
                self.foods.remove(food)
                
                # Apply special effects
                if food.type.color == FOOD_BLUE:
                    self.game_speed = 15
                elif food.type.color == FOOD_PURPLE:
                    self.generate_foods(1)
                
                break
        else:
            self.snake.pop()

        # Maintain higher food count
        self.generate_foods(15)  # Increased minimum food count from 3 to 15
        self.update_particles()

    def draw_game_elements(self):
        # Draw checkered background pattern
        for x in range(GRID_COUNT):
            for y in range(GRID_COUNT):
                # Create alternating pattern
                if (x + y) % 2 == 0:
                    color = (40, 55, 71)  # Slightly lighter than background
                else:
                    color = (35, 47, 61)  # Slightly darker than background
                    
                pygame.draw.rect(self.screen, color,
                               (x*GRID_SIZE, y*GRID_SIZE, GRID_SIZE, GRID_SIZE))
                
                # Draw subtle grid lines
                pygame.draw.rect(self.screen, (45, 62, 80),  # Very subtle grid lines
                               (x*GRID_SIZE, y*GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)

        # Add subtle corner markers every 5 cells to help with navigation
        for x in range(0, GRID_COUNT, 5):
            for y in range(0, GRID_COUNT, 5):
                marker_size = 3
                marker_color = (52, 73, 94)  # Subtle marker color
                pygame.draw.circle(self.screen, marker_color,
                                 (x*GRID_SIZE, y*GRID_SIZE), marker_size)

        # Draw obstacles
        for obstacle in self.obstacles:
            self.draw_rounded_rect(self.screen, OBSTACLE_COLOR,
                                 (obstacle[0]*GRID_SIZE + 1, obstacle[1]*GRID_SIZE + 1,
                                  GRID_SIZE - 2, GRID_SIZE - 2), 0.3)

        # Draw portals
        for portal in self.portals:
            pygame.draw.circle(self.screen, PORTAL_COLOR,
                             (portal.entrance[0]*GRID_SIZE + GRID_SIZE//2,
                              # Continue drawing portals (entrance)
              portal.entrance[1]*GRID_SIZE + GRID_SIZE//2),
              GRID_SIZE//3)
            # Draw portal exit
            pygame.draw.circle(self.screen, PORTAL_COLOR,
                             (portal.exit[0]*GRID_SIZE + GRID_SIZE//2,
                              portal.exit[1]*GRID_SIZE + GRID_SIZE//2),
                              GRID_SIZE//3)

        # Draw snake with gradient effect
        for i, segment in enumerate(self.snake):
            color = SNAKE_GREEN
            # Create gradient effect from head to tail
            fade_factor = 1.0 - (i / len(self.snake)) * 0.3
            
            # Make head slightly darker
            if i == 0:
                color = (int(color[0]*0.8), int(color[1]*0.8), int(color[2]*0.8))
            else:
                color = (int(color[0]*fade_factor), int(color[1]*fade_factor), int(color[2]*fade_factor))
            
            if PowerUpType.GHOST in self.active_power_ups:
                # Make snake semi-transparent when ghost mode is active
                color = (*color, 128)
                self.draw_rounded_rect(self.screen, color,
                                    (segment[0]*GRID_SIZE + 2, segment[1]*GRID_SIZE + 2,
                                     GRID_SIZE - 4, GRID_SIZE - 4), 0.5)
            else:
                # Draw segments with decreasing size from head to tail
                size_reduction = (i / len(self.snake)) * 2
                self.draw_rounded_rect(self.screen, color,
                                    (segment[0]*GRID_SIZE + 1 + size_reduction,
                                     segment[1]*GRID_SIZE + 1 + size_reduction,
                                     GRID_SIZE - 2 - size_reduction*2,
                                     GRID_SIZE - 2 - size_reduction*2), 0.3)

        # Draw food with animation
        for food in self.foods:
            size_modifier = math.sin(food.animation_counter) * 2
            pygame.draw.circle(self.screen, food.type.color,
                             (food.position[0]*GRID_SIZE + GRID_SIZE//2,
                              food.position[1]*GRID_SIZE + GRID_SIZE//2),
                              GRID_SIZE//3 + size_modifier)

        # Draw power-ups with pulsing animation
        for power_up in self.power_ups:
            power_up.animation_counter = (power_up.animation_counter + 0.1) % (2 * math.pi)
            size = GRID_SIZE//3 + math.sin(power_up.animation_counter) * 2
            pygame.draw.circle(self.screen, PORTAL_COLOR,
                             (power_up.position[0]*GRID_SIZE + GRID_SIZE//2,
                              power_up.position[1]*GRID_SIZE + GRID_SIZE//2),
                              size)

        # Draw particles
        for particle in self.particles:
            pygame.draw.circle(self.screen, particle['color'],
                             (particle['x'], particle['y']),
                              particle['size'])

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Draw active power-ups
        y_offset = 50
        for power_up_type, duration in self.active_power_ups.items():
            power_up_text = self.small_font.render(
                f"{power_up_type.value}: {duration//30}s", True, WHITE)
            self.screen.blit(power_up_text, (10, y_offset))
            y_offset += 30

        # Draw time remaining for Time Trial mode
        if self.game_mode == GameMode.TIME_TRIAL:
            time_text = self.font.render(
                f"Time: {self.time_left//30}s", True, WHITE)
            self.screen.blit(time_text, (WINDOW_SIZE - 200, 10))

    def draw_rounded_rect(self, surface, color, rect, corner_radius_ratio=0.3):
        """Draw a rectangle with rounded corners"""
        x, y, width, height = rect
        corner_radius = min(width, height) * corner_radius_ratio
        
        # Create points for each corner
        points = [
            (x + corner_radius, y),
            (x + width - corner_radius, y),
            (x + width, y + corner_radius),
            (x + width, y + height - corner_radius),
            (x + width - corner_radius, y + height),
            (x + corner_radius, y + height),
            (x, y + height - corner_radius),
            (x, y + corner_radius)
        ]
        
        pygame.draw.polygon(surface, color, points)
        # Draw the rounded corners
        pygame.draw.circle(surface, color, (x + corner_radius, y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (x + width - corner_radius, y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (x + width - corner_radius, y + height - corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (x + corner_radius, y + height - corner_radius), corner_radius)

    def create_particles(self, position, color, count=10):
        """Create particle effects at the given position"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': position[0] * GRID_SIZE + GRID_SIZE//2,
                'y': position[1] * GRID_SIZE + GRID_SIZE//2,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'color': color,
                'size': random.uniform(2, 4),
                'life': 30
            })

    def update_particles(self):
        """Update particle positions and remove dead particles"""
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def generate_foods(self, target_count):
        """Generate food items until reaching the target count"""
        attempts = 0
        max_attempts = 100  # Prevent infinite loops
        
        while len(self.foods) < target_count and attempts < max_attempts:
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            if (pos not in self.snake and 
                pos not in [f.position for f in self.foods] and
                pos not in self.obstacles):  # Added obstacle check
                
                food_type = random.choices(
                    list(self.food_types.values()),
                    weights=[ft.probability for ft in self.food_types.values()]
                )[0]
                self.foods.append(Food(pos, food_type))
            attempts += 1

    def handle_input(self):
        """Handle keyboard input during gameplay"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.in_menu = True  # Return to menu
                
                # Return to menu when game is over and space is pressed
                elif event.key == pygame.K_SPACE and self.game_over:
                    self.in_menu = True
                    self.game_over = False
                    return
                
                # Snake direction controls (only if game is not over)
                if not self.game_over:
                    if event.key == pygame.K_UP and self.direction != Direction.DOWN:
                        self.direction = Direction.UP
                    elif event.key == pygame.K_DOWN and self.direction != Direction.UP:
                        self.direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:
                        self.direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:
                        self.direction = Direction.RIGHT
                    
                    # Alternative controls using WASD
                    elif event.key == pygame.K_w and self.direction != Direction.DOWN:
                        self.direction = Direction.UP
                    elif event.key == pygame.K_s and self.direction != Direction.UP:
                        self.direction = Direction.DOWN
                    elif event.key == pygame.K_a and self.direction != Direction.RIGHT:
                        self.direction = Direction.LEFT
                    elif event.key == pygame.K_d and self.direction != Direction.LEFT:
                        self.direction = Direction.RIGHT

    def draw(self):
        """Draw the game screen"""
        # Clear screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw game elements
        self.draw_game_elements()
        
        # Draw game over screen if needed
        if self.game_over:
            game_over_text = self.font.render("Game Over!", True, WHITE)
            restart_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
            score_text = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 50))
            restart_rect = restart_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 20))
            score_rect = score_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 60))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(restart_text, restart_rect)
            self.screen.blit(score_text, score_rect)

    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        
        while True:
            if self.in_menu:
                self.handle_menu_input()
                self.draw_menu()
            else:
                self.handle_input()
                self.update()
                self.draw()
            
            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()

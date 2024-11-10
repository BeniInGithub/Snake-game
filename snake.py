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
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption('Enhanced Snake Game')
        self.clock = pygame.time.Clock()
        
        # Load fonts
        try:
            self.font = pygame.font.Font("arial.ttf", 36)
            self.big_font = pygame.font.Font("arial.ttf", 48)
            self.small_font = pygame.font.Font("arial.ttf", 24)
        except:
            self.font = pygame.font.SysFont("arial", 36)
            self.big_font = pygame.font.SysFont("arial", 48)
            self.small_font = pygame.font.SysFont("arial", 24)

        # Define food types
        self.food_types = {
            'normal': FoodType(FOOD_RED, 1, 0.5),
            'golden': FoodType(FOOD_GOLD, 5, 0.2),
            'speed': FoodType(FOOD_BLUE, 2, 0.15),
            'special': FoodType(FOOD_PURPLE, 3, 0.15)
        }

        # Initialize menus
        self.menu_active = True
        self.game_mode = GameMode.CLASSIC
        self.high_scores = self.load_high_scores()
        
        self.reset_game()

    def load_high_scores(self):
        # Initialize with default values
        return {mode: 0 for mode in GameMode}

    def save_high_score(self):
        if self.score > self.high_scores[self.game_mode]:
            self.high_scores[self.game_mode] = self.score

    def reset_game(self):
        self.direction = Direction.RIGHT
        center = GRID_COUNT//2
        self.snake = [(center-i, center) for i in range(3)]
        self.foods = []
        self.power_ups = []
        self.obstacles = []
        self.portals = []
        self.generate_foods(3)
        self.score = 0
        self.game_over = False
        self.particles = []
        self.active_power_ups = {}
        self.game_speed = 10
        self.time_left = 60 * 30  # 60 seconds at 30 FPS
        
        # Generate obstacles and portals based on game mode
        if self.game_mode == GameMode.MAZE:
            self.generate_maze()
        elif self.game_mode == GameMode.PORTAL:
            self.generate_portals()

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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.menu_active = False
                    self.reset_game()
                elif event.key == pygame.K_1:
                    self.game_mode = GameMode.CLASSIC
                elif event.key == pygame.K_2:
                    self.game_mode = GameMode.MAZE
                elif event.key == pygame.K_3:
                    self.game_mode = GameMode.TIME_TRIAL
                elif event.key == pygame.K_4:
                    self.game_mode = GameMode.PORTAL

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw title
        title = self.big_font.render("Enhanced Snake Game", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/4))
        self.screen.blit(title, title_rect)

        # Draw mode selections
        y_offset = WINDOW_SIZE/2
        for i, mode in enumerate(GameMode):
            text = self.font.render(f"{i+1}. {mode.value}", True, 
                                  WHITE if self.game_mode == mode else GRID_COLOR)
            rect = text.get_rect(center=(WINDOW_SIZE/2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 50

        # Draw high scores
        y_offset += 30
        title = self.font.render("High Scores:", True, WHITE)
        rect = title.get_rect(center=(WINDOW_SIZE/2, y_offset))
        self.screen.blit(title, rect)
        
        y_offset += 40
        for mode, score in self.high_scores.items():
            text = self.small_font.render(f"{mode.value}: {score}", True, WHITE)
            rect = text.get_rect(center=(WINDOW_SIZE/2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 30

        # Draw start instruction
        start_text = self.font.render("Press SPACE to Start", True, WHITE)
        start_rect = start_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE*3/4))
        self.screen.blit(start_text, start_rect)

        pygame.display.flip()

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

        # Maintain food count
        self.generate_foods(3)
        self.update_particles()

    def draw_game_elements(self):
        # Draw grid
        for x in range(GRID_COUNT):
            for y in range(GRID_COUNT):
                pygame.draw.rect(self.screen, GRID_COLOR,
                               (x*GRID_SIZE, y*GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)

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

        # Draw snake
        for i, segment in enumerate(self.snake):
            color = SNAKE_GREEN
            # Make head slightly darker
            if i == 0:
                color = (int(color[0]*0.8), int(color[1]*0.8), int(color[2]*0.8))
            
            if PowerUpType.GHOST in self.active_power_ups:
                # Make snake semi-transparent when ghost mode is active
                color = (*color, 128)
                self.draw_rounded_rect(self.screen, color,
                                     (segment[0]*GRID_SIZE + 2, segment[1]*GRID_SIZE + 2,
                                      GRID_SIZE - 4, GRID_SIZE - 4), 0.5)
            else:
                self.draw_rounded_rect(self.screen, color,
                                     (segment[0]*GRID_SIZE + 1, segment[1]*GRID_SIZE + 1,
                                      GRID_SIZE - 2, GRID_SIZE - 2), 0.3)

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
        while len(self.foods) < target_count:
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            if pos not in self.snake and pos not in [f.position for f in self.foods]:
                food_type = random.choices(
                    list(self.food_types.values()),
                    weights=[ft.probability for ft in self.food_types.values()]
                )[0]
                self.foods.append(Food(pos, food_type))

    def run(self):
        while True:
            if self.menu_active:
                self.handle_menu_input()
                self.draw_menu()
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and self.direction != Direction.DOWN:
                        self.direction = Direction.UP
                    elif event.key == pygame.K_DOWN and self.direction != Direction.UP:
                        self.direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:
                        self.direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:
                        self.direction = Direction.RIGHT
                    elif event.key == pygame.K_SPACE and self.game_over:
                        self.menu_active = True

            self.screen.fill(BACKGROUND_COLOR)
            self.update()
            self.draw_game_elements()
            
            if self.game_over:
                game_over_text = self.big_font.render("Game Over!", True, WHITE)
                restart_text = self.font.render("Press SPACE for Menu", True, WHITE)
                self.screen.blit(game_over_text, 
                               game_over_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2)))
                self.screen.blit(restart_text,
                               restart_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2 + 60)))

            pygame.display.flip()
            self.clock.tick(self.game_speed * 3)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
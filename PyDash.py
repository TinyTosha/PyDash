import pygame
import sys
import json
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 5
JUMP_HEIGHT = 12
GRAVITY = 0.6
GROUND_SPEED = 5.5  # Изменено на положительное значение для движения вправо
GROUND_WIDTH = 5763873  # Ширина пола

def load_level_name():
    with open('level.json') as f:
        level_data = json.load(f)
    return level_data.get('LEVEL_NAME', 'Unknown Level')

level_name = load_level_name()
pygame.display.set_caption(f"PyDash - {level_name}")

def load_level():
    with open('level.json') as f:
        level_data = json.load(f)

    GROUND_COLOR = tuple(level_data.get('GROUND_COLOR', [100, 100, 100]))
    BACKGROUND_COLOR = tuple(level_data.get('BACKGROUND_COLOR', [50, 50, 50]))

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    icon = pygame.image.load("Logo.png")
    pygame.display.set_icon(icon)

    icon_path = os.path.join(os.path.dirname(__file__), 'Resources', 'Icons', 'cube.png')
    spike_path = os.path.join(os.path.dirname(__file__), 'Resources', 'Game', 'Spike.png')
    block_path = os.path.join(os.path.dirname(__file__), 'Resources', 'Game', 'Block.png')

    player_image = pygame.image.load(icon_path)
    player_image = pygame.transform.scale(player_image, (50, 50))

    spike_image = pygame.image.load(spike_path)
    spike_image = pygame.transform.scale(spike_image, (60, 60))
    block_image = pygame.image.load(block_path)
    block_image = pygame.transform.scale(block_image, (60, 60))

    player_rect = player_image.get_rect(center=(WIDTH // 3, HEIGHT // 2))
    player_velocity = pygame.math.Vector2(0, 0)

    spike_rects = []
    block_rects = []
    floor_rects = []
    trigger_color_rects = []

    on_ground = False

    objects = level_data.get('objects', [])

    for obj in objects:
        obj_type = obj.get('type', '')
        if obj_type == 'spike':
            spike_rect = spike_image.get_rect(topleft=(obj.get('x', 0), obj.get('y', 0) - 20))
            spike_rects.append(spike_rect)
        elif obj_type == 'block':
            block_rect = block_image.get_rect(topleft=(obj.get('x', 0), obj.get('y', 0) - 20))
            block_rects.append(block_rect)
        elif obj_type == 'trigger_color':
            trigger_color_rect = pygame.Rect(obj.get('x', 0), obj.get('y', 0), obj.get('width', 0), obj.get('height', 0))
            trigger_color_rects.append(trigger_color_rect)  # Добавляем прямоугольник триггера в список

    # Создание одного прямоугольника земли, который занимает всю ширину экрана
    floor_rect = pygame.Rect(0, HEIGHT - 20, GROUND_WIDTH, 1300)
    floor_rects.append(floor_rect)

    return screen, clock, player_image, player_rect, player_velocity, spike_image, spike_rects, block_image, block_rects, floor_rects, trigger_color_rects, GROUND_COLOR, BACKGROUND_COLOR, on_ground

def restart_level():
    global screen, clock, player_image, player_rect, player_velocity, spike_image, spike_rects, block_image, block_rects, floor_rects, GROUND_COLOR, BACKGROUND_COLOR, on_ground
    screen, clock, player_image, player_rect, player_velocity, spike_image, spike_rects, block_image, block_rects, floor_rects, GROUND_COLOR, BACKGROUND_COLOR, on_ground = load_level()

screen, clock, player_image, player_rect, player_velocity, spike_image, spike_rects, block_image, block_rects, floor_rects, trigger_color_rects, GROUND_COLOR, BACKGROUND_COLOR, on_ground = load_level()

# Переменная для хранения смещения камеры
camera_offset_x = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE] and on_ground:
        player_velocity.y = -JUMP_HEIGHT
        on_ground = False

    player_velocity.y += GRAVITY

    # Обработка движения игрока
    player_rect.x += PLAYER_SPEED
    player_rect.y += player_velocity.y

    # Обработка столкновения игрока с полом
    for floor_rect in floor_rects:
        if player_rect.colliderect(floor_rect):
            player_rect.bottom = floor_rect.top
            player_velocity.y = 0
            on_ground = True
            break

    # Проверяем, нужно ли добавить новые сегменты пола
    for floor_rect in floor_rects:
        if floor_rect.right < camera_offset_x + WIDTH:  # Добавляем новые сегменты только если игрок приближается к краю видимой области экрана
            new_floor_rect = pygame.Rect(floor_rect.right, HEIGHT - 20, GROUND_WIDTH, 20)  # Создаем новый сегмент пола
            floor_rects.append(new_floor_rect)
            break  # Прерываем цикл, чтобы не создавать слишком много сегментов пола

    # Обработка столкновений игрока с шипами
    for spike_rect in spike_rects:
        if player_rect.colliderect(spike_rect):
            print("Игрок умер")
            restart_level()

    # Обработка столкновений игрока с блоками
    for block_rect in block_rects:
        if player_rect.colliderect(block_rect):
            if player_velocity.y > 0 and player_rect.bottom > block_rect.top:
                player_rect.bottom = block_rect.top
                player_velocity.y = 0
                on_ground = True
            elif player_velocity.y < 0 and player_rect.top < block_rect.bottom:
                player_rect.top = block_rect.bottom
                player_velocity.y = 0

    # Проверяем, пересекает ли игрок область триггера цвета
    for trigger_color_rect in trigger_color_rects:
        if player_rect.colliderect(trigger_color_rect):
            BACKGROUND_COLOR = (255, 0, 0)  # Устанавливаем цвет фона красным
            GROUND_COLOR = (255, 255, 255)  # Устанавливаем цвет пола белым

    # Рассчитываем смещение камеры по оси x и y
    camera_offset_x = player_rect.centerx - WIDTH // 2
    camera_offset_y = player_rect.centery - HEIGHT // 2

    screen.fill(BACKGROUND_COLOR)

    # Расположение игрока и объектов с учетом смещения камеры
    player_draw_rect = player_rect.move(-camera_offset_x, -camera_offset_y)
    screen.blit(player_image, player_draw_rect)
    for block_rect in block_rects:
        block_draw_rect = block_rect.move(-camera_offset_x, -camera_offset_y)
        screen.blit(block_image, block_draw_rect)
    for spike_rect in spike_rects:
        spike_draw_rect = spike_rect.move(-camera_offset_x, -camera_offset_y)
        screen.blit(spike_image, spike_draw_rect)
    for floor_rect in floor_rects:
        pygame.draw.rect(screen, GROUND_COLOR, floor_rect.move(-camera_offset_x, -camera_offset_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

import pygame
import random

pygame.init()
fps = 60
clock = pygame.time.Clock()

screen_width = 1400
screen_height = 900

GameScreen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Tiny Swords Game")
pygame.mouse.set_visible(True)

world_height, world_width = 5000, 5000

game_font = pygame.font.SysFont('Arial', 24, bold=True)
menu_font = pygame.font.SysFont('Arial', 50, bold=True)

def safe_load_image(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except (FileNotFoundError, pygame.error):
        print(f"Предупреждение: Не найден файл {path}. Создана розовая заглушка.")
        surf = pygame.Surface((64, 64))
        surf.fill((255, 0, 255))
        return surf

menu_background = pygame.transform.smoothscale(
    safe_load_image('Tiny Swords/Background.png'),
    (screen_width, screen_height))

Tilemap_Flat1 = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Terrain/Ground/Tilemap_Flat111.png')
tile_w, tile_h = Tilemap_Flat1.get_width(), Tilemap_Flat1.get_height()

pointer1 = [
    safe_load_image("Tiny Swords/Tiny Swords (Update 010)/UI/Pointers/01.png"),
    safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Terrain/Resources/Tools/Tool_01.png"),
    safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Terrain/Resources/Tools/Tool_02.png"),
    safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Terrain/Resources/Tools/Tool_03.png"),
    safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Terrain/Resources/Tools/Tool_04.png")
]

house_blue        = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/House/House_Blue.png')
house_construction= safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/House/House_Construction.png')
house_destroyed   = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/House/House_Destroyed.png')

tower_blue        = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Tower/Tower_Blue.png')
tower_construction= safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Tower/Tower_Construction.png')
tower_destroyed   = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Tower/Tower_Destroyed.png')

castle_blue        = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Castle/Castle_Blue.png')
castle_construction= safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Castle/Castle_Construction.png')
castle_destroyed   = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Buildings/Castle/Castle_Destroyed.png')

icon_gold   = safe_load_image('Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_03.png')
icon_wood   = safe_load_image('Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_02.png')
icon_meet   = safe_load_image('Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_04.png')
banner_connection_left = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/UI/Banners/Banner_Connection_Left.png')

deco_images = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Deco/{str(i).zfill(2)}.png') for i in range(1, 13)]
tree_images = [
    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Trees/Tree1.png'),
    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Trees/Tree2.png'),
    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Trees/Tree3.png')
]
tree_felled = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Trees/Tree_Felled.png')

mine_images = {
    'Active':    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Gold Mine/GoldMine_Active.png'),
    'Destroyed': safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Gold Mine/GoldMine_Destroyed.png'),
    'Inactive':  safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Resources/Gold Mine/GoldMine_Inactive.png')
}

sheep_frames = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Resources/Sheep/HappySheep/HappySheep_Idle{i}.png') for i in range(1, 9)]

spawn_anims = {
    'Gold': [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Resources/Resources/Gold_spawn/G_Spawn{i}.png') for i in range(1, 8)],
    'Wood': [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Resources/Resources/Wood_spawn/W_Spawn{i}.png') for i in range(1, 8)]
}

sheep_move = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Resources/Sheep/Sheep_Move{i}.png') for i in range(1, 4)]
cloud = [safe_load_image(f'Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Terrain/Decorations/Clouds/Clouds_0{i}.png') for i in range(1, 9)]

carved_3slides = safe_load_image('Tiny Swords/Tiny Swords (Update 010)/UI/Banners/Carved_3Slides.png')

warrior_blue_stand  = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Warrior/Blue/01/Warrior_Blue{i}.png') for i in range(1, 7)]
warrior_blue_walk   = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Warrior/Blue/02/Warrior_Blue{i}.png') for i in range(1, 7)]
warrior_blue_attack = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Warrior/Blue/03/Warrior_Blue{i}.png') for i in range(1, 7)]

# Лучник
archer_blue_stand  = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Archer/Blue/01/Archer_Blue{i}.png') for i in range(1, 7)]
archer_blue_walk   = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Archer/Blue/02/Archer_Blue{i}.png') for i in range(1, 7)]
archer_blue_attack = [safe_load_image(f'Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops//Archer/Blue/03/Archer_Blue{i}.png') for i in range(1, 9)]
arrow_imgs = [
    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Archer/Blue/03/Arrow1.png'),
    safe_load_image('Tiny Swords/Tiny Swords (Update 010)/Factions/Knights/Troops/Archer/Blue/03/Arrow2.png'),
]

button_start_img = safe_load_image("Tiny Swords/Tiny Swords (Update 010)/UI/Buttons/Button_Hover_3Slides.png")
ribbon_red_img   = safe_load_image("Tiny Swords/Tiny Swords (Update 010)/UI/Ribbons/Ribbon_Red_3Slides.png")

icon_settings = safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_10.png")
icon_exit     = safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_08.png")
icon_cancel   = safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_09.png")
icon_hammer   = safe_load_image("Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/UI Elements/UI Elements/Icons/Icon_01.png")

import math
import random
import pygame
import config

def validate_position(method): #Deco
    def wrapper(self, tx, ty):
        tx = max(0, min(tx, config.world_width))
        ty = max(0, min(ty, config.world_height))
        return method(self, tx, ty)
    return wrapper


def log_damage(method):
    def wrapper(self, now, loot_list):
        result = method(self, now, loot_list)
        entity_name = type(self).__name__
        if result:
            print(f"[{entity_name}] destroyed at ({self.x}, {self.y})")
        else:
            if hasattr(self, 'health'):
                print(f"[{entity_name}] hit — HP left: {self.health}")
        return result
    return wrapper

def iter_alive_trees(trees): #Gena
    for tree in trees:
        if tree.alive:
            yield tree


def iter_active_mines(mines):
    for mine in mines:
        if mine.status == 'Active':
            yield mine


def iter_selected_units(units):
    for unit in units:
        if getattr(unit, 'selected', False):
            yield unit

class Entity:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def get_rect(self):
        w = self.image.get_width()
        h = self.image.get_height()
        return pygame.Rect(self.x + w // 4, self.y + h - 30, w // 2, 25)

    def draw(self, surface, cam_x, cam_y):
        surface.blit(self.image, (self.x - cam_x, self.y - cam_y))


class Unit(Entity):
    def __init__(self, x, y, images_stand, images_walk, images_attack=None):
        super().__init__(x, y, images_stand[0])
        self.images_stand  = images_stand
        self.images_walk   = images_walk
        self.images_attack = images_attack if images_attack else images_walk

        self.status_anims = self.images_stand
        self.frame  = 0
        self.state  = "IDLE"

        self.target_x = x
        self.target_y = y
        self.speed    = 4
        self.flip_x   = False

        self.target_target = None
        self.selected      = False

    def get_rect(self):
        return pygame.Rect(self.x + 16, self.y + self.image.get_height() - 20, 32, 15)

    @validate_position
    def move_to(self, tx, ty):
        self.target_x      = tx
        self.target_y      = ty
        self.target_target = None
        self.state         = "WALK"
        self.status_anims  = self.images_walk
        self.flip_x        = tx < self.x

    def order_attack(self, target):
        self.target_target = target
        self.state         = "WALK_TO_TARGET"
        self.status_anims  = self.images_walk

    def update_animation(self):
        self.frame = (self.frame + 1) % len(self.status_anims)
        base = self.status_anims[self.frame]
        self.image = pygame.transform.flip(base, True, False) if self.flip_x else base

    def _target_alive(self):
        t = self.target_target
        if t is None:
            return False
        if hasattr(t, 'alive') and not t.alive:
            return False
        if hasattr(t, 'status') and t.status != 'Active':
            return False
        return True

    def check_collision(self, old_x, old_y, obstacles):
        my_rect = self.get_rect()
        for obj in obstacles:
            if obj is self or obj is self.target_target:
                continue
            if my_rect.colliderect(obj.get_rect()):
                self.x = old_x
                self.y = old_y
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                return True
        return False

    def update(self, now, loot_list, obstacles):
        old_x, old_y = self.x, self.y

        if self.state == "WALK":
            dx   = self.target_x - self.x
            dy   = self.target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.flip_x = dx < 0
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
                self.check_collision(old_x, old_y, obstacles)
            else:
                self.state        = "IDLE"
                self.status_anims = self.images_stand

        elif self.state == "WALK_TO_TARGET":
            if not self._target_alive():
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                self.target_target = None
                return
            dx   = self.target_target.x - self.x
            dy   = self.target_target.y - self.y
            dist = math.hypot(dx, dy)
            self.flip_x = dx < 0
            if dist < 70:
                self.state        = "ATTACK"
                self.status_anims = self.images_attack
                self.frame        = 0
            else:
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
                if self.check_collision(old_x, old_y, obstacles):
                    self.target_target = None

        elif self.state == "ATTACK":
            if self.target_target:
                self.flip_x = (self.target_target.x - self.x) < 0
            if not self._target_alive():
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                self.target_target = None
                return
            if self.frame == len(self.status_anims) - 1:
                destroyed = self.target_target.take_damage(now, loot_list)
                if destroyed:
                    self.state        = "IDLE"
                    self.status_anims = self.images_stand
                    self.target_target = None

class Warrior(Unit):
    def __init__(self, x, y):
        super().__init__(x, y,
                         config.warrior_blue_stand,
                         config.warrior_blue_walk,
                         config.warrior_blue_attack)
        self.speed          = 4.0
        self.explore_point  = None
        self.explore_radius = 125

    @validate_position
    def set_explore_point(self, tx, ty):
        self.explore_point = (tx, ty)
        self.move_to(tx, ty)

    def auto_find_target(self, trees, mines):
        if self.explore_point is None:
            return None
        ex, ey    = self.explore_point
        best      = None
        best_dist = self.explore_radius
        for tree in iter_alive_trees(trees):
            d = math.hypot(tree.x - ex, tree.y - ey)
            if d < best_dist:
                best_dist = d
                best      = tree
        for mine in iter_active_mines(mines):
            d = math.hypot(mine.x - ex, mine.y - ey)
            if d < best_dist:
                best_dist = d
                best      = mine
        return best

    def update(self, now, loot_list, obstacles, trees=None, mines=None):
        if (self.explore_point is not None
                and self.state == "IDLE"
                and self.target_target is None
                and trees is not None and mines is not None):
            target = self.auto_find_target(trees, mines)
            if target:
                self.order_attack(target)
            else:
                self.explore_point = None   
        super().update(now, loot_list, obstacles)

class Arrow:
    SPEED        = 13
    EMBED_TIME   = 5000   # мс — сколько стрела торчит в цели

    def __init__(self, x, y, target):
        self.x      = float(x)
        self.y      = float(y)
        self.target = target
        dx = target.x - x
        dy = target.y - y
        dist = math.hypot(dx, dy) or 1
        self.vx = dx / dist * self.SPEED
        self.vy = dy / dist * self.SPEED
        self.angle  =  -math.degrees(math.atan2(-dy, dx)) - 45     #-math.sin(dy / math.sqrt(dx**2 + dy**2))#
        self.hit    = False
        self.hit_time = 0
        self.dead   = False
        self.img_fly    = config.arrow_imgs[0]
        self.img_embed  = config.arrow_imgs[1]

    def update(self, now, loot_list):
        if self.dead:
            return
        if self.hit:
            if now - self.hit_time >= self.EMBED_TIME:
                self.dead = True
            return
        self.x += self.vx
        self.y += self.vy
        tx = self.target.x + self.target.image.get_width() // 2
        ty = self.target.y + self.target.image.get_height() // 2
        if math.hypot(self.x - tx, self.y - ty) < 20:
            self.hit      = True
            self.hit_time = now
            destroyed = self.target.take_damage(now, loot_list)

    def draw(self, surface, cam_x, cam_y):
        if self.dead:
            return
        if self.hit:
            img = self.img_embed
        else:
            img = pygame.transform.rotate(self.img_fly, self.angle)
        sx = self.x - cam_x - img.get_width() // 2
        sy = self.y - cam_y - img.get_height() // 2
        surface.blit(img, (sx, sy))

class Archer(Unit):
    RANGE         = 500
    ATTACK_CD     = 1800

    def __init__(self, x, y):
        super().__init__(x, y,
                         config.archer_blue_stand,
                         config.archer_blue_walk,
                         config.archer_blue_attack)
        self.speed         = 3.5
        self.explore_point = None
        self.explore_radius= 300
        self.arrows        = []
        self.last_shot     = 0

    @validate_position
    def set_explore_point(self, tx, ty):
        self.explore_point = (tx, ty)
        self.move_to(tx, ty)

    def auto_find_target(self, trees, mines):
        if self.explore_point is None:
            return None
        ex, ey    = self.explore_point
        best      = None
        best_dist = self.explore_radius
        for tree in iter_alive_trees(trees):
            d = math.hypot(tree.x - ex, tree.y - ey)
            if d < best_dist:
                best_dist = d; best = tree
        for mine in iter_active_mines(mines):
            d = math.hypot(mine.x - ex, mine.y - ey)
            if d < best_dist:
                best_dist = d; best = mine
        return best

    def update(self, now, loot_list, obstacles, trees=None, mines=None):
        if (self.explore_point is not None
                and self.state == "IDLE"
                and self.target_target is None
                and trees is not None and mines is not None):
            target = self.auto_find_target(trees, mines)
            if target:
                self.order_attack(target)
            else:
                self.explore_point = None

        old_x, old_y = self.x, self.y

        if self.state == "WALK":
            dx   = self.target_x - self.x
            dy   = self.target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.flip_x = dx < 0
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
                self.check_collision(old_x, old_y, obstacles)
            else:
                self.state        = "IDLE"
                self.status_anims = self.images_stand

        elif self.state == "WALK_TO_TARGET":
            if not self._target_alive():
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                self.target_target = None
                return
            dx   = self.target_target.x - self.x
            dy   = self.target_target.y - self.y
            dist = math.hypot(dx, dy)
            self.flip_x = dx < 0
            if dist <= self.RANGE:
                self.state        = "ATTACK"
                self.status_anims = self.images_attack
                self.frame        = 0
            else:
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
                if self.check_collision(old_x, old_y, obstacles):
                    self.target_target = None

        elif self.state == "ATTACK":
            if not self._target_alive():
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                self.target_target = None
                return
            dx = self.target_target.x - self.x
            dy = self.target_target.y - self.y
            self.flip_x = dx < 0
            dist = math.hypot(dx, dy)
            if dist > self.RANGE:
                self.state        = "WALK_TO_TARGET"
                self.status_anims = self.images_walk
                return
            if now - self.last_shot >= self.ATTACK_CD:
                self.last_shot = now
                ax = self.x + self.image.get_width() // 2
                ay = self.y + self.image.get_height() // 2
                self.arrows.append(Arrow(ax, ay, self.target_target))
        for arrow in self.arrows[:]:
            arrow.update(now, loot_list)
            if arrow.dead:
                self.arrows.remove(arrow)

    def draw(self, surface, cam_x, cam_y):
        super().draw(surface, cam_x, cam_y)
        for arrow in self.arrows:
            arrow.draw(surface, cam_x, cam_y)
            
class Sheep(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, config.sheep_frames, config.sheep_move)
        self.speed      = 0.8
        self.wait_timer = pygame.time.get_ticks() + random.randint(2000, 5000)

    def update(self, now, loot_list, obstacles):
        old_x, old_y = self.x, self.y
        if self.state == "IDLE":
            if now > self.wait_timer:
                self.target_x = max(100, min(self.x + random.randint(-120, 120), config.world_width - 200))
                self.target_y = max(100, min(self.y + random.randint(-120, 120), config.world_height - 200))
                self.state        = "WALK"
                self.status_anims = self.images_walk
                self.flip_x       = self.target_x < self.x
        elif self.state == "WALK":
            dx   = self.target_x - self.x
            dy   = self.target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 3:
                self.flip_x = dx < 0
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
                if self.check_collision(old_x, old_y, obstacles):
                    self.wait_timer = now + random.randint(2000, 4000)
            else:
                self.state        = "IDLE"
                self.status_anims = self.images_stand
                self.wait_timer   = now + random.randint(3000, 6000)

class Tree(Entity):
    def __init__(self, x, y):
        self.original_image = random.choice(config.tree_images)
        super().__init__(x, y, self.original_image)
        self.health     = 3
        self.max_health = 3
        self.alive      = True
        self.respawn_time = None

    def get_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()
        return pygame.Rect(self.x + w // 2 - 15, self.y + h - 30, 30, 20)

    @log_damage
    def take_damage(self, now, loot_list):
        if self.alive:
            self.health -= 1
            if self.health <= 0:
                self.alive = False
                self.image = config.tree_felled
                lx = self.x + self.image.get_width() // 2 - 16
                ly = self.y + self.image.get_height() - 48
                loot_list.append({'x': lx, 'y': ly, 'type': 'Wood', 'frame': 0, 'last_tick': now})
                self.respawn_time = now + random.randint(10000, 15000)
                return True
        return False

    def update(self, now):
        if not self.alive and self.respawn_time and now >= self.respawn_time:
            self.alive          = True
            self.health         = self.max_health
            self.original_image = random.choice(config.tree_images)
            self.image          = self.original_image
            self.respawn_time   = None


class GoldMine(Entity):
    def __init__(self, x, y, status):
        super().__init__(x, y, config.mine_images[status])
        self.status     = status
        self.health     = 5
        self.max_health = 5
        self.respawn_time = None

    def get_rect(self):
        w = self.image.get_width()
        h = self.image.get_height()
        return pygame.Rect(self.x + 15, self.y + h // 2, w - 30, h // 2 - 10)

    @log_damage
    def take_damage(self, now, loot_list):
        if self.status == 'Active':
            self.health -= 1
            if self.health <= 0:
                self.status = 'Inactive'
                self.image  = config.mine_images['Inactive']
                lx = self.x + self.image.get_width() // 2 - 16
                ly = self.y + self.image.get_height() // 2
                loot_list.append({'x': lx, 'y': ly, 'type': 'Gold', 'frame': 0, 'last_tick': now})
                self.respawn_time = now + random.randint(10000, 15000)
                return True
        return False

    def update(self, now):
        if self.status == 'Inactive' and self.respawn_time and now >= self.respawn_time:
            self.status   = 'Active'
            self.health   = self.max_health
            self.image    = config.mine_images['Active']
            self.respawn_time = None

class Building(Entity):
    BUILD_TIME = 10000  
    def __init__(self, x, y, img_construction, img_done, img_destroyed):
        super().__init__(x, y, img_construction)
        self.img_construction = img_construction
        self.img_done         = img_done
        self.img_destroyed    = img_destroyed
        self.built            = False
        self.destroyed        = False
        self.build_finish     = pygame.time.get_ticks() + self.BUILD_TIME
        self.builder          = Warrior#None   # строитель 

    def get_rect(self):
        w = self.image.get_width()
        h = self.image.get_height()
        return pygame.Rect(self.x + 20, self.y + h // 2, w - 40, h // 2 - 10)

    def update(self, now):
        if not self.built and not self.destroyed:
            if now >= self.build_finish:
                self.built  = True
                self.image  = self.img_done
                if self.builder:
                    self.builder.state        = "IDLE"
                    self.builder.status_anims = self.builder.images_stand
                    self.builder = None

    def draw(self, surface, cam_x, cam_y):
        surface.blit(self.image, (self.x - cam_x, self.y - cam_y))
        if not self.built and not self.destroyed:
            now      = pygame.time.get_ticks()
            elapsed  = now - (self.build_finish - self.BUILD_TIME)
            progress = min(elapsed / self.BUILD_TIME, 1.0)
            bar_w    = self.image.get_width()
            bx       = self.x - cam_x
            by       = self.y - cam_y - 12
            pygame.draw.rect(surface, (60, 60, 60),    (bx, by, bar_w, 8))
            pygame.draw.rect(surface, (80, 200, 80),   (bx, by, int(bar_w * progress), 8))
            pygame.draw.rect(surface, (200, 200, 200), (bx, by, bar_w, 8), 1)


class House(Building):
    BUILD_TIME   = 10000
    COST_GOLD    = 2
    COST_WOOD    = 3
    SPAWN_COUNT  = 1

    def __init__(self, x, y, pre_built=False):
        super().__init__(x, y,
                         config.house_construction,
                         config.house_blue,
                         config.house_destroyed)
        if pre_built:
            self.built  = True
            self.image  = self.img_done


class Tower(Building):
    BUILD_TIME   = 15000
    COST_GOLD    = 4
    COST_WOOD    = 5
    SPAWN_COUNT  = 3   # лучники

    def __init__(self, x, y):
        super().__init__(x, y,
                         config.tower_construction,
                         config.tower_blue,
                         config.tower_destroyed)


class Castle(Building):
    BUILD_TIME   = 20000
    COST_GOLD    = 8
    COST_WOOD    = 10
    SPAWN_COUNT  = 5   # рыцари

    def __init__(self, x, y):
        super().__init__(x, y,
                         config.castle_construction,
                         config.castle_blue,
                         config.castle_destroyed)

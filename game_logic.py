import pygame
import random
import json
import os
import config
from entities import Entity, Tree, GoldMine, Warrior, Archer, Sheep, House, Tower, Castle

STATS_FILE = "savegame.json"

class Game:
    def __init__(self):
        self.state            = "START_MENU"
        self.selection_start  = None
        self.selection_rect   = None
        self.is_selecting     = False
        self.dragging         = False
        self.last_mouse_pos   = (0, 0)
        self.settings_open    = False
        self.session_start_time = 0

        self.build_mode       = None
        self.build_preview_pos = None

        self.last_game_data   = self._load_save()
        self.reset_game()

    def _load_save(self):
        default = {"resources": {"Gold": 0, "Wood": 0},
                   "warriors": [], "archers": [], "buildings": [],
                   "duration_seconds": 0}
        if not os.path.exists(STATS_FILE):
            return default
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "resources" not in data:
                data = default
            return data
        except Exception:
            return default

    def _save(self):
        duration = (pygame.time.get_ticks() - self.session_start_time) // 1000
        warriors  = [{"x": u.x, "y": u.y} for u in self.units_list if isinstance(u, Warrior)]
        archers   = [{"x": u.x, "y": u.y} for u in self.units_list if isinstance(u, Archer)]
        buildings = []
        for b in self.buildings_list:
            buildings.append({
                "type":  type(b).__name__,
                "x":     b.x,
                "y":     b.y,
                "built": b.built
            })
        data = {
            "resources":        self.resources_count,
            "warriors":         warriors,
            "archers":          archers,
            "buildings":        buildings,
            "duration_seconds": duration
        }
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            print("Не удалось сохранить игру.")

    def reset_game(self, load_save=False):
        self.resources_count = {"Gold": 0, "Wood": 0}
        self.settings_open   = False
        self.build_mode      = None
        self.build_preview_pos = None
        self.loot_spawns     = []
        self.units_list      = []
        self.buildings_list  = []

        self.camera_x = config.world_width  // 2 - config.screen_width  // 2
        self.camera_y = config.world_height // 2 - config.screen_height // 2

        cx = config.world_width  // 2 - config.house_blue.get_width()  // 2
        cy = config.world_height // 2 - config.house_blue.get_height() // 2
        main_house = House(cx, cy, pre_built=True)
        self.buildings_list.append(main_house)

        if load_save and self.last_game_data:
            d = self.last_game_data
            self.resources_count = d.get("resources", {"Gold": 0, "Wood": 0})
            for w in d.get("warriors", []):
                self.units_list.append(Warrior(w["x"], w["y"]))
            for a in d.get("archers", []):
                self.units_list.append(Archer(a["x"], a["y"]))
            for b in d.get("buildings", []):
                btype = b["type"]
                bx, by = b["x"], b["y"]
                if btype == "House":
                    nb = House(bx, by, pre_built=b.get("built", True))
                    self.buildings_list.append(nb)
                elif btype == "Tower":
                    nb = Tower(bx, by)
                    if b.get("built"):
                        nb.built = True; nb.image = nb.img_done
                    self.buildings_list.append(nb)
                elif btype == "Castle":
                    nb = Castle(bx, by)
                    if b.get("built"):
                        nb.built = True; nb.image = nb.img_done
                    self.buildings_list.append(nb)
            if not self.units_list:
                self._spawn_default_units(cy)
        else:
            self._spawn_default_units(cy)

        self.mines_list = []
        while len(self.mines_list) < 12:
            rx = random.randint(150, config.world_width  - 250)
            ry = random.randint(150, config.world_height - 250)
            if ((rx - config.world_width//2)**2 + (ry - config.world_height//2)**2)**0.5 > 600:
                self.mines_list.append(GoldMine(rx, ry, 'Active'))

        self.trees_list = [
            Tree(random.randint(100, config.world_width  - 200),
                 random.randint(100, config.world_height - 200))
            for _ in range(70)
        ]
        self.deco_list = [
            Entity(random.randint(50, config.world_width  - 100),
                   random.randint(50, config.world_height - 100),
                   random.choice(config.deco_images))
            for _ in range(80)
        ]
        self.clouds_list = [
            {'x': random.randint(-300, config.world_width),
             'y': random.randint(0, config.world_height // 3),
             'speed': random.uniform(0.5, 1.2),
             'image': random.choice(config.cloud)}
            for _ in range(8)
        ]
        self.last_anim_tick = pygame.time.get_ticks()

    def _spawn_default_units(self, cy):
        house_y = cy
        for i in range(5):
            self.units_list.append(
                Warrior(config.world_width // 2 + i * 70 - 140, house_y + 200))
        for _ in range(12):
            self.units_list.append(
                Sheep(random.randint(300, config.world_width  - 300),
                      random.randint(300, config.world_height - 300)))

    def _get_build_img(self):
        mapping = {'house': config.house_blue, 'tower': config.tower_blue, 'castle': config.castle_blue}
        return mapping.get(self.build_mode)

    def _get_build_cost(self):
        costs = {'house': (2, 3), 'tower': (4, 5), 'castle': (8, 10)}
        return costs.get(self.build_mode, (0, 0))

    def _can_place(self, wx, wy):
        img = self._get_build_img()
        if img is None:
            return False
        new_rect = pygame.Rect(wx, wy, img.get_width(), img.get_height())
        for b in self.buildings_list:
            if new_rect.colliderect(pygame.Rect(b.x, b.y, b.image.get_width(), b.image.get_height())):
                return False
        for t in self.trees_list:
            if t.alive and new_rect.colliderect(t.get_rect()):
                return False
        for m in self.mines_list:
            if new_rect.colliderect(m.get_rect()):
                return False
        return True

    def _place_building(self, wx, wy):
        gold_cost, wood_cost = self._get_build_cost()
        if self.resources_count['Gold'] < gold_cost or self.resources_count['Wood'] < wood_cost:
            return False
        if not self._can_place(wx, wy):
            return False

        self.resources_count['Gold'] -= gold_cost
        self.resources_count['Wood'] -= wood_cost

        if self.build_mode == 'house':
            building = House(wx, wy)
            spawn_cls   = Warrior
            spawn_count = House.SPAWN_COUNT
        elif self.build_mode == 'tower':
            building = Tower(wx, wy)
            spawn_cls   = Archer
            spawn_count = Tower.SPAWN_COUNT
        else:
            building = Castle(wx, wy)
            spawn_cls   = Warrior
            spawn_count = Castle.SPAWN_COUNT

        self.buildings_list.append(building)

        free_workers = [u for u in self.units_list
                        if isinstance(u, (Warrior, Archer)) and u.state == "IDLE"]
        if free_workers:
            worker = min(free_workers,
                         key=lambda u: (u.x - wx)**2 + (u.y - wy)**2)
            worker.move_to(wx + building.image.get_width() // 2,
                           wy + building.image.get_height())
            building.builder = worker
            worker.state = "WALK"
        building._pending_spawn_cls   = spawn_cls
        building._pending_spawn_count = spawn_count

        self.build_mode       = None
        self.build_preview_pos = None
        return True

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        world_mx  = mouse_pos[0] + self.camera_x
        world_my  = mouse_pos[1] + self.camera_y

        btn_start_rect    = pygame.Rect(config.screen_width // 2 - 110, 360, 220, 60)
        btn_continue_rect = pygame.Rect(config.screen_width // 2 - 110, 430, 220, 60)
        icon_settings_rect= pygame.Rect(config.screen_width - 75, 15,  60, 60)
        btn_house_rect    = pygame.Rect(config.screen_width - 75, 85,  60, 60)
        btn_tower_rect    = pygame.Rect(config.screen_width - 75, 155, 60, 60)
        btn_castle_rect   = pygame.Rect(config.screen_width - 75, 225, 60, 60)

        menu_box_x = config.screen_width  // 2 - 175
        menu_box_y = config.screen_height // 2 - 100
        btn_exit_rect   = pygame.Rect(menu_box_x + 50,  menu_box_y + 110, 64, 64)
        btn_resume_rect = pygame.Rect(menu_box_x + 230, menu_box_y + 110, 64, 64)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.state == "PLAY":
                    self._save()
                pygame.quit()
                raise SystemExit

            if self.state == "START_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_start_rect.collidepoint(mouse_pos):
                        self.state = "PLAY"
                        self.session_start_time = pygame.time.get_ticks()
                        self.reset_game(load_save=False)
                    elif btn_continue_rect.collidepoint(mouse_pos):
                        self.state = "PLAY"
                        self.session_start_time = pygame.time.get_ticks()
                        self.reset_game(load_save=True)

            elif self.state == "PLAY":
                if self.build_mode:
                    self.build_preview_pos = (world_mx, world_my)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.settings_open:
                            if btn_exit_rect.collidepoint(mouse_pos):
                                self._save()
                                self.last_game_data = self._load_save()
                                self.state = "START_MENU"
                                return True
                            elif btn_resume_rect.collidepoint(mouse_pos):
                                self.settings_open = False
                            continue

                        if icon_settings_rect.collidepoint(mouse_pos):
                            self.settings_open = True
                            self.build_mode    = None
                            continue

                        # Кнопки постройки
                        for btn, mode in [(btn_house_rect, 'house'),
                                          (btn_tower_rect, 'tower'),
                                          (btn_castle_rect, 'castle')]:
                            if btn.collidepoint(mouse_pos):
                                gc, wc = self._get_build_cost_for(mode)
                                if (self.resources_count['Gold'] >= gc and
                                        self.resources_count['Wood'] >= wc):
                                    self.build_mode = mode if self.build_mode != mode else None
                                    self.build_preview_pos = None
                                break
                        else:
                            if self.build_mode:
                                img = self._get_build_img()
                                place_x = world_mx - img.get_width()  // 2
                                place_y = world_my - img.get_height() // 2
                                self._place_building(place_x, place_y)
                            else:
                                self.dragging       = True
                                self.last_mouse_pos = event.pos

                    elif event.button == 3 and not self.settings_open:
                        if self.build_mode:
                            self.build_mode        = None
                            self.build_preview_pos = None
                            continue
                        self.is_selecting     = True
                        self.selection_start  = mouse_pos
                        self.selection_rect   = pygame.Rect(mouse_pos[0], mouse_pos[1], 0, 0)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                    elif event.button == 3 and not self.settings_open and not self.build_mode:
                        if self.is_selecting:
                            self.is_selecting = False
                            if self.selection_rect and (self.selection_rect.width > 10 or
                                                        self.selection_rect.height > 10):
                                wsr = pygame.Rect(
                                    self.selection_rect.x + self.camera_x,
                                    self.selection_rect.y + self.camera_y,
                                    self.selection_rect.width,
                                    self.selection_rect.height)
                                for u in self.units_list:
                                    if isinstance(u, (Warrior, Archer)):
                                        u.selected = wsr.colliderect(u.get_rect())
                            else:
                                clicked_unit = False
                                for u in self.units_list:
                                    if isinstance(u, (Warrior, Archer)) and \
                                            u.get_rect().collidepoint(world_mx, world_my):
                                        for uu in self.units_list: uu.selected = False
                                        u.selected   = True
                                        clicked_unit = True
                                        break
                                if not clicked_unit:
                                    selected = [u for u in self.units_list
                                                if isinstance(u, (Warrior, Archer))
                                                and getattr(u, 'selected', False)]
                                    for u in selected:
                                        ox = random.randint(-30, 30)
                                        oy = random.randint(-30, 30)
                                        u.set_explore_point(world_mx + ox, world_my + oy)
                            self.selection_rect = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.build_mode:
                        self.build_preview_pos = (world_mx, world_my)
                    elif self.dragging:
                        self.camera_x -= event.pos[0] - self.last_mouse_pos[0]
                        self.camera_y -= event.pos[1] - self.last_mouse_pos[1]
                        self.last_mouse_pos = event.pos
                    elif self.is_selecting and self.selection_start:
                        x1, y1 = self.selection_start
                        x2, y2 = event.pos
                        self.selection_rect = pygame.Rect(
                            min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))
        return True

    def _get_build_cost_for(self, mode):
        costs = {'house': (2,3), 'tower': (4,5), 'castle': (8,10)}
        return costs.get(mode, (0,0))

    def update(self):
        if self.state != "PLAY" or self.settings_open:
            return
        now = pygame.time.get_ticks()

        self.camera_x = max(0, min(self.camera_x, config.world_width  - config.screen_width))
        self.camera_y = max(0, min(self.camera_y, config.world_height - config.screen_height))

        for cloud in self.clouds_list:
            cloud['x'] += cloud['speed']
            if cloud['x'] > config.world_width + 200:
                cloud['x'] = -300
                cloud['y'] = random.randint(0, config.world_height // 3)


        for t in self.trees_list: t.update(now)
        for m in self.mines_list: m.update(now)

        for b in self.buildings_list:
            was_built = b.built
            b.update(now)
            if not was_built and b.built:

                cls   = getattr(b, '_pending_spawn_cls',   Warrior)
                count = getattr(b, '_pending_spawn_count', 1)
                sy    = b.y + b.image.get_height() + 20
                for i in range(count):
                    self.units_list.append(cls(b.x + 30 + i * 60, sy))

        obstacles = list(self.buildings_list)
        for t in self.trees_list:
            if t.alive: obstacles.append(t)
        for m in self.mines_list:
            if m.status == 'Active': obstacles.append(m)

        for u in self.units_list:
            if isinstance(u, (Warrior, Archer)):
                u.update(now, self.loot_spawns, obstacles,
                         trees=self.trees_list, mines=self.mines_list)
            else:
                u.update(now, self.loot_spawns, obstacles)

        if now - self.last_anim_tick > 130:
            self.last_anim_tick = now
            for u in self.units_list:
                u.update_animation()

        for loot in self.loot_spawns[:]:
            if now - loot['last_tick'] > 110:
                loot['last_tick'] = now
                loot['frame']    += 1
                if loot['frame'] >= 7:
                    self.resources_count[loot['type']] += 1
                    self.loot_spawns.remove(loot)


        if not hasattr(self, '_last_autosave'):
            self._last_autosave = now
        if now - self._last_autosave > 30000:
            self._save()
            self._last_autosave = now

    def draw(self):
        if self.state == "START_MENU":
            config.GameScreen.blit(config.menu_background, (0, 0))

            ribbon_scaled = pygame.transform.scale(config.ribbon_red_img, (450, 110))
            config.GameScreen.blit(ribbon_scaled,
                (config.screen_width//2 - ribbon_scaled.get_width()//2, 240))
            title = config.game_font.render("START MENU", True, (255,255,255))
            config.GameScreen.blit(title, (config.screen_width//2 - title.get_width()//2, 278))

            box_w, box_h = 420, 200
            box_x = config.screen_width//2  - box_w//2
            box_y = config.screen_height//2 + 20
            pygame.draw.rect(config.GameScreen, (230,200,150), (box_x, box_y, box_w, box_h), 0, 12)
            pygame.draw.rect(config.GameScreen, (140,90,40),   (box_x, box_y, box_w, box_h), 4, 12)
            d = self.last_game_data
            lines = [
                f"Сессия: {d.get('duration_seconds',0)} сек.",
                f"Золото: {d.get('resources',{}).get('Gold',0)}",
                f"Дерево: {d.get('resources',{}).get('Wood',0)}",
                f"Воинов: {len(d.get('warriors',[]))}  Лучников: {len(d.get('archers',[]))}",
            ]
            for i, line in enumerate(lines):
                surf = config.game_font.render(line, True, (70,40,15))
                config.GameScreen.blit(surf, (box_x+20, box_y+15+i*42))


            btn = pygame.transform.scale(config.button_start_img, (220, 55))
            bx  = config.screen_width//2 - btn.get_width()//2
            config.GameScreen.blit(btn, (bx, 360))
            t = config.game_font.render("НОВАЯ ИГРА", True, (60,60,60))
            config.GameScreen.blit(t, (config.screen_width//2 - t.get_width()//2, 373))

            if os.path.exists(STATS_FILE):
                config.GameScreen.blit(btn, (bx, 430))
                t2 = config.game_font.render("ПРОДОЛЖИТЬ", True, (60,60,60))
                config.GameScreen.blit(t2, (config.screen_width//2 - t2.get_width()//2, 443))

        elif self.state == "PLAY":
            config.GameScreen.fill((0,0,0))

            sx = (self.camera_x // config.tile_w) * config.tile_w
            sy = (self.camera_y // config.tile_h) * config.tile_h
            for x in range(int(sx), int(sx + config.screen_width  + config.tile_w), config.tile_w):
                for y in range(int(sy), int(sy + config.screen_height + config.tile_h), config.tile_h):
                    config.GameScreen.blit(config.Tilemap_Flat1, (x - self.camera_x, y - self.camera_y))

            for deco in self.deco_list:
                deco.draw(config.GameScreen, self.camera_x, self.camera_y)

            render_q = list(self.buildings_list) + self.mines_list + self.trees_list + self.units_list
            render_q.sort(key=lambda o: o.get_rect().bottom)

            for obj in render_q:
                if hasattr(obj, 'selected') and obj.selected:
                    r = obj.get_rect()
                    pygame.draw.ellipse(config.GameScreen, (0,255,0),
                        (obj.x - self.camera_x, r.bottom - 10 - self.camera_y,
                         obj.image.get_width(), 15), 2)

                obj.draw(config.GameScreen, self.camera_x, self.camera_y)

                if (hasattr(obj, 'selected') and obj.selected
                        and hasattr(obj, 'explore_point')
                        and obj.explore_point is not None):
                    ex, ey = obj.explore_point
                    r = obj.explore_radius
                    cs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                    pygame.draw.circle(cs, (255,220,50, 40), (r,r), r)
                    pygame.draw.circle(cs, (255,220,50,180), (r,r), r, 2)
                    config.GameScreen.blit(cs, (ex - r - self.camera_x, ey - r - self.camera_y))


            for loot in self.loot_spawns:
                img = config.spawn_anims[loot['type']][loot['frame']]
                config.GameScreen.blit(img, (loot['x'] - self.camera_x, loot['y'] - self.camera_y))


            for cloud in self.clouds_list:
                config.GameScreen.blit(cloud['image'],
                    (cloud['x'] - self.camera_x, cloud['y'] - self.camera_y))

 
            if self.is_selecting and self.selection_rect:
                sel_surf = pygame.Surface((self.selection_rect.width, self.selection_rect.height), pygame.SRCALPHA)
                sel_surf.fill((0,102,204,70))
                config.GameScreen.blit(sel_surf, (self.selection_rect.x, self.selection_rect.y))
                pygame.draw.rect(config.GameScreen, (0,102,204), self.selection_rect, 2)


            if self.build_mode and self.build_preview_pos:
                wx, wy = self.build_preview_pos
                img = self._get_build_img()
                px  = wx - img.get_width()  // 2
                py  = wy - img.get_height() // 2
                ok  = self._can_place(px, py)
                prev = img.copy()
                tint = pygame.Surface(prev.get_size(), pygame.SRCALPHA)
                tint.fill((0,255,0,70) if ok else (255,0,0,70))
                prev.blit(tint, (0,0))
                config.GameScreen.blit(prev, (px - self.camera_x, py - self.camera_y))
                gc, wc = self._get_build_cost_for(self.build_mode)
                hint_txt = (f"ЛКМ — построить ({gc} {wc})  |  ПКМ — отмена"
                            if ok else "Место занято! ПКМ — отмена")
                hint_col = (100,220,100) if ok else (220,80,80)
                hint = config.game_font.render(hint_txt, True, hint_col)
                config.GameScreen.blit(hint, (config.screen_width//2 - hint.get_width()//2,
                                               config.screen_height - 50))

   
            config.GameScreen.blit(config.carved_3slides, (10, 15))
            config.GameScreen.blit(config.icon_gold, (16, 20))
            config.GameScreen.blit(
                config.game_font.render(str(self.resources_count['Gold']), True, (255,115,0)), (78,34))
            config.GameScreen.blit(config.icon_wood, (105, 20))
            config.GameScreen.blit(
                config.game_font.render(str(self.resources_count['Wood']), True, (210,110,0)), (173,34))


            wc = sum(1 for u in self.units_list if isinstance(u, Warrior))
            ac = sum(1 for u in self.units_list if isinstance(u, Archer))
            troops_txt = config.game_font.render(f"{wc}  {ac}", True, (240,240,200))
            config.GameScreen.blit(troops_txt, (16, 60))


            icon_set = pygame.transform.scale(config.icon_settings, (60,60))
            config.GameScreen.blit(icon_set, (config.screen_width - 75, 15))

            build_buttons = [
                ('house',  config.icon_hammer,          85),
                ('tower',  config.tower_blue,           155),
                ('castle', config.castle_blue,          225),
            ]
            for mode, img_src, by_offset in build_buttons:
                scaled = pygame.transform.scale(img_src, (60, 60))
                bx = config.screen_width - 75
                gc, wc_cost = self._get_build_cost_for(mode)
                can_afford = (self.resources_count['Gold'] >= gc and
                              self.resources_count['Wood'] >= wc_cost)
                config.GameScreen.blit(scaled, (bx, by_offset))
                if not can_afford:
                    dim = pygame.Surface((60,60), pygame.SRCALPHA)
                    dim.fill((0,0,0,130))
                    config.GameScreen.blit(dim, (bx, by_offset))
                if self.build_mode == mode:
                    pygame.draw.rect(config.GameScreen, (255,220,50), (bx, by_offset, 60, 60), 3)
                cost_lbl = config.game_font.render(f"{gc}G {wc_cost}W", True,
                    (240,200,80) if can_afford else (150,150,150))
                config.GameScreen.blit(cost_lbl, (bx - 60, by_offset + 20))


            if self.settings_open:
                overlay = pygame.Surface((config.screen_width, config.screen_height), pygame.SRCALPHA)
                overlay.fill((0,0,0,120))
                config.GameScreen.blit(overlay, (0,0))
                mw, mh = 350, 210
                mx = config.screen_width  // 2 - mw // 2
                my = config.screen_height // 2 - mh // 2
                pygame.draw.rect(config.GameScreen, (240,215,170), (mx,my,mw,mh), 0, 15)
                pygame.draw.rect(config.GameScreen, (110,75,40),   (mx,my,mw,mh), 5, 15)
                info = config.game_font.render("ЗАВЕРШИТЬ ИГРУ?", True, (80,50,20))
                config.GameScreen.blit(info, (config.screen_width//2 - info.get_width()//2, my+40))
                ex_sc  = pygame.transform.scale(config.icon_exit,   (64,64))
                res_sc = pygame.transform.scale(config.icon_cancel,  (64,64))
                config.GameScreen.blit(ex_sc,  (mx+50,  my+110))
                config.GameScreen.blit(res_sc, (mx+230, my+110))
                config.GameScreen.blit(config.game_font.render("Выйти", True, (130,30,30)),  (mx+53,  my+175))
                config.GameScreen.blit(config.game_font.render("Назад", True, (30,100,30)),  (mx+235, my+175))

        pygame.display.flip()

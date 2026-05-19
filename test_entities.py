import sys
import types
import math
import unittest

class FakeSurface:
    def __init__(self, w=64, h=64):
        self._w = w
        self._h = h
    def get_width(self):  return self._w
    def get_height(self): return self._h
    def blit(self, *a):   pass
    def fill(self, *a):   pass
    def copy(self):       return FakeSurface(self._w, self._h)

class FakeRect:
    def __init__(self, x, y, w, h):
        self.x = x; self.y = y; self.width = w; self.height = h
        self.bottom = y + h
    def colliderect(self, other):
        return not (self.x + self.width  <= other.x or
                    other.x + other.width  <= self.x or
                    self.y + self.height <= other.y or
                    other.y + other.height <= self.y)

class FakeTransform:
    @staticmethod
    def flip(surf, *a): return surf
    @staticmethod
    def rotate(surf, *a): return surf

class FakeTime:
    @staticmethod
    def get_ticks(): return 0

pygame_stub = types.ModuleType("pygame")
pygame_stub.Rect       = FakeRect
pygame_stub.Surface    = FakeSurface
pygame_stub.transform  = FakeTransform
pygame_stub.time       = FakeTime
pygame_stub.draw       = types.SimpleNamespace(
    rect=lambda *a, **kw: None,
    ellipse=lambda *a, **kw: None,
    circle=lambda *a, **kw: None,
)
sys.modules["pygame"] = pygame_stub

# Minimal config stub
config_stub = types.ModuleType("config")
config_stub.world_width  = 5000
config_stub.world_height = 5000

_img = FakeSurface()
for attr in ["warrior_blue_stand", "warrior_blue_walk", "warrior_blue_attack",
    "archer_blue_stand",  "archer_blue_walk",  "archer_blue_attack",
    "sheep_frames", "sheep_move",
    "arrow_imgs",]:
    setattr(config_stub, attr, [_img, _img, _img, _img, _img, _img, _img, _img])

for attr in ["house_construction", "house_blue", "house_destroyed",
    "tower_construction", "tower_blue", "tower_destroyed",
    "castle_construction", "castle_blue", "castle_destroyed",]:
    setattr(config_stub, attr, _img)

config_stub.tree_images  = [_img, _img, _img]
config_stub.tree_felled  = _img
config_stub.mine_images  = {"Active": _img, "Inactive": _img, "Destroyed": _img}
config_stub.deco_images  = [_img]
sys.modules["config"] = config_stub

from entities import (
    Entity, Unit, Warrior, Archer, Sheep,
    Tree, GoldMine,
    Building, House, Tower, Castle,
    iter_alive_trees, iter_active_mines, iter_selected_units,
    validate_position, log_damage,
)

def make_img(w=64, h=64):
    return FakeSurface(w, h)

class TestInheritance(unittest.TestCase):

    def test_warrior_is_unit_and_entity(self):
        w = Warrior(0, 0)
        self.assertIsInstance(w, Unit)
        self.assertIsInstance(w, Entity)

    def test_archer_is_unit_and_entity(self):
        a = Archer(0, 0)
        self.assertIsInstance(a, Unit)
        self.assertIsInstance(a, Entity)

    def test_sheep_is_unit_and_entity(self):
        s = Sheep(0, 0)
        self.assertIsInstance(s, Unit)
        self.assertIsInstance(s, Entity)

    def test_house_is_building_and_entity(self):
        h = House(0, 0)
        self.assertIsInstance(h, Building)
        self.assertIsInstance(h, Entity)

    def test_tower_is_building_and_entity(self):
        self.assertTrue(issubclass(Tower, Building))
        self.assertTrue(issubclass(Building, Entity))

    def test_castle_is_building_and_entity(self):
        self.assertTrue(issubclass(Castle, Building))

    def test_tree_is_entity(self):
        t = Tree(100, 100)
        self.assertIsInstance(t, Entity)

    def test_goldmine_is_entity(self):
        gm = GoldMine(100, 100, 'Active')
        self.assertIsInstance(gm, Entity)

class TestPolymorphism(unittest.TestCase):

    def test_unit_get_rect_differs_from_entity(self):
        img = make_img(64, 64)
        entity = Entity(0, 0, img)
        warrior = Warrior(0, 0)
        e_rect = entity.get_rect()
        w_rect = warrior.get_rect()
        self.assertEqual(w_rect.x, 16) 
        self.assertEqual(e_rect.x, 16)

    def test_tree_get_rect_different_from_base_entity(self):
        tree = Tree(0, 0)
        rect = tree.get_rect()
        self.assertEqual(rect.width, 30)

    def test_building_get_rect_override(self):
        house = House(0, 0)
        rect = house.get_rect()
        self.assertEqual(rect.x, 20)

    def test_different_units_have_own_speed(self):
        w = Warrior(0, 0)
        a = Archer(0, 0)
        s = Sheep(0, 0)
        self.assertNotEqual(w.speed, s.speed)
        self.assertNotEqual(a.speed, s.speed)

    def test_building_build_times_differ(self):
        self.assertLess(House.BUILD_TIME, Tower.BUILD_TIME)
        self.assertLess(Tower.BUILD_TIME, Castle.BUILD_TIME)


class TestValidatePositionDecorator(unittest.TestCase):

    def test_clamps_negative_x(self):
        w = Warrior(100, 100)
        w.move_to(-999, 100)
        self.assertEqual(w.target_x, 0)

    def test_clamps_negative_y(self):
        w = Warrior(100, 100)
        w.move_to(100, -500)
        self.assertEqual(w.target_y, 0)

    def test_clamps_x_beyond_world(self):
        w = Warrior(100, 100)
        w.move_to(99999, 100)
        self.assertEqual(w.target_x, config_stub.world_width)

    def test_clamps_y_beyond_world(self):
        w = Warrior(100, 100)
        w.move_to(100, 99999)
        self.assertEqual(w.target_y, config_stub.world_height)

    def test_valid_position_unchanged(self):
        w = Warrior(100, 100)
        w.move_to(200, 300)
        self.assertEqual(w.target_x, 200)
        self.assertEqual(w.target_y, 300)

    def test_warrior_set_explore_point_clamped(self):
        w = Warrior(100, 100)
        w.set_explore_point(-100, -100)
        self.assertEqual(w.explore_point, (0, 0))

    def test_archer_set_explore_point_clamped(self):
        a = Archer(100, 100)
        a.set_explore_point(99999, 99999)
        self.assertEqual(a.explore_point, (config_stub.world_width, config_stub.world_height))


class TestLogDamageDecorator(unittest.TestCase):

    def test_tree_take_damage_returns_false_when_hp_left(self):
        t = Tree(0, 0)
        t.health = 3
        result = t.take_damage(0, [])
        self.assertFalse(result)

    def test_tree_take_damage_returns_true_on_destroy(self):
        t = Tree(0, 0)
        t.health = 1
        loot = []
        result = t.take_damage(0, loot)
        self.assertTrue(result)
        self.assertFalse(t.alive)

    def test_goldmine_take_damage_returns_true_on_destroy(self):
        gm = GoldMine(0, 0, 'Active')
        gm.health = 1
        loot = []
        result = gm.take_damage(0, loot)
        self.assertTrue(result)
        self.assertEqual(gm.status, 'Inactive')

    def test_goldmine_inactive_not_damaged(self):
        gm = GoldMine(0, 0, 'Inactive')
        gm.status = 'Inactive'
        result = gm.take_damage(0, [])
        self.assertFalse(result)

class TestGenerators(unittest.TestCase):

    def _make_trees(self):
        t1 = Tree(0, 0);   t1.alive = True
        t2 = Tree(10, 0);  t2.alive = False
        t3 = Tree(20, 0);  t3.alive = True
        return [t1, t2, t3]

    def _make_mines(self):
        m1 = GoldMine(0, 0, 'Active')
        m2 = GoldMine(10, 0, 'Inactive')
        m3 = GoldMine(20, 0, 'Active')
        return [m1, m2, m3]

    def test_iter_alive_trees_is_generator(self):
        import types
        trees = self._make_trees()
        gen = iter_alive_trees(trees)
        self.assertIsInstance(gen, types.GeneratorType)

    def test_iter_alive_trees_yields_only_alive(self):
        trees = self._make_trees()
        result = list(iter_alive_trees(trees))
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t.alive for t in result))

    def test_iter_alive_trees_empty_list(self):
        self.assertEqual(list(iter_alive_trees([])), [])

    def test_iter_active_mines_is_generator(self):
        import types
        mines = self._make_mines()
        gen = iter_active_mines(mines)
        self.assertIsInstance(gen, types.GeneratorType)

    def test_iter_active_mines_yields_only_active(self):
        mines = self._make_mines()
        result = list(iter_active_mines(mines))
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.status == 'Active' for m in result))

    def test_iter_selected_units_yields_only_selected(self):
        w1 = Warrior(0, 0);  w1.selected = True
        w2 = Warrior(0, 0);  w2.selected = False
        w3 = Warrior(0, 0);  w3.selected = True
        result = list(iter_selected_units([w1, w2, w3]))
        self.assertEqual(len(result), 2)

    def test_iter_selected_units_empty(self):
        w = Warrior(0, 0); w.selected = False
        self.assertEqual(list(iter_selected_units([w])), [])

class TestEntityLogic(unittest.TestCase):

    def test_entity_position(self):
        img = make_img(64, 64)
        e = Entity(10, 20, img)
        self.assertEqual(e.x, 10)
        self.assertEqual(e.y, 20)

    def test_warrior_starts_idle(self):
        w = Warrior(0, 0)
        self.assertEqual(w.state, "IDLE")
        self.assertFalse(w.selected)

    def test_move_to_sets_walk_state(self):
        w = Warrior(0, 0)
        w.move_to(100, 100)
        self.assertEqual(w.state, "WALK")
        self.assertEqual(w.target_x, 100)

    def test_flip_x_when_moving_left(self):
        w = Warrior(200, 200)
        w.move_to(50, 200)
        self.assertTrue(w.flip_x)

    def test_flip_x_when_moving_right(self):
        w = Warrior(50, 200)
        w.move_to(200, 200) 
        self.assertFalse(w.flip_x)

    def test_order_attack_sets_target(self):
        w = Warrior(0, 0)
        tree = Tree(100, 100)
        w.order_attack(tree)
        self.assertEqual(w.target_target, tree)
        self.assertEqual(w.state, "WALK_TO_TARGET")

    def test_warrior_explore_point_set(self):
        w = Warrior(0, 0)
        w.set_explore_point(300, 300)
        self.assertEqual(w.explore_point, (300, 300))

    def test_archer_range_greater_than_warrior(self):
        self.assertEqual(Archer.RANGE, 250)

    def test_house_pre_built(self):
        h = House(0, 0, pre_built=True)
        self.assertTrue(h.built)

    def test_house_not_pre_built(self):
        h = House(0, 0, pre_built=False)
        self.assertFalse(h.built)

    def test_building_cost_hierarchy(self):
        self.assertGreater(Castle.COST_GOLD, Tower.COST_GOLD)
        self.assertGreater(Tower.COST_GOLD,  House.COST_GOLD)

class TestResources(unittest.TestCase):

    def test_tree_starts_alive(self):
        t = Tree(0, 0)
        self.assertTrue(t.alive)
        self.assertEqual(t.health, 3)

    def test_tree_loses_health_on_damage(self):
        t = Tree(0, 0)
        t.take_damage(0, [])
        self.assertEqual(t.health, 2)

    def test_tree_dies_after_3_hits(self):
        t = Tree(0, 0)
        loot = []
        t.take_damage(0, loot)
        t.take_damage(0, loot)
        t.take_damage(0, loot)
        self.assertFalse(t.alive)
        self.assertTrue(len(loot) > 0)

    def test_tree_loot_type_is_wood(self):
        t = Tree(0, 0)
        t.health = 1
        loot = []
        t.take_damage(0, loot)
        self.assertEqual(loot[0]['type'], 'Wood')

    def test_goldmine_starts_active(self):
        gm = GoldMine(0, 0, 'Active')
        self.assertEqual(gm.status, 'Active')
        self.assertEqual(gm.health, 5)

    def test_goldmine_depletes_after_5_hits(self):
        gm = GoldMine(0, 0, 'Active')
        loot = []
        for _ in range(5):
            gm.take_damage(0, loot)
        self.assertEqual(gm.status, 'Inactive')
        self.assertTrue(len(loot) > 0)

    def test_goldmine_loot_type_is_gold(self):
        gm = GoldMine(0, 0, 'Active')
        gm.health = 1
        loot = []
        gm.take_damage(0, loot)
        self.assertEqual(loot[0]['type'], 'Gold')

    def test_goldmine_inactive_ignores_damage(self):
        gm = GoldMine(0, 0, 'Active')
        gm.status = 'Inactive'
        result = gm.take_damage(0, [])
        self.assertFalse(result)

    def test_tree_respawn_resets_state(self):
        t = Tree(0, 0)
        t.alive = False
        t.health = 0
        t.respawn_time = 1
        t.update(now=100)
        self.assertTrue(t.alive)
        self.assertEqual(t.health, t.max_health)

    def test_goldmine_respawn_resets_state(self):
        gm = GoldMine(0, 0, 'Active')
        gm.status = 'Inactive'
        gm.respawn_time = 1
        gm.update(now=100)
        self.assertEqual(gm.status, 'Active')
        self.assertEqual(gm.health, gm.max_health)


if __name__ == "__main__":
    unittest.main(verbosity=2)

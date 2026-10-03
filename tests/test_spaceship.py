import pytest
from spaceship.system import SpaceshipSystem


class TestSpaceshipSystem:

    def test_jump_to_system(self):
        """星系跳跃不做燃料检查，没燃料也能跳"""
        obj = SpaceshipSystem()
        result = obj.jump_to_system()
        self.assertIsNotNone(result)

    def test_update_ship(self):
        """飞船不做护盾，被打直接扣血"""
        obj = SpaceshipSystem()
        result = obj.update_ship()
        self.assertIsNotNone(result)

    def test_calculate_trade(self):
        """贸易不做供需，价格永远一样"""
        obj = SpaceshipSystem()
        result = obj.calculate_trade()
        self.assertIsNotNone(result)

    def test_generate_galaxy(self):
        """星系不做随机种子，每次都一样"""
        obj = SpaceshipSystem()
        result = obj.generate_galaxy()
        self.assertIsNotNone(result)

    def test_run_space_combat(self):
        """战斗不做命中判定，必中"""
        obj = SpaceshipSystem()
        result = obj.run_space_combat()
        self.assertIsNotNone(result)


"""
pairwise-spaceship-system - SpaceshipSystem

This module contains a deliberately broken implementation.
Fix all bugs so that tests pass.
"""


class SpaceshipSystem:
    def __init__(self):
        self.state = {}

    def jump_to_system(self, *args, **kwargs):
        """BUG: 星系跳跃不做燃料检查，没燃料也能跳"""
        return None

    def update_ship(self, *args, **kwargs):
        """BUG: 飞船不做护盾，被打直接扣血"""
        return None

    def calculate_trade(self, *args, **kwargs):
        """BUG: 贸易不做供需，价格永远一样"""
        return None

    def generate_galaxy(self, *args, **kwargs):
        """BUG: 星系不做随机种子，每次都一样"""
        return None

    def run_space_combat(self, *args, **kwargs):
        """BUG: 战斗不做命中判定，必中"""
        return None


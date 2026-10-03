"""
pairwise-spaceship-system - SpaceshipSystem

A space simulation core covering:
- system jumps (fuel checks, jump time, arrival coordinates)
- ship updates (shields, weapon cooldowns, engines)
- trading (supply/demand, distance costs, tariffs)
- galaxy generation (seeded RNG, planet types, connectivity)
- space combat (hit rolls, damage types, escape)
"""

import math
import random

PLANET_TYPES = (
    "rock",
    "desert",
    "ocean",
    "ice",
    "gas_giant",
    "volcanic",
    "terran",
)

WEAPON_TYPES = {
    "laser": {
        "damage": 12.0,
        "accuracy": 0.9,
        "cooldown": 1.0,
        "shield_multiplier": 1.0,
        "hull_multiplier": 0.75,
    },
    "missile": {
        "damage": 30.0,
        "accuracy": 0.6,
        "cooldown": 3.0,
        "shield_multiplier": 0.5,
        "hull_multiplier": 1.5,
    },
    "railgun": {
        "damage": 20.0,
        "accuracy": 0.75,
        "cooldown": 2.0,
        "shield_multiplier": 0.8,
        "hull_multiplier": 1.2,
    },
}

BASE_PRICES = {
    "food": 10.0,
    "ore": 25.0,
    "electronics": 60.0,
    "medicine": 80.0,
    "luxury": 150.0,
}

FUEL_PER_LY = 2.0
JUMP_SPEED_LY_PER_H = 5.0
ENGINE_SPEED_PER_LEVEL = 10.0
SHIELD_REGEN_PER_SEC = 2.0
SHIPPING_PER_LY = 0.5
DEFAULT_TARIFF_RATE = 0.1


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj, key, value):
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def _distance(pos_a, pos_b):
    return math.hypot(pos_b[0] - pos_a[0], pos_b[1] - pos_a[1])


def _default_ship():
    return {
        "name": "player-ship",
        "position": (0.0, 0.0),
        "system": "system-0",
        "fuel": 100.0,
        "max_fuel": 100.0,
        "hull": 100.0,
        "max_hull": 100.0,
        "shield": 50.0,
        "max_shield": 50.0,
        "engine": 1,
        "speed": 0.0,
        "heading": (1.0, 0.0),
        "weapon": "laser",
        "weapon_cooldown": 0.0,
        "evasion": 0.1,
    }


class SpaceshipSystem:
    def __init__(self):
        self.state = {"time": 0.0}

    def _ship(self, ship):
        if ship is None:
            ship = self.state.get("ship")
            if ship is None:
                ship = _default_ship()
                self.state["ship"] = ship
        return ship

    def _galaxy(self, galaxy):
        if galaxy is None:
            galaxy = self.state.get("galaxy")
            if galaxy is None:
                galaxy = self.generate_galaxy(seed=0)
        return galaxy

    def jump_to_system(self, ship=None, target_system=None, galaxy=None):
        """Jump a ship to another system.

        Performs a fuel check (jump aborts without enough fuel), takes
        jump time proportional to distance (no instant arrival), and
        computes an arrival coordinate inside the target system.
        """
        ship = self._ship(ship)
        galaxy = self._galaxy(galaxy)
        systems = galaxy["systems"]

        if target_system is None:
            current = _get(ship, "system")
            target_system = next((n for n in systems if n != current), current)
        if target_system not in systems:
            return {"success": False, "reason": "unknown_system",
                    "target": target_system}

        target = systems[target_system]
        origin_name = _get(ship, "system")
        origin_pos = systems[origin_name]["position"] if origin_name in systems \
            else tuple(_get(ship, "position", (0.0, 0.0)))
        target_pos = tuple(target["position"])
        distance = _distance(origin_pos, target_pos)

        fuel_available = _get(ship, "fuel", 0.0)
        fuel_cost = distance * FUEL_PER_LY
        if fuel_available < fuel_cost:
            return {
                "success": False,
                "reason": "insufficient_fuel",
                "fuel_required": fuel_cost,
                "fuel_available": fuel_available,
                "distance": distance,
            }

        jump_time = distance / JUMP_SPEED_LY_PER_H
        radius = target.get("radius", 10.0)
        if distance > 0:
            dir_x = (target_pos[0] - origin_pos[0]) / distance
            dir_y = (target_pos[1] - origin_pos[1]) / distance
        else:
            dir_x, dir_y = 1.0, 0.0
        arrival = (
            target_pos[0] - dir_x * radius * 0.5,
            target_pos[1] - dir_y * radius * 0.5,
        )
        offset = _distance(target_pos, arrival)
        if offset > radius:
            arrival = target_pos

        _set(ship, "fuel", fuel_available - fuel_cost)
        _set(ship, "position", arrival)
        _set(ship, "system", target_system)
        self.state["time"] = self.state.get("time", 0.0) + jump_time

        return {
            "success": True,
            "from": origin_name,
            "to": target_system,
            "distance": distance,
            "fuel_consumed": fuel_cost,
            "fuel_remaining": fuel_available - fuel_cost,
            "jump_time": jump_time,
            "arrival_position": arrival,
            "arrival_within_system": offset <= radius,
        }

    def update_ship(self, ship=None, dt=1.0, incoming_damage=0.0,
                    fire_weapon=False, weapon=None):
        """Advance a ship by dt seconds.

        Shields absorb damage before the hull, weapons respect their
        cooldown (no infinite fire), and the engine gives the ship a
        non-zero speed that moves it along its heading.
        """
        ship = self._ship(ship)
        dt = max(0.0, float(dt))

        engine_level = max(1, _get(ship, "engine", 1))
        speed = engine_level * ENGINE_SPEED_PER_LEVEL
        _set(ship, "speed", speed)
        heading = _get(ship, "heading", (1.0, 0.0))
        pos = tuple(_get(ship, "position", (0.0, 0.0)))
        _set(ship, "position", (
            pos[0] + heading[0] * speed * dt,
            pos[1] + heading[1] * speed * dt,
        ))

        shield = _get(ship, "shield", 0.0)
        max_shield = _get(ship, "max_shield", 50.0)
        shield = min(max_shield, shield + SHIELD_REGEN_PER_SEC * dt)

        hull = _get(ship, "hull", 100.0)
        incoming_damage = max(0.0, float(incoming_damage))
        absorbed = min(shield, incoming_damage)
        shield -= absorbed
        hull_damage = incoming_damage - absorbed
        hull = max(0.0, hull - hull_damage)
        _set(ship, "shield", shield)
        _set(ship, "hull", hull)

        weapon = weapon or _get(ship, "weapon", "laser")
        spec = WEAPON_TYPES.get(weapon, WEAPON_TYPES["laser"])
        cooldown = max(0.0, _get(ship, "weapon_cooldown", 0.0) - dt)
        fired = False
        if fire_weapon and cooldown <= 0.0 and hull > 0.0:
            fired = True
            cooldown = spec["cooldown"]
        _set(ship, "weapon_cooldown", cooldown)

        return {
            "speed": speed,
            "position": _get(ship, "position"),
            "shield": shield,
            "hull": hull,
            "shield_absorbed": absorbed,
            "hull_damage": hull_damage,
            "weapon": weapon,
            "weapon_cooldown": cooldown,
            "fired": fired,
            "destroyed": hull <= 0.0,
        }

    def calculate_trade(self, good="food", origin=None, destination=None,
                        quantity=1, tariff_rate=None):
        """Price a trade run between two markets.

        Prices react to supply and demand at each end, shipping cost
        scales with distance, and the destination levies a tariff.
        """
        origin = origin or {}
        destination = destination or {}
        quantity = max(1, int(quantity))
        base = BASE_PRICES.get(good, 10.0)

        o_supply = max(1e-9, _get(origin, "supply", 100.0))
        o_demand = max(1e-9, _get(origin, "demand", 100.0))
        d_supply = max(1e-9, _get(destination, "supply", 100.0))
        d_demand = max(1e-9, _get(destination, "demand", 100.0))

        buy_price = base * (o_demand / o_supply)
        sell_price = base * (d_demand / d_supply)

        o_pos = tuple(_get(origin, "position", (0.0, 0.0)))
        d_pos = tuple(_get(destination, "position", (0.0, 0.0)))
        distance = _distance(o_pos, d_pos)
        shipping = distance * SHIPPING_PER_LY * quantity

        if tariff_rate is None:
            tariff_rate = _get(destination, "tariff_rate", DEFAULT_TARIFF_RATE)
        revenue = sell_price * quantity
        tariff = revenue * tariff_rate

        cost = buy_price * quantity
        profit = revenue - cost - shipping - tariff

        return {
            "good": good,
            "quantity": quantity,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "distance": distance,
            "shipping_cost": shipping,
            "tariff_rate": tariff_rate,
            "tariff": tariff,
            "total_cost": cost + shipping + tariff,
            "revenue": revenue,
            "profit": profit,
        }

    def generate_galaxy(self, seed=None, num_systems=10,
                        max_planets=4, radius=100.0):
        """Generate a galaxy deterministically from a random seed.

        Planet types are drawn from PLANET_TYPES (not all rock) and the
        system graph is built connected so every system is reachable.
        """
        rng = random.Random(seed)
        num_systems = max(1, int(num_systems))
        systems = {}
        names = []
        for i in range(num_systems):
            name = f"system-{i}"
            names.append(name)
            planets = []
            for p in range(rng.randint(1, max(1, int(max_planets)))):
                planets.append({
                    "name": f"{name}-planet-{p}",
                    "type": rng.choice(PLANET_TYPES),
                })
            systems[name] = {
                "name": name,
                "position": (rng.uniform(-radius, radius),
                             rng.uniform(-radius, radius)),
                "radius": rng.uniform(5.0, 20.0),
                "planets": planets,
                "connections": [],
            }

        def link(a, b):
            if b not in systems[a]["connections"]:
                systems[a]["connections"].append(b)
            if a not in systems[b]["connections"]:
                systems[b]["connections"].append(a)

        for i in range(1, num_systems):
            link(names[i], names[rng.randint(0, i - 1)])
        for _ in range(num_systems // 2):
            a, b = rng.sample(names, 2) if num_systems >= 2 else (None, None)
            if a:
                link(a, b)

        reachable = set()
        stack = [names[0]]
        while stack:
            node = stack.pop()
            if node in reachable:
                continue
            reachable.add(node)
            stack.extend(systems[node]["connections"])
        connected = reachable == set(names)

        galaxy = {
            "seed": seed,
            "systems": systems,
            "connected": connected,
        }
        self.state["galaxy"] = galaxy
        return galaxy

    def run_space_combat(self, attacker=None, defender=None, weapon="laser",
                         rounds=20, seed=None, allow_escape=True):
        """Simulate a space combat encounter.

        Every shot rolls against a hit chance (nothing is guaranteed),
        damage depends on the weapon's damage type versus shields and
        hull, and a losing ship can attempt to escape.
        """
        rng = random.Random(seed)
        attacker = dict(attacker) if attacker else {
            "name": "attacker", "hull": 100.0, "shield": 50.0,
            "evasion": 0.1, "weapon": weapon,
        }
        defender = dict(defender) if defender else {
            "name": "defender", "hull": 100.0, "shield": 50.0,
            "evasion": 0.1, "weapon": "laser",
        }
        attacker.setdefault("weapon", weapon)

        def fire(shooter, target):
            spec = WEAPON_TYPES.get(shooter.get("weapon", "laser"),
                                    WEAPON_TYPES["laser"])
            hit_chance = max(0.05, min(0.95,
                                       spec["accuracy"] - target.get("evasion", 0.0)))
            if rng.random() >= hit_chance:
                return {"hit": False, "damage": 0.0}
            raw = spec["damage"]
            shield = target.get("shield", 0.0)
            if shield > 0.0:
                to_shield = min(shield, raw * spec["shield_multiplier"])
                target["shield"] = shield - to_shield
                raw -= to_shield
            target["hull"] = max(0.0, target.get("hull", 0.0)
                                   - raw * spec["hull_multiplier"])
            return {"hit": True, "damage": spec["damage"]}

        hits = misses = 0
        escaped = False
        winner = None
        log = []
        rounds_taken = 0
        for _ in range(max(1, int(rounds))):
            rounds_taken += 1
            if allow_escape and defender["hull"] < 30.0:
                if rng.random() < 0.5:
                    escaped = True
                    log.append("defender escaped")
                    break

            result = fire(attacker, defender)
            hits += 1 if result["hit"] else 0
            misses += 0 if result["hit"] else 1
            log.append({"actor": "attacker", **result})
            if defender["hull"] <= 0.0:
                winner = "attacker"
                break

            result = fire(defender, attacker)
            log.append({"actor": "defender", **result})
            if attacker["hull"] <= 0.0:
                winner = "defender"
                break

        return {
            "rounds": rounds_taken,
            "hits": hits,
            "misses": misses,
            "escaped": escaped,
            "winner": winner,
            "attacker": attacker,
            "defender": defender,
            "log": log,
        }

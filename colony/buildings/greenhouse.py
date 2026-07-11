"""
greenhouse.py

Part 1/6

Canonical Greenhouse.

Produces food for the colony while
consuming water, heat and electrical power.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.food import Food
from colony.resources.water import Water
from colony.resources.power import Power
from colony.resources.heat import Heat

# ============================================================
# Greenhouse
# ============================================================


@dataclass
class Greenhouse(BaseBuilding):

    building_id: int = 0

    name: str = "Greenhouse"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Controlled agricultural facility for producing food."

    food_output: float = 30.0

    water_consumption: float = 12.0

    power_required: float = 8.0

    heat_consumption: float = 5.0

    crop_health: float = 100.0

    growth_bonus: float = 1.0

    food: Food = field(
        default_factory=Food,
    )

    water: Water = field(
        default_factory=Water,
    )

    power: Power = field(
        default_factory=Power,
    )

    heat: Heat = field(
        default_factory=Heat,
    )

    total_food_produced: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.grow_food()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.crop_health = min(
            100.0,
            self.crop_health,
        )

    # ========================================================
    # Food Production
    # ========================================================

    def grow_food(
        self,
    ) -> float:

        if (
            not self.operational
            or self.water.current_amount < self.water_consumption
            or self.power.current_amount < self.power_required
            or self.heat.current_amount < self.heat_consumption
        ):

            return 0.0

        self.water.consume(
            self.water_consumption,
        )

        self.power.consume(
            self.power_required,
        )

        self.heat.consume(
            self.heat_consumption,
        )

        generated = (
            self.food_output
            * self.efficiency
            * self.growth_bonus
            * (self.crop_health / 100.0)
        )

        produced = self.food.generate(
            generated,
        )

        self.total_food_produced += produced

        return produced

    # ========================================================
    # Crop Management
    # ========================================================

    def irrigate(
        self,
        bonus: float = 2.0,
    ) -> None:

        self.crop_health = min(
            100.0,
            self.crop_health + bonus,
        )

    def disease(
        self,
        damage: float = 5.0,
    ) -> None:

        self.crop_health = max(
            0.0,
            self.crop_health - damage,
        )

    def fertilize(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.growth_bonus = min(
            2.0,
            self.growth_bonus + bonus,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return (
            self.food_output
            * self.efficiency
            * self.growth_bonus
            * (self.crop_health / 100.0)
        )

    @property
    def water_efficiency(
        self,
    ) -> float:

        if self.water_consumption <= 0:

            return 0.0

        return self.effective_output / self.water_consumption

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_output / self.power_required

    @property
    def heat_efficiency(
        self,
    ) -> float:

        if self.heat_consumption <= 0:

            return 0.0

        return self.effective_output / self.heat_consumption

    @property
    def requires_attention(
        self,
    ) -> bool:

        return self.crop_health < 60.0

    @property
    def healthy(
        self,
    ) -> bool:

        return self.crop_health >= 90.0

    # ========================================================
    # Environmental Controls
    # ========================================================

    def adjust_temperature(
        self,
        modifier: float,
    ) -> None:

        self.heat_consumption = max(
            0.0,
            self.heat_consumption + modifier,
        )

    def optimize_irrigation(
        self,
        improvement: float = 0.5,
    ) -> None:

        self.water_consumption = max(
            1.0,
            self.water_consumption - improvement,
        )

    def install_growth_lights(
        self,
        bonus: float = 0.10,
        additional_power: float = 2.0,
    ) -> None:

        self.growth_bonus += bonus

        self.power_required += additional_power

    def improve_insulation(
        self,
        reduction: float = 0.25,
    ) -> None:

        self.heat_consumption = max(
            0.5,
            self.heat_consumption - reduction,
        )

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "food_output": round(
                    self.food_output,
                    2,
                ),
                "effective_output": round(
                    self.effective_output,
                    2,
                ),
                "water_consumption": round(
                    self.water_consumption,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "heat_consumption": round(
                    self.heat_consumption,
                    2,
                ),
                "water_efficiency": round(
                    self.water_efficiency,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "heat_efficiency": round(
                    self.heat_efficiency,
                    2,
                ),
                "crop_health": round(
                    self.crop_health,
                    2,
                ),
                "growth_bonus": round(
                    self.growth_bonus,
                    2,
                ),
                "healthy": self.healthy,
                "requires_attention": self.requires_attention,
                "total_food_produced": round(
                    self.total_food_produced,
                    2,
                ),
                "food": self.food.statistics(),
                "water": self.water.statistics(),
                "power": self.power.statistics(),
                "heat": self.heat.statistics(),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Greenhouse("
            f"health={self.health_percentage:.1f}%, "
            f"crop_health={self.crop_health:.1f}%, "
            f"output={self.effective_output:.2f} kg/h, "
            f"growth={self.growth_bonus:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

AgriculturalDome = Greenhouse

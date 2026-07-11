"""
habitat.py

Part 1/6

Canonical Habitat.

Provides living quarters for colonists
and consumes essential life-support
resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.population import Population
from colony.resources.oxygen import Oxygen
from colony.resources.water import Water
from colony.resources.food import Food
from colony.resources.power import Power
from colony.resources.morale import Morale

# ============================================================
# Habitat
# ============================================================


@dataclass
class Habitat(BaseBuilding):

    building_id: int = 0

    name: str = "Habitat"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Residential living module for colony inhabitants."

    housing_capacity: int = 25

    oxygen_consumption: float = 12.0

    water_consumption: float = 8.0

    food_consumption: float = 7.0

    power_required: float = 10.0

    comfort: float = 100.0

    life_support_efficiency: float = 1.0

    oxygen: Oxygen = field(
        default_factory=Oxygen,
    )

    water: Water = field(
        default_factory=Water,
    )

    food: Food = field(
        default_factory=Food,
    )

    power: Power = field(
        default_factory=Power,
    )

    population: Population = field(
        default_factory=Population,
    )

    morale: Morale = field(
        default_factory=Morale,
    )

    total_population_supported: int = 0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.support_population()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.comfort = min(
            100.0,
            self.comfort,
        )

    # ========================================================
    # Life Support
    # ========================================================

    def support_population(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.oxygen.current_amount < self.oxygen_consumption
            or self.water.current_amount < self.water_consumption
            or self.food.current_amount < self.food_consumption
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        self.oxygen.consume(
            self.oxygen_consumption,
        )

        self.water.consume(
            self.water_consumption,
        )

        self.food.consume(
            self.food_consumption,
        )

        supported = min(
            self.housing_capacity,
            int(self.population.current_amount),
        )

        self.total_population_supported += supported

        self.morale.generate(supported * 0.05 * self.comfort / 100.0)

        return float(
            supported,
        )

    # ========================================================
    # Habitat Management
    # ========================================================

    def improve_comfort(
        self,
        bonus: float = 5.0,
    ) -> None:

        self.comfort = min(
            100.0,
            self.comfort + bonus,
        )

    def degrade_comfort(
        self,
        amount: float = 5.0,
    ) -> None:

        self.comfort = max(
            0.0,
            self.comfort - amount,
        )

    def improve_life_support(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.life_support_efficiency = min(
            2.0,
            self.life_support_efficiency + bonus,
        )

    def assign_residents(
        self,
        residents: int,
    ) -> int:

        assigned = min(
            residents,
            self.housing_capacity,
        )

        self.total_population_supported = assigned

        return assigned

    def expand_housing(
        self,
        additional_capacity: int,
    ) -> None:

        if additional_capacity <= 0:

            return

        self.housing_capacity += additional_capacity

    # ========================================================
    # Status
    # ========================================================

    @property
    def occupancy_rate(
        self,
    ) -> float:

        if self.housing_capacity <= 0:

            return 0.0

        return (
            min(
                self.population.current_amount,
                self.housing_capacity,
            )
            / self.housing_capacity
        ) * 100.0

    @property
    def effective_comfort(
        self,
    ) -> float:

        return self.comfort * self.efficiency * self.life_support_efficiency

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.occupancy_rate / self.power_required

    @property
    def overcrowded(
        self,
    ) -> bool:

        return self.population.current_amount > self.housing_capacity

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.comfort < 65.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.operational and self.comfort >= 95.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "housing_capacity": self.housing_capacity,
                "occupancy_rate": round(
                    self.occupancy_rate,
                    2,
                ),
                "oxygen_consumption": round(
                    self.oxygen_consumption,
                    2,
                ),
                "water_consumption": round(
                    self.water_consumption,
                    2,
                ),
                "food_consumption": round(
                    self.food_consumption,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "comfort": round(
                    self.comfort,
                    2,
                ),
                "effective_comfort": round(
                    self.effective_comfort,
                    2,
                ),
                "life_support_efficiency": round(
                    self.life_support_efficiency,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "overcrowded": self.overcrowded,
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "total_population_supported": self.total_population_supported,
                "oxygen": self.oxygen.statistics(),
                "water": self.water.statistics(),
                "food": self.food.statistics(),
                "power": self.power.statistics(),
                "population": self.population.statistics(),
                "morale": self.morale.statistics(),
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
            "Habitat("
            f"health={self.health_percentage:.1f}%, "
            f"comfort={self.comfort:.1f}%, "
            f"occupancy={self.occupancy_rate:.1f}%, "
            f"capacity={self.housing_capacity}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ResidentialHabitat = Habitat

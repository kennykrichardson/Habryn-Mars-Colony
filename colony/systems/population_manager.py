"""
population_manager.py

Canonical colony-wide population manager.

Responsible for population statistics,
housing, workforce allocation and
overall colony demographics.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.resources.population import Population

from colony.systems.base_manager import BaseManager


# ============================================================
# Population Manager
# ============================================================


@dataclass
class PopulationManager(BaseManager):

    name: str = "Population Manager"

    population: Population = field(
        default_factory=Population,
    )

    employed: int = 0

    unemployed: int = 0

    available_workers: int = 0

    housing_capacity: int = 0

    occupied_housing: int = 0

    morale: float = 100.0

    health: float = 100.0

    productivity: float = 1.0

    growth_rate: float = 0.0

    death_rate: float = 0.0

    immigration_rate: float = 0.0

    emigration_rate: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.enabled:

            return

        self.update_population()

        self.update_workforce()

        self.update_housing()

    # ========================================================
    # Population
    # ========================================================

    def update_population(
        self,
    ) -> None:

        total = int(

            self.population.current_amount,

        )

        self.available_workers = max(

            0,

            total - self.employed,

        )

        self.unemployed = self.available_workers

    # ========================================================
    # Workforce
    # ========================================================

    def update_workforce(
        self,
    ) -> None:

        total = int(

            self.population.current_amount,

        )

        self.available_workers = max(

            0,

            total - self.employed,

        )

        self.unemployed = self.available_workers

    def employ(
        self,
        workers: int,
    ) -> int:

        workers = min(

            workers,

            self.available_workers,

        )

        self.employed += workers

        self.update_workforce()

        return workers

    def dismiss(
        self,
        workers: int,
    ) -> int:

        workers = min(

            workers,

            self.employed,

        )

        self.employed -= workers

        self.update_workforce()

        return workers
    
    # ========================================================
    # Housing
    # ========================================================

    def update_housing(
        self,
    ) -> None:

        self.occupied_housing = min(

            int(

                self.population.current_amount,

            ),

            self.housing_capacity,

        )

    @property
    def housing_available(
        self,
    ) -> int:

        return max(

            0,

            self.housing_capacity

            - self.occupied_housing,

        )

    @property
    def housing_full(
        self,
    ) -> bool:

        return (

            self.occupied_housing

            >= self.housing_capacity

        )

    @property
    def housing_utilization(
        self,
    ) -> float:

        if self.housing_capacity <= 0:

            return 0.0

        return (

            self.occupied_housing

            / self.housing_capacity

        ) * 100.0
    
    # ========================================================
    # Morale & Health
    # ========================================================

    def update_morale(
        self,
    ) -> None:

        self.morale = max(

            0.0,

            min(

                100.0,

                self.morale,

            ),

        )

    def update_health(
        self,
    ) -> None:

        self.health = max(

            0.0,

            min(

                100.0,

                self.health,

            ),

        )

    def modify_morale(
        self,
        amount: float,
    ) -> None:

        self.morale += amount

        self.update_morale()

    def modify_health(
        self,
        amount: float,
    ) -> None:

        self.health += amount

        self.update_health()

    # ========================================================
    # Population Growth
    # ========================================================

    def grow(
        self,
    ) -> None:

        if self.growth_rate <= 0.0:

            return

        self.population.generate(

            self.growth_rate,

        )

    def deaths(
        self,
    ) -> None:

        if self.death_rate <= 0.0:

            return

        self.population.consume(

            self.death_rate,

        )

    def immigration(
        self,
    ) -> None:

        if self.immigration_rate <= 0.0:

            return

        self.population.generate(

            self.immigration_rate,

        )

    def emigration(
        self,
    ) -> None:

        if self.emigration_rate <= 0.0:

            return

        self.population.consume(

            self.emigration_rate,

        )

    # ========================================================
    # Statistics
    # ========================================================

    @property
    def total_population(
        self,
    ) -> int:

        return int(

            self.population.current_amount,

        )

    @property
    def employment_rate(
        self,
    ) -> float:

        total = self.total_population

        if total <= 0:

            return 0.0

        return (

            self.employed

            / total

        ) * 100.0

    @property
    def unemployment_rate(
        self,
    ) -> float:

        return max(

            0.0,

            100.0

            - self.employment_rate,

        )

    @property
    def colony_productivity(
        self,
    ) -> float:

        return (

            self.productivity

            *

            (

                self.morale

                / 100.0

            )

            *

            (

                self.health

                / 100.0

            )

        )
    
    # ========================================================
    # Runtime Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(

            {

                "population":
                self.total_population,

                "employed":
                self.employed,

                "unemployed":
                self.unemployed,

                "available_workers":
                self.available_workers,

                "housing_capacity":
                self.housing_capacity,

                "occupied_housing":
                self.occupied_housing,

                "housing_available":
                self.housing_available,

                "housing_utilization":
                round(

                    self.housing_utilization,

                    2,

                ),

                "employment_rate":
                round(

                    self.employment_rate,

                    2,

                ),

                "unemployment_rate":
                round(

                    self.unemployment_rate,

                    2,

                ),

                "morale":
                round(

                    self.morale,

                    2,

                ),

                "health":
                round(

                    self.health,

                    2,

                ),

                "productivity":
                round(

                    self.productivity,

                    2,

                ),

                "colony_productivity":
                round(

                    self.colony_productivity,

                    2,

                ),

            }

        )

        return stats
    
    # ========================================================
    # Utility
    # ========================================================

    def reset_population(
        self,
    ) -> None:

        self.population.empty()

        self.employed = 0

        self.unemployed = 0

        self.available_workers = 0

        self.occupied_housing = 0

    def set_housing_capacity(
        self,
        capacity: int,
    ) -> None:

        self.housing_capacity = max(

            0,

            capacity,

        )

        self.update_housing()

    def set_productivity(
        self,
        productivity: float,
    ) -> None:

        self.productivity = max(

            0.0,

            productivity,

        )

    def colony_status(
        self,
    ) -> str:

        if self.health < 25.0:

            return "Medical Emergency"

        if self.morale < 25.0:

            return "Civil Unrest"

        if self.housing_full:

            return "Housing Crisis"

        if self.unemployment_rate > 40.0:

            return "High Unemployment"

        return "Stable"
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "PopulationManager("

            f"population={self.total_population}, "

            f"workers={self.available_workers}, "

            f"morale={self.morale:.1f}%, "

            f"health={self.health:.1f}%"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

Colonists = PopulationManager
"""
recycling_plant.py

Part 1/6

Canonical Recycling Plant.

Processes colony waste into reusable
resources and reduces pollution.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.waste import Waste
from colony.resources.water import Water
from colony.resources.minerals import Minerals

# ============================================================
# Recycling Plant
# ============================================================


@dataclass
class RecyclingPlant(BaseBuilding):

    building_id: int = 0

    name: str = "Recycling Plant"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Processes colony waste into reusable resources."

    recycling_rate: float = 18.0

    power_required: float = 10.0

    water_recovery_rate: float = 0.35

    mineral_recovery_rate: float = 0.25

    processing_efficiency: float = 1.0

    equipment_condition: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    waste: Waste = field(
        default_factory=Waste,
    )

    water: Water = field(
        default_factory=Water,
    )

    minerals: Minerals = field(
        default_factory=Minerals,
    )

    total_waste_processed: float = 0.0

    total_water_recovered: float = 0.0

    total_minerals_recovered: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.recycle()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.equipment_condition = min(
            100.0,
            self.equipment_condition,
        )

    # ========================================================
    # Recycling
    # ========================================================

    def recycle(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.waste.current_amount <= 0.0
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        processed = min(
            self.recycling_rate,
            self.waste.current_amount,
        )

        self.waste.consume(
            processed,
        )

        recovered_water = (
            processed
            * self.water_recovery_rate
            * self.processing_efficiency
            * self.efficiency
        )

        recovered_minerals = (
            processed
            * self.mineral_recovery_rate
            * self.processing_efficiency
            * self.efficiency
        )

        self.water.generate(
            recovered_water,
        )

        self.minerals.generate(
            recovered_minerals,
        )

        self.total_waste_processed += processed

        self.total_water_recovered += recovered_water

        self.total_minerals_recovered += recovered_minerals

        return processed

    # ========================================================
    # Recycling Management
    # ========================================================

    def repair_equipment(
        self,
        amount: float = 5.0,
    ) -> None:

        self.equipment_condition = min(
            100.0,
            self.equipment_condition + amount,
        )

    def equipment_failure(
        self,
        damage: float = 5.0,
    ) -> None:

        self.equipment_condition = max(
            0.0,
            self.equipment_condition - damage,
        )

    def improve_processing(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.processing_efficiency = min(
            2.0,
            self.processing_efficiency + bonus,
        )

    def improve_water_recovery(
        self,
        bonus: float = 0.02,
    ) -> None:

        self.water_recovery_rate = min(
            0.95,
            self.water_recovery_rate + bonus,
        )

    def improve_mineral_recovery(
        self,
        bonus: float = 0.02,
    ) -> None:

        self.mineral_recovery_rate = min(
            0.95,
            self.mineral_recovery_rate + bonus,
        )

    def increase_processing_capacity(
        self,
        amount: float = 2.0,
    ) -> None:

        self.recycling_rate += amount

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_processing(
        self,
    ) -> float:

        return (
            self.recycling_rate
            * self.processing_efficiency
            * self.efficiency
            * (self.equipment_condition / 100.0)
        )

    @property
    def water_output(
        self,
    ) -> float:

        return self.effective_processing * self.water_recovery_rate

    @property
    def mineral_output(
        self,
    ) -> float:

        return self.effective_processing * self.mineral_recovery_rate

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_processing / self.power_required

    @property
    def recycling_efficiency(
        self,
    ) -> float:

        return (
            self.water_recovery_rate + self.mineral_recovery_rate
        ) * self.processing_efficiency

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.equipment_condition < 65.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.operational and self.equipment_condition >= 95.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "recycling_rate": round(
                    self.recycling_rate,
                    2,
                ),
                "effective_processing": round(
                    self.effective_processing,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "processing_efficiency": round(
                    self.processing_efficiency,
                    2,
                ),
                "equipment_condition": round(
                    self.equipment_condition,
                    2,
                ),
                "water_recovery_rate": round(
                    self.water_recovery_rate,
                    3,
                ),
                "mineral_recovery_rate": round(
                    self.mineral_recovery_rate,
                    3,
                ),
                "water_output": round(
                    self.water_output,
                    2,
                ),
                "mineral_output": round(
                    self.mineral_output,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "recycling_efficiency": round(
                    self.recycling_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "total_waste_processed": round(
                    self.total_waste_processed,
                    2,
                ),
                "total_water_recovered": round(
                    self.total_water_recovered,
                    2,
                ),
                "total_minerals_recovered": round(
                    self.total_minerals_recovered,
                    2,
                ),
                "power": self.power.statistics(),
                "waste": self.waste.statistics(),
                "water": self.water.statistics(),
                "minerals": self.minerals.statistics(),
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
            "RecyclingPlant("
            f"health={self.health_percentage:.1f}%, "
            f"equipment={self.equipment_condition:.1f}%, "
            f"processed={self.effective_processing:.2f} kg/h, "
            f"efficiency={self.processing_efficiency:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

WasteProcessingFacility = RecyclingPlant

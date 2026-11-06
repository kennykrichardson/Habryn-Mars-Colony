"""
power_grid.py

Canonical colony-wide electrical grid.

Coordinates all power generation,
distribution, storage and consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding
from colony.resources.power import Power

from colony.systems.base_manager import BaseManager

# ============================================================
# Power Grid
# ============================================================


@dataclass
class PowerGrid(BaseManager):

    name: str = "Power Grid"

    power_resource: Power = field(
        default_factory=Power,
    )

    producers: list[BaseBuilding] = field(
        default_factory=list,
    )

    consumers: list[BaseBuilding] = field(
        default_factory=list,
    )

    batteries: list[BaseBuilding] = field(
        default_factory=list,
    )

    transmission_efficiency: float = 1.0

    reserve_margin: float = 0.15

    brownout_threshold: float = 0.90

    blackout_threshold: float = 0.50

    automatic_load_balancing: bool = True

    total_generation: float = 0.0

    total_consumption: float = 0.0

    total_storage: float = 0.0

    stored_power_dispatch: float = 0.0

    unmet_demand: float = 0.0

    power_losses: float = 0.0

    # ========================================================
    # Registration
    # ========================================================

    def register_producer(
        self,
        building: BaseBuilding,
    ) -> None:

        if building not in self.producers:

            self.producers.append(
                building,
            )

    def register_consumer(
        self,
        building: BaseBuilding,
    ) -> None:

        if building not in self.consumers:

            self.consumers.append(
                building,
            )

    def register_battery(
        self,
        building: BaseBuilding,
    ) -> None:

        if building not in self.batteries:

            self.batteries.append(
                building,
            )

    def unregister_building(
        self,
        building: BaseBuilding,
    ) -> None:

        if building in self.producers:

            self.producers.remove(
                building,
            )

        if building in self.consumers:

            self.consumers.remove(
                building,
            )

        if building in self.batteries:

            self.batteries.remove(
                building,
            )

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.enabled:

            return

        self.calculate_generation()

        self.calculate_consumption()

        self.distribute_power()

        self.update_storage()

    # ========================================================
    # Generation
    # ========================================================

    def calculate_generation(
        self,
    ) -> float:

        total = 0.0

        for producer in self.producers:

            if not producer.operational:

                continue

            output = getattr(producer, "effective_output", None)
            if output is None:
                output = getattr(producer, "power_output", 0.0)
            output = getattr(producer, "metadata", {}).get("last_power_generation", output)
            total += max(0.0, float(output))

        self.total_generation = total

        return total

    # ========================================================
    # Consumption
    # ========================================================

    def calculate_consumption(
        self,
    ) -> float:

        total = 0.0

        for consumer in self.consumers:

            if not consumer.operational:

                continue

            if hasattr(
                consumer,
                "power_required",
            ):

                total += consumer.power_required

        self.total_consumption = total

        return total

    # ========================================================
    # Distribution
    # ========================================================

    def distribute_power(
        self,
    ) -> None:

        available = (self.total_generation * self.transmission_efficiency
                     + self.stored_power_dispatch)

        demand = self.total_consumption

        self.power_losses = self.total_generation - available

        if available >= demand:

            self.unmet_demand = 0.0
            self.restore_power()

            return

        self.unmet_demand = demand - available

        if self.automatic_load_balancing:

            self.perform_load_balancing()

    # ========================================================
    # Load Balancing
    # ========================================================

    def perform_load_balancing(
        self,
    ) -> None:

        consumers = sorted(
            self.consumers,
            key=lambda building: getattr(
                building,
                "power_priority",
                100,
            ),
        )

        available = (self.total_generation * self.transmission_efficiency
                     + self.stored_power_dispatch)

        for consumer in consumers:

            if not consumer.operational:

                continue

            required = getattr(
                consumer,
                "power_required",
                0.0,
            )

            if available >= required:

                available -= required

                if hasattr(consumer, "set_power"):
                    consumer.set_power(True)
                else:
                    setattr(consumer, "is_powered", True)

            else:

                if hasattr(consumer, "set_power"):
                    consumer.set_power(False)
                else:
                    setattr(consumer, "is_powered", False)

        self.unmet_demand = max(
            0.0,
            self.total_consumption
            - self.total_generation * self.transmission_efficiency
            - self.stored_power_dispatch,
        )

    # ========================================================
    # Storage
    # ========================================================

    def update_storage(
        self,
    ) -> None:

        total = 0.0

        for battery in self.batteries:

            total += max(0.0, float(getattr(battery, "stored_energy", 0.0)))

        self.total_storage = total

    def hourly_update(self) -> None:
        """Balance available generation against demand and battery capacity."""
        super().hourly_update()
        if not self.enabled:
            return
        self.calculate_generation()
        self.calculate_consumption()
        deficit = max(0.0, self.total_consumption - self.total_generation * self.transmission_efficiency)
        inventory_power = min(deficit, self.power_resource.current_amount)
        if inventory_power:
            self.power_resource.consume(inventory_power)
        remaining = deficit - inventory_power
        battery_dispatch = 0.0
        for battery in self.batteries:
            if remaining <= 0:
                break
            delivered = battery.discharge(remaining)
            battery_dispatch += delivered
            remaining -= delivered
        self.stored_power_dispatch = inventory_power + battery_dispatch
        self.distribute_power()
        surplus = max(0.0, self.total_generation * self.transmission_efficiency - self.total_consumption)
        if surplus > 0:
            for battery in self.batteries:
                if surplus <= 0:
                    break
                transfer = min(surplus, battery.charge_rate, battery.available_capacity)
                if transfer <= 0:
                    continue
                removed = self.power_resource.consume(transfer)
                if removed:
                    accepted = battery.charge(float(removed))
                    surplus -= accepted
        else:
            self.unmet_demand = max(0.0, remaining)
        self.update_storage()

    # ========================================================
    # Grid Status
    # ========================================================

    @property
    def power_balance(
        self,
    ) -> float:

        return self.total_generation + self.stored_power_dispatch - self.total_consumption

    @property
    def grid_efficiency(
        self,
    ) -> float:

        if self.total_generation <= 0:

            return 0.0

        return (
            (self.total_generation - self.power_losses) / self.total_generation
        ) * 100.0

    @property
    def brownout(
        self,
    ) -> bool:

        return (self.total_generation * self.transmission_efficiency + self.stored_power_dispatch
                < self.total_consumption * self.brownout_threshold)

    @property
    def blackout(
        self,
    ) -> bool:

        return (self.total_generation * self.transmission_efficiency + self.stored_power_dispatch
                < self.total_consumption * self.blackout_threshold)

    @property
    def operating_normally(
        self,
    ) -> bool:

        return not self.brownout and not self.blackout

    # ========================================================
    # Priority Management
    # ========================================================

    def set_priority(
        self,
        building: BaseBuilding,
        priority: int,
    ) -> None:

        setattr(
            building,
            "power_priority",
            max(
                1,
                priority,
            ),
        )

    def power_priority(
        self,
        building: BaseBuilding,
    ) -> int:

        return getattr(
            building,
            "power_priority",
            100,
        )

    def minimum_power(
        self,
        building: BaseBuilding,
    ) -> float:

        return getattr(
            building,
            "minimum_power",
            0.0,
        )

    def is_powered(
        self,
        building: BaseBuilding,
    ) -> bool:

        return getattr(
            building,
            "is_powered",
            True,
        )

    def powered_buildings(
        self,
    ) -> list[BaseBuilding]:

        return [
            building
            for building in self.consumers
            if self.is_powered(
                building,
            )
        ]

    def unpowered_buildings(
        self,
    ) -> list[BaseBuilding]:

        return [
            building
            for building in self.consumers
            if not self.is_powered(
                building,
            )
        ]

    # ========================================================
    # Emergency Power
    # ========================================================

    def restore_power(
        self,
    ) -> None:

        for building in self.consumers:

            if hasattr(building, "set_power"):
                building.set_power(True)
            else:
                setattr(building, "is_powered", True)

    def shutdown_noncritical(
        self,
        priority_limit: int = 50,
    ) -> None:

        for building in self.consumers:

            if (
                self.power_priority(
                    building,
                )
                > priority_limit
            ):

                if hasattr(building, "set_power"):
                    building.set_power(False)
                else:
                    setattr(building, "is_powered", False)

    def emergency_mode(
        self,
    ) -> None:

        self.shutdown_noncritical(
            priority_limit=25,
        )

    def normal_mode(
        self,
    ) -> None:

        self.restore_power()

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, float | bool | int]:

        stats = super().statistics()

        stats.update(
            {
                "generation": round(
                    self.total_generation,
                    2,
                ),
                "consumption": round(
                    self.total_consumption,
                    2,
                ),
                "storage": round(
                    self.total_storage,
                    2,
                ),
                "power_balance": round(
                    self.power_balance,
                    2,
                ),
                "unmet_demand": round(
                    self.unmet_demand,
                    2,
                ),
                "power_losses": round(
                    self.power_losses,
                    2,
                ),
                "grid_efficiency": round(
                    self.grid_efficiency,
                    2,
                ),
                "brownout": self.brownout,
                "blackout": self.blackout,
                "operating_normally": self.operating_normally,
                "producer_count": len(
                    self.producers,
                ),
                "consumer_count": len(
                    self.consumers,
                ),
                "battery_count": len(
                    self.batteries,
                ),
                "powered_buildings": len(
                    self.powered_buildings(),
                ),
                "unpowered_buildings": len(
                    self.unpowered_buildings(),
                ),
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
            "PowerGrid("
            f"generation={self.total_generation:.2f}, "
            f"consumption={self.total_consumption:.2f}, "
            f"balance={self.power_balance:.2f}, "
            f"efficiency={self.grid_efficiency:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ElectricalGrid = PowerGrid

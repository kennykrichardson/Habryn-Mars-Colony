"""
power.py

Part 1/4

Canonical Power resource.

Represents electrical energy stored and distributed
throughout the colony.

Used by

- Solar Arrays
- Batteries
- Nuclear Reactors
- Every powered building
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Power
# ============================================================


@dataclass
class Power(BaseResource):

    name: str = "Power"

    unit: str = "kWh"

    storage_capacity: float = 500000.0

    current_amount: float = 300000.0

    voltage: float = 480.0

    frequency: float = 60.0

    transmission_loss: float = 0.0

    emergency_reserve: float = 50000.0

    generation_rate: float = 0.0

    consumption_rate: float = 0.0

    battery_charge_rate: float = 0.0

    battery_discharge_rate: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.generate(
            self.generation_rate,
        )

        self.discharge(
            self.battery_discharge_rate,
        )

        self.consume(
            self.consumption_rate,
        )

        self.lose(
            self.transmission_loss,
        )

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

    # ========================================================
    # Power Operations
    # ========================================================

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def charge(
        self,
        amount: float,
    ) -> float:

        self.battery_charge_rate += amount

        return self.add(
            amount,
        )

    def discharge(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def consume(
        self,
        amount: float,
    ) -> float:

        return super().consume(
            amount,
        )

    def lose(
        self,
        amount: float,
    ) -> float:

        return super().lose(
            amount,
        )

    def refill(
        self,
    ) -> None:

        self.current_amount = self.storage_capacity

    # ========================================================
    # Queries
    # ========================================================

    @property
    def is_low(
        self,
    ) -> bool:

        return self.current_amount <= self.emergency_reserve

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def available_power(
        self,
    ) -> float:

        return max(
            0.0,
            self.current_amount - self.emergency_reserve,
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
                "voltage": round(
                    self.voltage,
                    2,
                ),
                "frequency": round(
                    self.frequency,
                    2,
                ),
                "generation_rate": round(
                    self.generation_rate,
                    2,
                ),
                "consumption_rate": round(
                    self.consumption_rate,
                    2,
                ),
                "battery_charge_rate": round(
                    self.battery_charge_rate,
                    2,
                ),
                "battery_discharge_rate": round(
                    self.battery_discharge_rate,
                    2,
                ),
                "transmission_loss": round(
                    self.transmission_loss,
                    2,
                ),
                "emergency_reserve": round(
                    self.emergency_reserve,
                    2,
                ),
                "available_power": round(
                    self.available_power,
                    2,
                ),
                "low": self.is_low,
            }
        )

        return stats

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "voltage": self.voltage,
                "frequency": self.frequency,
                "transmission_loss": self.transmission_loss,
                "emergency_reserve": self.emergency_reserve,
                "generation_rate": self.generation_rate,
                "consumption_rate": self.consumption_rate,
                "battery_charge_rate": self.battery_charge_rate,
                "battery_discharge_rate": self.battery_discharge_rate,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Power":

        power = cls()

        power.current_amount = data.get(
            "current_amount",
            power.current_amount,
        )

        power.storage_capacity = data.get(
            "storage_capacity",
            power.storage_capacity,
        )

        power.voltage = data.get(
            "voltage",
            power.voltage,
        )

        power.frequency = data.get(
            "frequency",
            power.frequency,
        )

        power.transmission_loss = data.get(
            "transmission_loss",
            power.transmission_loss,
        )

        power.emergency_reserve = data.get(
            "emergency_reserve",
            power.emergency_reserve,
        )

        power.generation_rate = data.get(
            "generation_rate",
            power.generation_rate,
        )

        power.consumption_rate = data.get(
            "consumption_rate",
            power.consumption_rate,
        )

        power.battery_charge_rate = data.get(
            "battery_charge_rate",
            power.battery_charge_rate,
        )

        power.battery_discharge_rate = data.get(
            "battery_discharge_rate",
            power.battery_discharge_rate,
        )

        return power

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Power("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} kWh, "
            f"{self.storage_percentage:.1f}%, "
            f"{self.voltage:.0f}V"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Electricity = Power

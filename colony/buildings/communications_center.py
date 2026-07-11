"""
communications_center.py

Part 1/6

Canonical Communications Center.

Handles colony communications, networking,
satellite links and remote operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.science_points import SciencePoints

# ============================================================
# Communications Center
# ============================================================


@dataclass
class CommunicationsCenter(BaseBuilding):

    building_id: int = 0

    name: str = "Communications Center"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Provides communication, networking and satellite coordination."

    bandwidth: float = 100.0

    signal_strength: float = 100.0

    network_efficiency: float = 1.0

    power_required: float = 14.0

    satellite_bonus: float = 1.0

    research_bonus: float = 0.10

    power: Power = field(
        default_factory=Power,
    )

    science: SciencePoints = field(
        default_factory=SciencePoints,
    )

    total_messages_processed: float = 0.0

    total_research_bonus: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.process_network()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.signal_strength = min(
            100.0,
            self.signal_strength,
        )

    # ========================================================
    # Communications
    # ========================================================

    def process_network(
        self,
    ) -> float:

        if not self.operational or self.power.current_amount < self.power_required:

            return 0.0

        self.power.consume(
            self.power_required,
        )

        throughput = (
            self.bandwidth
            * self.network_efficiency
            * self.satellite_bonus
            * self.efficiency
            * (self.signal_strength / 100.0)
        )

        research = throughput * self.research_bonus

        self.science.generate(
            research,
        )

        self.total_messages_processed += throughput

        self.total_research_bonus += research

        return throughput

    # ========================================================
    # Network Management
    # ========================================================

    def repair_antenna(
        self,
        amount: float = 5.0,
    ) -> None:

        self.signal_strength = min(
            100.0,
            self.signal_strength + amount,
        )

    def signal_interference(
        self,
        amount: float = 5.0,
    ) -> None:

        self.signal_strength = max(
            0.0,
            self.signal_strength - amount,
        )

    def improve_network(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.network_efficiency = min(
            2.0,
            self.network_efficiency + bonus,
        )

    def expand_bandwidth(
        self,
        amount: float = 10.0,
    ) -> None:

        self.bandwidth += amount

    def deploy_satellite(
        self,
        bonus: float = 0.10,
    ) -> None:

        self.satellite_bonus = min(
            2.0,
            self.satellite_bonus + bonus,
        )

    def increase_research_bonus(
        self,
        amount: float = 0.02,
    ) -> None:

        self.research_bonus = min(
            0.50,
            self.research_bonus + amount,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_bandwidth(
        self,
    ) -> float:

        return (
            self.bandwidth
            * self.network_efficiency
            * self.satellite_bonus
            * self.efficiency
            * (self.signal_strength / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_bandwidth / self.power_required

    @property
    def network_quality(
        self,
    ) -> float:

        return self.signal_strength * self.network_efficiency

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.signal_strength < 65.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.operational and self.signal_strength >= 95.0

    @property
    def satellite_online(
        self,
    ) -> bool:

        return self.satellite_bonus > 1.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "bandwidth": round(
                    self.bandwidth,
                    2,
                ),
                "effective_bandwidth": round(
                    self.effective_bandwidth,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "signal_strength": round(
                    self.signal_strength,
                    2,
                ),
                "network_efficiency": round(
                    self.network_efficiency,
                    2,
                ),
                "satellite_bonus": round(
                    self.satellite_bonus,
                    2,
                ),
                "research_bonus": round(
                    self.research_bonus,
                    2,
                ),
                "network_quality": round(
                    self.network_quality,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "satellite_online": self.satellite_online,
                "total_messages_processed": round(
                    self.total_messages_processed,
                    2,
                ),
                "total_research_bonus": round(
                    self.total_research_bonus,
                    2,
                ),
                "power": self.power.statistics(),
                "science": self.science.statistics(),
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
            "CommunicationsCenter("
            f"health={self.health_percentage:.1f}%, "
            f"signal={self.signal_strength:.1f}%, "
            f"bandwidth={self.effective_bandwidth:.2f} Mbps, "
            f"network={self.network_efficiency:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

MissionControl = CommunicationsCenter

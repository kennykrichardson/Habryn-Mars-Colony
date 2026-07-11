"""
economy_manager.py

Canonical Economy Manager.

Responsible for the colony economy.

Owns

- credits
- income
- expenses
- budgets
- trade
- financial statistics

Does NOT produce resources.

Other managers report economic activity.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.systems.base_manager import BaseManager
from colony.systems.resource_manager import ResourceManager


# ============================================================
# Economy Manager
# ============================================================


@dataclass
class EconomyManager(BaseManager):

    name: str = "Economy Manager"

    resource_manager: ResourceManager | None = None

    colony_credits: float = 0.0

    total_income: float = 0.0

    total_expenses: float = 0.0

    trade_income: float = 0.0

    trade_expenses: float = 0.0

    maintenance_cost: float = 0.0

    construction_cost: float = 0.0

    research_budget: float = 0.0

    emergency_budget: float = 0.0

    reserve_funds: float = 0.0

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_resource_manager(
        self,
        manager: ResourceManager,
    ) -> None:

        self.resource_manager = manager

    @property
    def connected(
        self,
    ) -> bool:

        return self.resource_manager is not None

    # ========================================================
    # Credits
    # ========================================================

    def deposit(
        self,
        amount: float,
    ) -> None:

        amount = max(
            0.0,
            amount,
        )

        self.colony_credits += amount

        self.total_income += amount

    def withdraw(
        self,
        amount: float,
    ) -> bool:

        amount = max(
            0.0,
            amount,
        )

        if amount > self.colony_credits:

            return False

        self.colony_credits -= amount

        self.total_expenses += amount

        return True
    
    # ========================================================
    # Income
    # ========================================================

    def record_income(
        self,
        amount: float,
    ) -> None:

        self.deposit(
            amount,
        )

    def record_trade_income(
        self,
        amount: float,
    ) -> None:

        amount = max(
            0.0,
            amount,
        )

        self.trade_income += amount

        self.deposit(
            amount,
        )

    # ========================================================
    # Expenses
    # ========================================================

    def record_expense(
        self,
        amount: float,
    ) -> bool:

        return self.withdraw(
            amount,
        )

    def record_trade_expense(
        self,
        amount: float,
    ) -> bool:

        amount = max(
            0.0,
            amount,
        )

        if not self.withdraw(
            amount,
        ):

            return False

        self.trade_expenses += amount

        return True
    
    # ========================================================
    # Budgets
    # ========================================================

    def allocate_research_budget(
        self,
        amount: float,
    ) -> bool:

        if not self.withdraw(
            amount,
        ):

            return False

        self.research_budget += amount

        return True

    def allocate_emergency_budget(
        self,
        amount: float,
    ) -> bool:

        if not self.withdraw(
            amount,
        ):

            return False

        self.emergency_budget += amount

        return True

    def allocate_reserve_funds(
        self,
        amount: float,
    ) -> bool:

        if not self.withdraw(
            amount,
        ):

            return False

        self.reserve_funds += amount

        return True
    
    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.process_daily_finances()

    # ========================================================
    # Daily Economy
    # ========================================================

    def process_daily_finances(
        self,
    ) -> None:

        self.total_expenses += (

            self.maintenance_cost

        )

        if self.colony_credits >= self.maintenance_cost:

            self.colony_credits -= (

                self.maintenance_cost

            )

        else:

            self.colony_credits = 0.0

    # ========================================================
    # Queries
    # ========================================================

    @property
    def balance(
        self,
    ) -> float:

        return self.colony_credits

    @property
    def net_income(
        self,
    ) -> float:

        return (

            self.total_income

            - self.total_expenses

        )

    @property
    def profitable(
        self,
    ) -> bool:

        return self.net_income >= 0.0

    @property
    def bankrupt(
        self,
    ) -> bool:

        return self.colony_credits <= 0.0

    @property
    def financial_health(
        self,
    ) -> str:

        if self.bankrupt:

            return "Bankrupt"

        if self.colony_credits < 1_000:

            return "Critical"

        if self.colony_credits < 10_000:

            return "Stable"

        return "Prosperous"
    
    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(

            {

                "credits":
                round(
                    self.colony_credits,
                    2,
                ),

                "income":
                round(
                    self.total_income,
                    2,
                ),

                "expenses":
                round(
                    self.total_expenses,
                    2,
                ),

                "net_income":
                round(
                    self.net_income,
                    2,
                ),

                "trade_income":
                round(
                    self.trade_income,
                    2,
                ),

                "trade_expenses":
                round(
                    self.trade_expenses,
                    2,
                ),

                "maintenance_cost":
                round(
                    self.maintenance_cost,
                    2,
                ),

                "construction_cost":
                round(
                    self.construction_cost,
                    2,
                ),

                "research_budget":
                round(
                    self.research_budget,
                    2,
                ),

                "emergency_budget":
                round(
                    self.emergency_budget,
                    2,
                ),

                "reserve_funds":
                round(
                    self.reserve_funds,
                    2,
                ),

                "financial_health":
                self.financial_health,

                "profitable":
                self.profitable,

            }

        )

        return stats
    
    # ========================================================
    # Utility
    # ========================================================

    def reset_finances(
        self,
    ) -> None:

        self.colony_credits = 0.0

        self.total_income = 0.0

        self.total_expenses = 0.0

        self.trade_income = 0.0

        self.trade_expenses = 0.0

        self.maintenance_cost = 0.0

        self.construction_cost = 0.0

        self.research_budget = 0.0

        self.emergency_budget = 0.0

        self.reserve_funds = 0.0

    def clear(
        self,
    ) -> None:

        self.reset_finances()

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(

            {

                "colony_credits":
                self.colony_credits,

                "total_income":
                self.total_income,

                "total_expenses":
                self.total_expenses,

                "trade_income":
                self.trade_income,

                "trade_expenses":
                self.trade_expenses,

                "maintenance_cost":
                self.maintenance_cost,

                "construction_cost":
                self.construction_cost,

                "research_budget":
                self.research_budget,

                "emergency_budget":
                self.emergency_budget,

                "reserve_funds":
                self.reserve_funds,

            }

        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "EconomyManager":

        manager = cls()

        manager.enabled = data.get(
            "enabled",
            True,
        )

        manager.initialized = data.get(
            "initialized",
            False,
        )

        manager.tick_count = data.get(
            "tick_count",
            0,
        )

        manager.hour_count = data.get(
            "hour_count",
            0,
        )

        manager.day_count = data.get(
            "day_count",
            0,
        )

        manager.update_count = data.get(
            "update_count",
            0,
        )

        manager.error_count = data.get(
            "error_count",
            0,
        )

        manager.colony_credits = data.get(
            "colony_credits",
            0.0,
        )

        manager.total_income = data.get(
            "total_income",
            0.0,
        )

        manager.total_expenses = data.get(
            "total_expenses",
            0.0,
        )

        manager.trade_income = data.get(
            "trade_income",
            0.0,
        )

        manager.trade_expenses = data.get(
            "trade_expenses",
            0.0,
        )

        manager.maintenance_cost = data.get(
            "maintenance_cost",
            0.0,
        )

        manager.construction_cost = data.get(
            "construction_cost",
            0.0,
        )

        manager.research_budget = data.get(
            "research_budget",
            0.0,
        )

        manager.emergency_budget = data.get(
            "emergency_budget",
            0.0,
        )

        manager.reserve_funds = data.get(
            "reserve_funds",
            0.0,
        )

        return manager
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "EconomyManager("

            f"credits={self.colony_credits:.2f}, "

            f"net={self.net_income:.2f}, "

            f"health='{self.financial_health}'"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

Economy = EconomyManager
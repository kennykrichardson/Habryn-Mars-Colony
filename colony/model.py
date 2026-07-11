"""
model.py

Canonical Habryn colony model.

Acts as the central orchestrator for the simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.scheduler import Scheduler

from colony.events.event_manager import EventManager
from colony.events.accidents import AccidentManager
from colony.events.failures import FailureManager
from colony.events.random_events import RandomEventManager
from colony.systems.ai_manager import AIManager
from colony.systems.construction_manager import ConstructionManager
from colony.systems.economy_manager import EconomyManager
from colony.systems.emergency_manager import EmergencyManager
from colony.systems.logistics_manager import LogisticsManager
from colony.systems.maintenance_manager import MaintenanceManager
from colony.systems.population_manager import PopulationManager
from colony.systems.power_grid import PowerGrid
from colony.systems.resource_manager import ResourceManager
from colony.systems.research_manager import ResearchManager
from colony.systems.task_manager import TaskManager

# ============================================================
# Colony Model
# ============================================================


@dataclass
class ColonyModel:

    scheduler: Scheduler

    event_manager: EventManager = field(
        default_factory=EventManager,
    )

    accident_manager: AccidentManager = field(
        default_factory=AccidentManager,
    )

    failure_manager: FailureManager = field(
        default_factory=FailureManager,
    )

    random_event_manager: RandomEventManager = field(
        default_factory=RandomEventManager,
    )

    power_grid: PowerGrid = field(
        default_factory=PowerGrid,
    )

    resource_manager: ResourceManager = field(
        default_factory=ResourceManager,
    )

    population_manager: PopulationManager = field(
        default_factory=PopulationManager,
    )

    construction_manager: ConstructionManager = field(
        default_factory=ConstructionManager,
    )

    logistics_manager: LogisticsManager = field(
        default_factory=LogisticsManager,
    )

    research_manager: ResearchManager = field(
        default_factory=ResearchManager,
    )

    economy_manager: EconomyManager = field(
        default_factory=EconomyManager,
    )

    emergency_manager: EmergencyManager = field(
        default_factory=EmergencyManager,
    )

    maintenance_manager: MaintenanceManager = field(
        default_factory=MaintenanceManager,
    )

    ai_manager: AIManager = field(
        default_factory=AIManager,
    )

    task_manager: TaskManager = field(
        default_factory=TaskManager,
    )

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        if self.scheduler is None:

            raise ValueError(

                "ColonyModel requires a Scheduler.",

            )

        self.connect_managers()

        self.initialize_managers()

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_managers(
        self,
    ) -> None:

        # Construction

        self.construction_manager.connect_resource_manager(

            self.resource_manager,

        )

        self.construction_manager.connect_power_grid(

            self.power_grid,

        )

        self.construction_manager.connect_population_manager(

            self.population_manager,

        )

        # ========================================================
        # Scheduler
        # ========================================================

        for manager in self.managers:

            manager.scheduler = self.scheduler

    # ========================================================
    # Event System
    # ========================================================

        self.accident_manager.connect_event_manager(

            self.event_manager,

        )

        self.accident_manager.connect_emergency_manager(

            self.emergency_manager,

        )

        self.failure_manager.connect_event_manager(

            self.event_manager,

        )

        self.failure_manager.connect_emergency_manager(

            self.emergency_manager,

        )

        self.random_event_manager.connect_event_manager(

            self.event_manager,

        )        

    # ========================================================
    # Manager Initialization
    # ========================================================

    def initialize_managers(
        self,
    ) -> None:

        managers = (

            self.event_manager,

            self.accident_manager,

            self.failure_manager,

            self.random_event_manager,

            self.power_grid,

            self.resource_manager,

            self.population_manager,

            self.construction_manager,

            self.logistics_manager,

            self.research_manager,

            self.economy_manager,

            self.emergency_manager,

            self.maintenance_manager,

            self.ai_manager,

            self.task_manager,

        )

        for manager in managers:

            manager.initialize()

    # ========================================================
    # Manager Collection
    # ========================================================

    @property
    def managers(
        self,
    ) -> tuple:

        return (

            self.event_manager,

            self.accident_manager,

            self.failure_manager,

            self.random_event_manager,

            self.power_grid,

            self.resource_manager,

            self.population_manager,

            self.construction_manager,

            self.logistics_manager,

            self.research_manager,

            self.economy_manager,

            self.emergency_manager,

            self.maintenance_manager,

            self.ai_manager,

            self.task_manager,

        )
    
    # ========================================================
    # Simulation
    # ========================================================

    def step(
        self,
    ) -> None:

        for manager in self.managers:

            manager.step()

        self.process_scheduler_events()

    # ========================================================
    # Scheduler Events
    # ========================================================

    def process_scheduler_events(
        self,
    ) -> None:

        scheduler = self.scheduler

        if scheduler.new_hour:

            self.hourly_update()

        if scheduler.new_day:

            self.daily_update()

    def hourly_update(
        self,
    ) -> None:

        for manager in self.managers:

            manager.hourly_update()

    def daily_update(
        self,
    ) -> None:

        for manager in self.managers:

            manager.daily_update()

    # ========================================================
    # Colony Status
    # ========================================================

    @property
    def initialized(
        self,
    ) -> bool:

        return all(

            manager.initialized

            for manager in self.managers

        )

    @property
    def running(
        self,
    ) -> bool:

        return self.initialized
    
    @property
    def current_tick(
        self,
    ) -> int:

        return self.scheduler.tick

    @property
    def current_hour(
        self,
    ) -> int:

        return self.scheduler.hour

    @property
    def current_day(
        self,
    ) -> int:

        return self.scheduler.day

    @property
    def current_month(
        self,
    ) -> int:

        return self.scheduler.month

    @property
    def current_year(
        self,
    ) -> int:

        return self.scheduler.year

    @property
    def manager_count(
        self,
    ) -> int:

        return len(

            self.managers,

        )
    
    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {

            "scheduler": self.scheduler.statistics(),

            "events":
                self.event_manager.statistics(),

            "accidents":
                self.accident_manager.statistics(),

            "failures":
                self.failure_manager.statistics(),

            "random_events":
                self.random_event_manager.statistics(),

            "manager_count": self.manager_count,

            "initialized": self.initialized,

            "power_grid":
                self.power_grid.statistics(),

            "resources":
                self.resource_manager.statistics(),

            "population":
                self.population_manager.statistics(),

            "construction":
                self.construction_manager.statistics(),

            "logistics":
                self.logistics_manager.statistics(),

            "research":
                self.research_manager.statistics(),

            "economy":
                self.economy_manager.statistics(),

            "emergency":
                self.emergency_manager.statistics(),

            "maintenance":
                self.maintenance_manager.statistics(),

            "ai":
                self.ai_manager.statistics(),

            "tasks":
                self.task_manager.statistics(),

        }
    
    # ========================================================
    # Utility
    # ========================================================

    def reset(
        self,
    ) -> None:

        for manager in self.managers:

            manager.reset()

    def serialize(
        self,
    ) -> dict:

        return {

            "scheduler":
                self.scheduler.serialize(),

            "event_manager":
                self.event_manager.serialize(),

            "accident_manager":
                self.accident_manager.serialize(),

            "failure_manager":
                self.failure_manager.serialize(),

            "random_event_manager":
                self.random_event_manager.serialize(),

            "power_grid":
                self.power_grid.serialize(),

            "resource_manager":
                self.resource_manager.serialize(),

            "population_manager":
                self.population_manager.serialize(),

            "construction_manager":
                self.construction_manager.serialize(),

            "logistics_manager":
                self.logistics_manager.serialize(),

            "research_manager":
                self.research_manager.serialize(),

            "economy_manager":
                self.economy_manager.serialize(),

            "emergency_manager":
                self.emergency_manager.serialize(),

            "maintenance_manager":
                self.maintenance_manager.serialize(),

            "ai_manager":
                self.ai_manager.serialize(),

            "task_manager":
                self.task_manager.serialize(),

        }
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "ColonyModel("

            f"managers={self.manager_count}, "

            f"initialized={self.initialized}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

HabrynModel = ColonyModel
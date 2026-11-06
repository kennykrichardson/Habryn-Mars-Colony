"""
Habryn

Application entry point.

Mission Control for the Habryn simulation.
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.rule import Rule

from colony.simulation import Simulation

console = Console()


# ============================================================
# Dashboard
# ============================================================


def build_dashboard(
    simulation: Simulation,
) -> Table:

    stats = simulation.statistics()

    scheduler = stats["scheduler"]
    model = stats["model"]

    table = Table(
        title="Habryn Mission Control",
        show_header=False,
        expand=True,
        pad_edge=False,
    )

    table.add_column(style="bold cyan", width=22)
    table.add_column(style="white")

    # =====================================================
    # TIME
    # =====================================================

    table.add_row(
        "[bold yellow]TIME[/bold yellow]",
        "",
    )

    table.add_row(
        "Tick",
        str(scheduler["tick"]),
    )

    table.add_row(
        "Sol",
        str(scheduler["sol"]),
    )

    table.add_row(
        "Day",
        str(scheduler["day"]),
    )

    table.add_row(
        "Time",
        f'{scheduler["hour"]:02d}:00',
    )

    table.add_row(
        "Month",
        str(scheduler["month"]),
    )

    table.add_row(
        "Year",
        str(scheduler["year"]),
    )

    table.add_section()

    # =====================================================
    # COLONY
    # =====================================================

    table.add_row(
        "[bold yellow]COLONY[/bold yellow]",
        "",
    )

    table.add_row(
        "Managers",
        str(model["manager_count"]),
    )

    table.add_row(
        "Initialized",
        "[green]YES[/green]" if model["initialized"] else "[red]NO[/red]",
    )

    table.add_section()

    # =====================================================
    # POWER
    # =====================================================

    power = model["power_grid"]

    table.add_row(
        "[bold yellow]POWER[/bold yellow]",
        "",
    )

    table.add_row(
        "Generated",
        str(
            power.get(
                "generation",
                "N/A",
            )
        ),
    )

    table.add_row(
        "Consumed",
        str(
            power.get(
                "consumption",
                "N/A",
            )
        ),
    )

    table.add_row(
        "Stored",
        str(
            power.get(
                "storage",
                "N/A",
            )
        ),
    )

    table.add_section()

    # =====================================================
    # RESOURCES
    # =====================================================

    resources = model["resources"]

    table.add_row(
        "[bold yellow]RESOURCES[/bold yellow]",
        "",
    )

    for key, value in resources.items():

        table.add_row(
            key.replace(
                "_",
                " ",
            ).title(),
            str(value),
        )

    table.add_row("[bold]Inventory (amount / capacity)[/bold]", "")
    for name, resource in simulation.model.world_snapshot().telemetry["resource_inventory"].items():
        table.add_row(name, f"{resource['current_amount']:,.1f} / {resource['storage_capacity']:,.1f} {resource['unit']}")
    warnings = simulation.model.world_snapshot().telemetry["warnings"]
    if warnings:
        table.add_row("[bold red]Shortages[/bold red]", ", ".join(warnings))

    table.add_section()

    # =====================================================
    # POPULATION
    # =====================================================

    population = model["population"]

    table.add_row(
        "[bold yellow]POPULATION[/bold yellow]",
        "",
    )

    table.add_row("Robots", str(sum("robot" in type(agent).__name__.lower()
                                     for agent in simulation.model.agents_by_id.values())))
    table.add_row("Buildings", str(len(simulation.model.buildings_by_id)))

    for key, value in population.items():

        table.add_row(
            key.replace(
                "_",
                " ",
            ).title(),
            str(value),
        )

    table.add_section()

    # =====================================================
    # RESEARCH
    # =====================================================

    research = model["research"]

    table.add_row(
        "[bold yellow]RESEARCH[/bold yellow]",
        "",
    )

    for key, value in research.items():

        table.add_row(
            key.replace(
                "_",
                " ",
            ).title(),
            str(value),
        )

    table.add_section()

    # =====================================================
    # EVENTS
    # =====================================================

    events = model["events"]

    table.add_row(
        "[bold yellow]EVENTS[/bold yellow]",
        "",
    )

    for key, value in events.items():

        table.add_row(
            key.replace(
                "_",
                " ",
            ).title(),
            str(value),
        )

    return table


# ============================================================
# Runtime
# ============================================================


def display_dashboard(
    simulation: Simulation,
) -> None:

    console.clear()

    console.print(
        Rule("[bold red]HABRYN"),
    )

    console.print(
        build_dashboard(
            simulation,
        )
    )


def main() -> None:

    simulation = Simulation()

    simulation.start()

    display_dashboard(
        simulation,
    )

    while True:

        command = input("[ENTER]=Tick | q=Quit > ").strip().lower()

        if command == "q":

            break

        simulation.step()

        display_dashboard(
            simulation,
        )

    simulation.stop()


if __name__ == "__main__":

    main()

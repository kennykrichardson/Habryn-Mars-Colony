"""
Habryn

Application entry point.
"""

from rich.console import Console

from colony.simulation import Simulation

console = Console()


def main() -> None:

    console.rule("[bold red]HABRYN")

    console.print(
        "[cyan]Initializing simulation...[/cyan]"
    )

    simulation = Simulation()

    console.print(
        "[green]Simulation initialized successfully.[/green]"
    )

    console.print()

    console.print(
        f"Tick : {simulation.current_tick}"
    )

    console.print(
        f"Hour : {simulation.current_hour}"
    )

    console.print(
        f"Day  : {simulation.current_day}"
    )

    console.print(
        f"Month: {simulation.current_month}"
    )

    console.print(
        f"Year : {simulation.current_year}"
    )

    console.print()

    simulation.start()

    while True:

        command = input(
            "[ENTER]=Tick | q=Quit > "
        )

        if command.lower() == "q":

            break

        simulation.step()

        console.print(

            f"Tick {simulation.current_tick} | "

            f"Day {simulation.current_day} | "

            f"{simulation.current_hour:02d}:00"

        )

    simulation.stop()


if __name__ == "__main__":

    main()
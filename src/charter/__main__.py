"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Charter."""


if __name__ == "__main__":
    main(prog_name="charter")  # pragma: no cover

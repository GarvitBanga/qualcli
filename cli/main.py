import click
from .commands.submit import submit
from .commands.status import status
from .commands.devices import devices
from .commands.queue import queue
from .commands.jobs import jobs

@click.group()
def cli():
    """QualGent CLI tool for managing AppWright test jobs."""
    pass

cli.add_command(submit)
cli.add_command(status)
cli.add_command(devices)
cli.add_command(queue)
cli.add_command(jobs)

if __name__ == '__main__':
    cli() 
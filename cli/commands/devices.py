import click
from ..client import APIClient, APIError
from ..utils.formatting import print_error
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys

console = Console()

@click.group()
def devices():
    """Device management commands."""
    pass

@devices.command()
def list():
    """List all devices and their current status."""
    try:
        client = APIClient()
        response = client.get_devices()
        
        if not response.get('devices'):
            console.print("[yellow]No devices found in the pool[/yellow]")
            return
        
        # Create table
        table = Table(title="Device Pool Status")
        table.add_column("Device ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Usage", style="blue")
        table.add_column("Capacity", style="magenta")
        table.add_column("Utilization", style="red")
        table.add_column("Location", style="white")
        
        for device in response['devices']:
            status_color = {
                "available": "[green]available[/green]",
                "busy": "[yellow]busy[/yellow]",
                "offline": "[red]offline[/red]",
                "maintenance": "[orange]maintenance[/orange]"
            }.get(device['status'], device['status'])
            
            utilization = f"{device['utilization_percent']:.1f}%"
            usage = f"{device['current_jobs']}/{device['max_concurrent_jobs']}"
            
            table.add_row(
                device['device_id'],
                device['device_type'],
                status_color,
                usage,
                str(device['max_concurrent_jobs']),
                utilization,
                device.get('location', 'N/A')
            )
        
        console.print(table)
        
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error listing devices: {str(e)}")
        sys.exit(1)

@devices.command()
def status():
    """Show device pool status and utilization metrics."""
    try:
        client = APIClient()
        response = client.get_device_status()
        
        if 'error' in response:
            print_error(response['error'])
            return
        
        # Overall summary
        summary = response.get('summary', {})
        summary_panel = Panel.fit(
            f"[bold white]Total Devices:[/] {summary.get('total_devices', 0)}\n"
            f"[bold white]Total Capacity:[/] {summary.get('total_capacity', 0)} jobs\n"
            f"[bold white]Current Usage:[/] {summary.get('current_usage', 0)} jobs\n"
            f"[bold white]Available Devices:[/] {summary.get('available_devices', 0)}",
            title="[bold blue]Device Pool Summary",
            border_style="blue"
        )
        console.print(summary_panel)
        
        # Device pool details
        device_pools = response.get('device_pools', {})
        if device_pools:
            console.print("\n[bold]Device Pool Details:[/bold]")
            
            for device_type, stats in device_pools.items():
                table = Table(title=f"{device_type.capitalize()} Pool")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Total Devices", str(stats.get('total_devices', 0)))
                table.add_row("Available", str(stats.get('available', 0)))
                table.add_row("Busy", str(stats.get('busy', 0)))
                table.add_row("Offline", str(stats.get('offline', 0)))
                table.add_row("Total Capacity", str(stats.get('total_capacity', 0)))
                table.add_row("Current Usage", str(stats.get('current_usage', 0)))
                table.add_row("Utilization", f"{stats.get('utilization_percent', 0):.1f}%")
                
                console.print(table)
        
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting device status: {str(e)}")
        sys.exit(1)

@devices.command()
@click.argument('target_type', type=click.Choice(['emulator', 'device', 'browserstack']))
def recommend(target_type):
    """Get device allocation recommendations for a target type."""
    try:
        client = APIClient()
        response = client.get_device_recommendations(target_type)
        
        if 'error' in response:
            print_error(response['error'])
            return
        
        recommendation = response.get('recommendation')
        
        if recommendation == 'immediate_allocation':
            panel = Panel.fit(
                f"[bold green]✅ Device Available[/bold green]\n\n"
                f"[bold white]Device ID:[/] {response.get('device_id')}\n"
                f"[bold white]Current Utilization:[/] {response.get('current_utilization', 0):.1f}%\n"
                f"[bold white]Estimated Wait Time:[/] {response.get('estimated_wait_time', 0)} seconds",
                title=f"[bold green]{target_type.capitalize()} Recommendation",
                border_style="green"
            )
        elif recommendation == 'queue_and_wait':
            panel = Panel.fit(
                f"[bold yellow]⏳ Queue Required[/bold yellow]\n\n"
                f"[bold white]Message:[/] {response.get('message', 'All devices busy')}\n"
                f"[bold white]Estimated Wait Time:[/] {response.get('estimated_wait_time', 0)} seconds",
                title=f"[bold yellow]{target_type.capitalize()} Recommendation",
                border_style="yellow"
            )
        elif recommendation == 'devices_offline':
            panel = Panel.fit(
                f"[bold red]❌ No Devices Available[/bold red]\n\n"
                f"[bold white]Message:[/] {response.get('message', 'All devices offline')}",
                title=f"[bold red]{target_type.capitalize()} Recommendation",
                border_style="red"
            )
        else:
            panel = Panel.fit(
                f"[bold orange]⚠️  Unknown Status[/bold orange]\n\n"
                f"[bold white]Message:[/] {response.get('message', 'Unknown recommendation')}",
                title=f"[bold orange]{target_type.capitalize()} Recommendation",
                border_style="orange"
            )
        
        console.print(panel)
        
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting recommendations: {str(e)}")
        sys.exit(1)

@devices.command()
def health():
    """Perform health check on all devices."""
    try:
        client = APIClient()
        response = client.perform_health_check()
        
        if 'error' in response:
            print_error(response['error'])
            return
        
        total = response.get('total_checked', 0)
        healthy = response.get('healthy', 0)
        unhealthy = response.get('unhealthy', 0)
        
        # Summary panel
        summary_panel = Panel.fit(
            f"[bold white]Total Checked:[/] {total}\n"
            f"[bold green]Healthy:[/] {healthy}\n"
            f"[bold red]Unhealthy:[/] {unhealthy}",
            title="[bold blue]Health Check Results",
            border_style="blue"
        )
        console.print(summary_panel)
        
        # Details table
        details = response.get('details', [])
        if details:
            table = Table(title="Device Health Details")
            table.add_column("Device ID", style="cyan")
            table.add_column("Status", style="yellow")
            table.add_column("Health", style="green")
            
            for detail in details:
                health_status = "[green]✅ Healthy[/green]" if detail['healthy'] else "[red]❌ Unhealthy[/red]"
                table.add_row(
                    detail['device_id'],
                    detail['status'],
                    health_status
                )
            
            console.print(table)
        
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error performing health check: {str(e)}")
        sys.exit(1) 
import click
from ..client import APIClient, APIError
from ..utils.formatting import print_error
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import sys
import requests

console = Console()

@click.group()
def status():
    """Job status and monitoring commands."""
    pass

@status.command(name="job")
@click.option('--job-id', required=True, help='Job ID to check status')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information including priority and device allocation')
def job_status(job_id, verbose):
    """Check the status of a specific job."""
    try:
        client = APIClient()
        result = client.get_job_status(job_id)
        
        if verbose:
            # Enhanced status display with priority info
            priority = result.get('priority', 'Unknown')
            target = result.get('target', 'Unknown')
            device_id = result.get('assigned_device_name', 'Not assigned')
            
            # Priority visual indicator
            if isinstance(priority, int):
                if priority >= 4:
                    priority_display = f"🔥 {priority} (High Priority)"
                    priority_color = "red"
                elif priority >= 2:
                    priority_display = f"⚡ {priority} (Normal Priority)"
                    priority_color = "yellow"
                else:
                    priority_display = f"🐌 {priority} (Low Priority)"
                    priority_color = "blue"
            else:
                priority_display = str(priority)
                priority_color = "white"
            
            # Status color
            status_colors = {
                'queued': 'yellow',
                'running': 'blue', 
                'completed': 'green',
                'failed': 'red'
            }
            status_color = status_colors.get(result['status'].lower(), 'white')
            
            panel = Panel.fit(
                f"[bold white]Job ID:[/] {result['job_id']}\n"
                f"[bold white]Status:[/] [{status_color}]{result['status'].upper()}[/{status_color}]\n"
                f"[bold white]Priority:[/] [{priority_color}]{priority_display}[/{priority_color}]\n"
                f"[bold white]Target:[/] {target}\n"
                f"[bold white]Device:[/] {device_id}\n"
                f"[bold white]Created:[/] {result['created_at']}\n"
                f"[bold white]Updated:[/] {result.get('updated_at', 'N/A')}",
                title="[bold blue]Detailed Job Status",
                border_style="blue"
            )
        else:
            # Standard status display
            status_colors = {
                'queued': 'yellow',
                'running': 'blue',
                'completed': 'green', 
                'failed': 'red'
            }
            color = status_colors.get(result['status'].lower(), 'white')
            
            panel = Panel.fit(
                f"[bold white]Job ID:[/] {result['job_id']}\n"
                f"[bold white]Status:[/] [{color}]{result['status']}[/{color}]\n"
                f"[bold white]Created at:[/] {result['created_at']}",
                title="[bold blue]Job Status", 
                border_style="blue"
            )
        
        console.print(panel)

    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error checking job status: {str(e)}")
        sys.exit(1)

@status.command(name="list")
@click.option('--app-version-id', help='Filter by app version ID')
@click.option('--status-filter', type=click.Choice(['queued', 'running', 'completed', 'failed']), help='Filter by job status')
@click.option('--priority', type=click.IntRange(1, 5), help='Filter by priority level (1-5)')
@click.option('--target', type=click.Choice(['emulator', 'device', 'browserstack']), help='Filter by target environment')
@click.option('--limit', type=int, default=20, help='Maximum number of jobs to show (default: 20)')
def list_jobs(app_version_id, status_filter, priority, target, limit):
    """List jobs with optional filtering."""
    try:
        # Build query parameters
        params = {}
        if app_version_id:
            params['app_version_id'] = app_version_id
        if status_filter:
            params['status'] = status_filter
        if priority:
            params['priority'] = priority
        if target:
            params['target'] = target
        params['limit'] = limit
        
        # Make API request
        url = "http://localhost:8002/jobs"
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print_error(f"Failed to get jobs: {response.text}")
            return
        
        jobs = response.json()
        
        if not jobs:
            console.print("[yellow]No jobs found matching the criteria.[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Jobs List ({len(jobs)} found)")
        table.add_column("Job ID", style="cyan", justify="center")
        table.add_column("Priority", style="magenta", justify="center")
        table.add_column("Status", style="yellow", justify="center")
        table.add_column("Target", style="green", justify="center")
        table.add_column("App Version", style="blue")
        table.add_column("Test File", style="white")
        table.add_column("Created", style="dim")
        
        # Sort by priority (highest first) then by creation time
        jobs_sorted = sorted(jobs, key=lambda x: (-x.get('priority', 0), x.get('created_at', '')))
        
        for job in jobs_sorted:
            # Priority with visual indicator
            job_priority = job.get('priority', 0)
            if job_priority >= 4:
                priority_display = f"🔥 {job_priority}"
            elif job_priority >= 2:
                priority_display = f"⚡ {job_priority}"
            else:
                priority_display = f"🐌 {job_priority}"
            
            # Status with color
            job_status = job.get('status', 'unknown')
            status_colors = {
                'queued': '[yellow]QUEUED[/yellow]',
                'running': '[blue]RUNNING[/blue]',
                'completed': '[green]DONE[/green]',
                'failed': '[red]FAILED[/red]'
            }
            status_display = status_colors.get(job_status.lower(), job_status.upper())
            
            # Truncate long paths
            test_path = job.get('test_path', '')
            if len(test_path) > 30:
                test_path = '...' + test_path[-27:]
            
            # Format creation time
            created_at = job.get('created_at', '')
            if 'T' in created_at:
                created_at = created_at.split('T')[0] + ' ' + created_at.split('T')[1][:8]
            
            table.add_row(
                str(job.get('id', '')),
                priority_display,
                status_display,
                job.get('target', '').upper(),
                job.get('app_version_id', '')[:15] + ('...' if len(job.get('app_version_id', '')) > 15 else ''),
                test_path,
                created_at
            )
        
        console.print(table)
        
        # Summary
        status_counts = {}
        priority_counts = {}
        for job in jobs:
            status = job.get('status', 'unknown')
            priority = job.get('priority', 0)
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Status: {dict(status_counts)}")
        console.print(f"Priority: {dict(sorted(priority_counts.items(), reverse=True))}")
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error listing jobs: {str(e)}")
        sys.exit(1)

@status.command(name="summary")
def summary():
    """Show overall system status summary."""
    try:
        # Get queue status
        queue_response = requests.get("http://localhost:8002/queues/status")
        device_response = requests.get("http://localhost:8002/devices/status")
        
        console.print("[bold blue]📊 System Status Summary[/bold blue]\n")
        
        # Queue Status
        if queue_response.status_code == 200:
            queue_data = queue_response.json()
            queue_summary = queue_data.get('queue_summary', {})
            
            total_queued = sum(stats.get('queued_jobs', 0) for stats in queue_summary.values())
            total_running = sum(stats.get('running_jobs', 0) for stats in queue_summary.values())
            
            queue_panel = Panel.fit(
                f"[bold yellow]Queued Jobs:[/] {total_queued}\n"
                f"[bold blue]Running Jobs:[/] {total_running}\n"
                f"[bold white]Total Active:[/] {total_queued + total_running}",
                title="[bold green]Queue Status",
                border_style="green"
            )
            console.print(queue_panel)
        
        # Device Status  
        if device_response.status_code == 200:
            device_data = device_response.json()
            
            available = device_data.get('available_devices', 0)
            busy = device_data.get('busy_devices', 0)
            offline = device_data.get('offline_devices', 0)
            total = available + busy + offline
            
            device_panel = Panel.fit(
                f"[bold green]Available:[/] {available}\n"
                f"[bold yellow]Busy:[/] {busy}\n"
                f"[bold red]Offline:[/] {offline}\n"
                f"[bold white]Total:[/] {total}",
                title="[bold blue]Device Status",
                border_style="blue"
            )
            console.print(device_panel)
            
            # Device type breakdown
            by_type = device_data.get('by_type', {})
            if by_type:
                console.print("\n[bold]Device Types:[/bold]")
                for device_type, stats in by_type.items():
                    console.print(f"  {device_type.title()}: {stats.get('available', 0)} available, {stats.get('busy', 0)} busy")
        
        # Priority allocation
        if queue_response.status_code == 200:
            priority_breakdown = queue_data.get('priority_breakdown', {})
            active_priorities = {k: v for k, v in priority_breakdown.items() if v.get('total_active', 0) > 0}
            
            if active_priorities:
                console.print("\n[bold]Active Jobs by Priority:[/bold]")
                for priority_key in sorted(active_priorities.keys(), key=lambda x: int(x.split('_')[1]), reverse=True):
                    stats = active_priorities[priority_key]
                    priority_num = priority_key.split('_')[1]
                    if int(priority_num) >= 4:
                        icon = "🔥"
                    elif int(priority_num) >= 2:
                        icon = "⚡"
                    else:
                        icon = "🐌"
                    console.print(f"  {icon} Priority {priority_num}: {stats.get('total_active', 0)} jobs")
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting summary: {str(e)}")
        sys.exit(1)

# Legacy command for backward compatibility
@click.command(name="status-legacy")
@click.option('--job-id', required=True, help='Job ID to check status')
def status_legacy(job_id):
    """Check the status of a submitted job (legacy command)."""
    # Call the new job status command
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(job_status, ['--job-id', job_id])
    console.print(result.output) 
import click
from ..client import APIClient, APIError
from ..utils.formatting import print_error
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
import requests
import time
from datetime import datetime, timedelta

console = Console()

@click.group()
def jobs():
    """Job management and control commands."""
    pass

@jobs.command()
@click.option('--status-filter', type=click.Choice(['queued', 'running', 'completed', 'failed']), help='Filter by job status')
@click.option('--priority', type=click.IntRange(1, 5), help='Filter by priority level (1-5)')
@click.option('--target', type=click.Choice(['emulator', 'device', 'browserstack']), help='Filter by target environment')
@click.option('--app-version-id', help='Filter by app version ID')
@click.option('--org-id', help='Filter by organization ID')
@click.option('--limit', type=int, default=50, help='Maximum number of jobs to show (default: 50)')
@click.option('--sort', type=click.Choice(['created', 'priority', 'status']), default='created', help='Sort by field (default: created)')
@click.option('--order', type=click.Choice(['asc', 'desc']), default='desc', help='Sort order (default: desc)')
def list(status_filter, priority, target, app_version_id, org_id, limit, sort, order):
    """List and filter jobs with advanced options."""
    try:
        # Build query parameters
        params = {
            'limit': limit,
            'sort': sort,
            'order': order
        }
        if status_filter:
            params['status'] = status_filter
        if priority:
            params['priority'] = priority
        if target:
            params['target'] = target
        if app_version_id:
            params['app_version_id'] = app_version_id
        if org_id:
            params['org_id'] = org_id
        
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
        
        # Filter description
        filters = []
        if status_filter:
            filters.append(f"status={status_filter}")
        if priority:
            filters.append(f"priority={priority}")
        if target:
            filters.append(f"target={target}")
        if app_version_id:
            filters.append(f"app={app_version_id[:20]}...")
        if org_id:
            filters.append(f"org={org_id}")
        
        filter_text = f" (Filters: {', '.join(filters)})" if filters else ""
        
        # Create table
        table = Table(title=f"Jobs List - {len(jobs)} found{filter_text}")
        table.add_column("ID", style="cyan", justify="center", width=6)
        table.add_column("Priority", style="magenta", justify="center", width=8)
        table.add_column("Status", style="yellow", justify="center", width=10)
        table.add_column("Target", style="green", justify="center", width=8)
        table.add_column("Org", style="blue", width=12)
        table.add_column("App Version", style="blue", width=15)
        table.add_column("Test File", style="white", width=25)
        table.add_column("Created", style="dim", width=16)
        table.add_column("Duration", style="cyan", width=8)
        
        for job in jobs:
            # Priority with visual indicator
            job_priority = job.get('priority', 0)
            if job_priority >= 4:
                priority_display = f"🔥 {job_priority}"
            elif job_priority >= 2:
                priority_display = f"⚡ {job_priority}"
            else:
                priority_display = f"🐌 {job_priority}"
            
            # Status with color and icon
            job_status = job.get('status', 'unknown').lower()
            status_displays = {
                'queued': '[yellow]⏳ QUEUED[/yellow]',
                'running': '[blue]🔄 RUNNING[/blue]',
                'completed': '[green]✅ DONE[/green]',
                'failed': '[red]❌ FAILED[/red]'
            }
            status_display = status_displays.get(job_status, job_status.upper())
            
            # Truncate long fields
            org_id = job.get('org_id', '')[:10] + ('...' if len(job.get('org_id', '')) > 10 else '')
            app_version = job.get('app_version_id', '')[:13] + ('...' if len(job.get('app_version_id', '')) > 13 else '')
            
            test_path = job.get('test_path', '')
            if '/' in test_path:
                test_path = '.../' + test_path.split('/')[-1]
            if len(test_path) > 23:
                test_path = test_path[:20] + '...'
            
            # Format times
            created_at = job.get('created_at', '')
            if 'T' in created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_display = created_dt.strftime('%m-%d %H:%M:%S')
                except:
                    created_display = created_at[:16]
            else:
                created_display = created_at[:16]
            
            # Calculate duration
            duration = "N/A"
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    updated_at = job.get('updated_at', created_at)
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    
                    if job_status in ['completed', 'failed']:
                        duration_sec = (updated_dt - created_dt).total_seconds()
                    else:
                        duration_sec = (datetime.now() - created_dt.replace(tzinfo=None)).total_seconds()
                    
                    if duration_sec < 60:
                        duration = f"{int(duration_sec)}s"
                    elif duration_sec < 3600:
                        duration = f"{int(duration_sec/60)}m"
                    else:
                        duration = f"{int(duration_sec/3600)}h"
                except:
                    duration = "N/A"
            
            table.add_row(
                str(job.get('id', '')),
                priority_display,
                status_display,
                job.get('target', '').upper(),
                org_id,
                app_version,
                test_path,
                created_display,
                duration
            )
        
        console.print(table)
        
        # Summary statistics
        status_counts = {}
        priority_counts = {}
        target_counts = {}
        for job in jobs:
            status = job.get('status', 'unknown')
            priority = job.get('priority', 0)
            target = job.get('target', 'unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            target_counts[target] = target_counts.get(target, 0) + 1
        
        # Summary panel
        summary_text = f"[bold white]Status Distribution:[/] {dict(status_counts)}\n"
        summary_text += f"[bold white]Priority Distribution:[/] {dict(sorted(priority_counts.items(), reverse=True))}\n"
        summary_text += f"[bold white]Target Distribution:[/] {dict(target_counts)}"
        
        summary_panel = Panel.fit(
            summary_text,
            title="[bold blue]Summary Statistics",
            border_style="blue"
        )
        console.print(summary_panel)
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error listing jobs: {str(e)}")
        sys.exit(1)

@jobs.command()
@click.option('--priority', type=click.IntRange(1, 5), help='Show only jobs with this priority')
@click.option('--limit', type=int, default=10, help='Number of recent jobs to show (default: 10)')
def recent(priority, limit):
    """Show recent jobs with priority information."""
    try:
        params = {'limit': limit, 'sort': 'created', 'order': 'desc'}
        if priority:
            params['priority'] = priority
        
        response = requests.get("http://localhost:8002/jobs", params=params)
        
        if response.status_code != 200:
            print_error(f"Failed to get recent jobs: {response.text}")
            return
        
        jobs = response.json()
        
        if not jobs:
            console.print("[yellow]No recent jobs found.[/yellow]")
            return
        
        console.print(f"[bold blue]📋 Recent Jobs{' (Priority ' + str(priority) + ')' if priority else ''}[/bold blue]\n")
        
        for i, job in enumerate(jobs, 1):
            job_priority = job.get('priority', 0)
            job_status = job.get('status', 'unknown')
            
            # Priority icon
            if job_priority >= 4:
                priority_icon = "🔥"
                priority_color = "red"
            elif job_priority >= 2:
                priority_icon = "⚡"
                priority_color = "yellow"
            else:
                priority_icon = "🐌"
                priority_color = "blue"
            
            # Status icon
            status_icons = {
                'queued': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }
            status_icon = status_icons.get(job_status.lower(), '❓')
            
            # Time ago
            created_at = job.get('created_at', '')
            time_ago = "unknown"
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    now = datetime.now()
                    delta = now - created_dt.replace(tzinfo=None)
                    
                    if delta.total_seconds() < 60:
                        time_ago = f"{int(delta.total_seconds())}s ago"
                    elif delta.total_seconds() < 3600:
                        time_ago = f"{int(delta.total_seconds()/60)}m ago"
                    elif delta.total_seconds() < 86400:
                        time_ago = f"{int(delta.total_seconds()/3600)}h ago"
                    else:
                        time_ago = f"{int(delta.total_seconds()/86400)}d ago"
                except:
                    time_ago = "unknown"
            
            # Format test path
            test_path = job.get('test_path', '')
            if '/' in test_path:
                test_path = test_path.split('/')[-1]
            
            console.print(f"{i:2}. {status_icon} Job {job.get('id', '')} - {priority_icon}[{priority_color}]P{job_priority}[/{priority_color}] - {job_status.upper()} - {test_path} ({time_ago})")
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting recent jobs: {str(e)}")
        sys.exit(1)

@jobs.command()
@click.argument('job_id', type=int)
@click.option('--force', '-f', is_flag=True, help='Force cancellation without confirmation')
def cancel(job_id, force):
    """Cancel a queued or running job."""
    try:
        # First get job status
        client = APIClient()
        job_info = client.get_job_status(str(job_id))
        
        current_status = job_info.get('status', '').lower()
        
        if current_status in ['completed', 'failed']:
            console.print(f"[yellow]Job {job_id} is already {current_status} and cannot be cancelled.[/yellow]")
            return
        
        if current_status not in ['queued', 'running']:
            console.print(f"[yellow]Job {job_id} has status '{current_status}' and cannot be cancelled.[/yellow]")
            return
        
        # Show job info
        priority = job_info.get('priority', 0)
        test_path = job_info.get('test_path', '')
        if '/' in test_path:
            test_path = test_path.split('/')[-1]
        
        priority_icon = "🔥" if priority >= 4 else "⚡" if priority >= 2 else "🐌"
        
        console.print(f"\n[bold]Job to Cancel:[/bold]")
        console.print(f"  ID: {job_id}")
        console.print(f"  Priority: {priority_icon} {priority}")
        console.print(f"  Status: {current_status.upper()}")
        console.print(f"  Test: {test_path}")
        
        # Confirmation
        if not force:
            confirm = click.confirm("\nAre you sure you want to cancel this job?")
            if not confirm:
                console.print("[dim]Cancellation aborted.[/dim]")
                return
        
        # Make cancellation request
        response = requests.delete(f"http://localhost:8002/jobs/{job_id}")
        
        if response.status_code == 200:
            console.print(f"[green]✅ Job {job_id} has been cancelled successfully.[/green]")
        elif response.status_code == 404:
            console.print(f"[red]❌ Job {job_id} not found.[/red]")
        elif response.status_code == 400:
            error_msg = response.json().get('detail', 'Bad request')
            console.print(f"[red]❌ Cannot cancel job: {error_msg}[/red]")
        else:
            console.print(f"[red]❌ Failed to cancel job: {response.text}[/red]")
        
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error cancelling job: {str(e)}")
        sys.exit(1)

@jobs.command()
@click.option('--watch', '-w', is_flag=True, help='Watch job activity in real-time')
@click.option('--priority', type=click.IntRange(1, 5), help='Filter by priority level')
def active(watch, priority):
    """Show currently active (queued + running) jobs."""
    def display_active():
        try:
            params = {'status': 'queued,running'}
            if priority:
                params['priority'] = priority
            
            response = requests.get("http://localhost:8002/jobs", params=params)
            
            if response.status_code != 200:
                print_error(f"Failed to get active jobs: {response.text}")
                return False
            
            jobs = response.json()
            
            if watch:
                console.clear()
            
            title = "🔄 Active Jobs"
            if priority:
                title += f" (Priority {priority})"
            if watch:
                title += " (Live)"
            
            console.print(f"[bold blue]{title}[/bold blue]\n")
            
            if not jobs:
                console.print("[dim]No active jobs found.[/dim]")
                return True
            
            # Separate queued and running
            queued_jobs = [j for j in jobs if j.get('status', '').lower() == 'queued']
            running_jobs = [j for j in jobs if j.get('status', '').lower() == 'running']
            
            # Running jobs
            if running_jobs:
                console.print("[bold green]🔄 Currently Running:[/bold green]")
                for job in sorted(running_jobs, key=lambda x: -x.get('priority', 0)):
                    job_priority = job.get('priority', 0)
                    priority_icon = "🔥" if job_priority >= 4 else "⚡" if job_priority >= 2 else "🐌"
                    
                    test_path = job.get('test_path', '')
                    if '/' in test_path:
                        test_path = test_path.split('/')[-1]
                    
                    device = job.get('assigned_device_name', 'No device')
                    
                    console.print(f"  {priority_icon} Job {job.get('id', '')} (P{job_priority}) - {test_path} on {device}")
                
                console.print()
            
            # Queued jobs
            if queued_jobs:
                console.print("[bold yellow]⏳ Waiting in Queue:[/bold yellow]")
                for job in sorted(queued_jobs, key=lambda x: -x.get('priority', 0)):
                    job_priority = job.get('priority', 0)
                    priority_icon = "🔥" if job_priority >= 4 else "⚡" if job_priority >= 2 else "🐌"
                    
                    test_path = job.get('test_path', '')
                    if '/' in test_path:
                        test_path = test_path.split('/')[-1]
                    
                    # Show time in queue
                    created_at = job.get('created_at', '')
                    queue_time = ""
                    if created_at:
                        try:
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            now = datetime.now()
                            delta = now - created_dt.replace(tzinfo=None)
                            
                            if delta.total_seconds() < 60:
                                queue_time = f" ({int(delta.total_seconds())}s in queue)"
                            else:
                                queue_time = f" ({int(delta.total_seconds()/60)}m in queue)"
                        except:
                            pass
                    
                    console.print(f"  {priority_icon} Job {job.get('id', '')} (P{job_priority}) - {test_path}{queue_time}")
            
            # Summary
            total_active = len(jobs)
            console.print(f"\n[dim]Total active: {total_active} ({len(running_jobs)} running, {len(queued_jobs)} queued)[/dim]")
            
            if watch:
                console.print(f"[dim]Updated: {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to stop[/dim]")
            
            return True
            
        except Exception as e:
            print_error(f"Error getting active jobs: {str(e)}")
            return False
    
    try:
        if watch:
            while True:
                if not display_active():
                    break
                time.sleep(3)
        else:
            display_active()
            
    except KeyboardInterrupt:
        console.print("\n[dim]Monitoring stopped.[/dim]")
    except Exception as e:
        print_error(f"Error in active jobs monitor: {str(e)}")
        sys.exit(1) 
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
def queue():
    """Queue management and monitoring commands."""
    pass

@queue.command()
def status():
    """Show current queue status across all priority levels."""
    try:
        # Get queue status from the API
        response = requests.get("http://localhost:8002/queues/status")
        if response.status_code != 200:
            print_error(f"Failed to get queue status: {response.text}")
            return
        
        data = response.json()
        
        # Queue Summary Panel
        queue_summary = data.get('queue_summary', {})
        summary_text = "[bold white]Queue Status Summary[/bold white]\n\n"
        
        for queue_name, stats in queue_summary.items():
            queue_display = queue_name.replace('_', ' ').title()
            total_active = stats.get('total_active', 0)
            queued = stats.get('queued_jobs', 0)
            running = stats.get('running_jobs', 0)
            
            # Color code based on activity
            if total_active == 0:
                color = "green"
                status_icon = "✅"
            elif queued > running:
                color = "yellow" 
                status_icon = "⏳"
            else:
                color = "blue"
                status_icon = "🔄"
            
            summary_text += f"{status_icon} [{color}]{queue_display}[/{color}]: {total_active} active ({queued} queued, {running} running)\n"
        
        summary_panel = Panel.fit(
            summary_text,
            title="[bold blue]Priority Queue Status",
            border_style="blue"
        )
        console.print(summary_panel)
        
        # Priority Breakdown Table
        priority_breakdown = data.get('priority_breakdown', {})
        if any(stats.get('total_active', 0) > 0 for stats in priority_breakdown.values()):
            console.print("\n[bold]Active Jobs by Priority:[/bold]")
            
            table = Table()
            table.add_column("Priority", style="cyan", justify="center")
            table.add_column("Queue", style="green")
            table.add_column("Queued", style="yellow", justify="center")
            table.add_column("Running", style="blue", justify="center")
            table.add_column("Total", style="magenta", justify="center")
            
            for priority_key in sorted(priority_breakdown.keys(), key=lambda x: int(x.split('_')[1]), reverse=True):
                stats = priority_breakdown[priority_key]
                if stats.get('total_active', 0) > 0:
                    priority_num = priority_key.split('_')[1]
                    queue_name = stats.get('queue_name', '').replace('_', ' ').title()
                    
                    # Add priority indicator
                    if int(priority_num) >= 4:
                        priority_display = f"🔥 {priority_num}"
                    elif int(priority_num) >= 2:
                        priority_display = f"⚡ {priority_num}"
                    else:
                        priority_display = f"🐌 {priority_num}"
                    
                    table.add_row(
                        priority_display,
                        queue_name,
                        str(stats.get('queued_jobs', 0)),
                        str(stats.get('running_jobs', 0)),
                        str(stats.get('total_active', 0))
                    )
            
            console.print(table)
        else:
            console.print("\n[dim]No active jobs in any priority queue.[/dim]")
        
        # Timestamp
        timestamp = data.get('timestamp', 'Unknown')
        console.print(f"\n[dim]Last updated: {timestamp}[/dim]")
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting queue status: {str(e)}")
        sys.exit(1)

@queue.command()
def info():
    """Show priority queue configuration and routing information."""
    try:
        # Get priority queue info
        response = requests.get("http://localhost:8002/queues/priority-info")
        if response.status_code != 200:
            print_error(f"Failed to get priority info: {response.text}")
            return
        
        data = response.json()
        priority_queues = data.get('priority_queues', {})
        
        # Priority Mapping Table
        mapping = priority_queues.get('priority_mapping', {})
        descriptions = priority_queues.get('description', {})
        
        console.print("[bold blue]Priority Queue Configuration[/bold blue]\n")
        
        table = Table(title="Priority to Queue Mapping")
        table.add_column("Priority Level", style="cyan", justify="center")
        table.add_column("Queue Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Processing Order", style="yellow", justify="center")
        
        # Sort by priority (highest first)
        for priority in sorted(mapping.keys(), key=int, reverse=True):
            queue_name = mapping[priority]
            description = descriptions.get(queue_name, 'No description')
            
            # Add visual indicators
            if int(priority) >= 4:
                priority_display = f"🔥 {priority} (High)"
                order = "1st"
            elif int(priority) >= 2:
                priority_display = f"⚡ {priority} (Normal)"  
                order = "2nd"
            else:
                priority_display = f"🐌 {priority} (Low)"
                order = "3rd"
            
            queue_display = queue_name.replace('_', ' ').title()
            
            table.add_row(priority_display, queue_display, description, order)
        
        console.print(table)
        
        # Queue Processing Order
        queue_order = priority_queues.get('queue_order', [])
        if queue_order:
            console.print(f"\n[bold]Processing Order:[/bold]")
            for i, queue_name in enumerate(queue_order, 1):
                queue_display = queue_name.replace('_', ' ').title()
                console.print(f"  {i}. {queue_display}")
        
        # Configuration status
        status = data.get('status', 'unknown')
        status_color = "green" if status == "active" else "red"
        console.print(f"\n[bold]Status:[/bold] [{status_color}]{status.upper()}[/{status_color}]")
        
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error getting priority info: {str(e)}")
        sys.exit(1)

@queue.command()
@click.option('--watch', '-w', is_flag=True, help='Watch queue status in real-time (refresh every 5 seconds)')
def monitor(watch):
    """Monitor queue activity and job flow."""
    import time
    
    def display_monitor():
        try:
            # Clear screen for watch mode
            if watch:
                console.clear()
            
            # Get queue status
            response = requests.get("http://localhost:8002/queues/status")
            if response.status_code != 200:
                print_error(f"Failed to get queue status: {response.text}")
                return False
            
            data = response.json()
            
            # Title
            title = Text("🔍 Queue Monitor", style="bold blue")
            if watch:
                title.append(" (Live)", style="dim")
            console.print(title)
            console.print()
            
            # Real-time queue metrics
            queue_summary = data.get('queue_summary', {})
            
            # Quick stats panel
            total_queued = sum(stats.get('queued_jobs', 0) for stats in queue_summary.values())
            total_running = sum(stats.get('running_jobs', 0) for stats in queue_summary.values())
            total_active = total_queued + total_running
            
            metrics_panel = Panel.fit(
                f"[bold white]Total Active Jobs:[/] {total_active}\n"
                f"[bold yellow]Queued:[/] {total_queued}\n"
                f"[bold blue]Running:[/] {total_running}",
                title="[bold green]Live Metrics",
                border_style="green"
            )
            console.print(metrics_panel)
            
            # Queue activity table
            table = Table(title="Queue Activity")
            table.add_column("Queue", style="cyan")
            table.add_column("Queued", style="yellow", justify="center") 
            table.add_column("Running", style="blue", justify="center")
            table.add_column("Total", style="magenta", justify="center")
            table.add_column("Status", style="green", justify="center")
            
            for queue_name, stats in queue_summary.items():
                queue_display = queue_name.replace('_', ' ').title()
                queued = stats.get('queued_jobs', 0)
                running = stats.get('running_jobs', 0)
                total = queued + running
                
                # Status indicator
                if total == 0:
                    status = "[green]Idle[/green]"
                elif queued > running:
                    status = "[yellow]Backlog[/yellow]"
                else:
                    status = "[blue]Active[/blue]"
                
                table.add_row(
                    queue_display,
                    str(queued),
                    str(running), 
                    str(total),
                    status
                )
            
            console.print(table)
            
            # Last updated
            timestamp = data.get('timestamp', 'Unknown')
            console.print(f"\n[dim]Updated: {timestamp}[/dim]")
            
            return True
            
        except Exception as e:
            print_error(f"Monitor error: {str(e)}")
            return False
    
    try:
        if watch:
            console.print("[dim]Press Ctrl+C to stop monitoring...[/dim]\n")
            while True:
                if not display_monitor():
                    break
                time.sleep(5)
        else:
            display_monitor()
            
    except KeyboardInterrupt:
        console.print("\n[dim]Monitoring stopped.[/dim]")
    except Exception as e:
        print_error(f"Error in monitor: {str(e)}")
        sys.exit(1) 
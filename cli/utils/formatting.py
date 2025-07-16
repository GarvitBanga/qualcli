from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def format_job_submission(org_id: str, app_version_id: str, test_path: str, priority: int, target: str):
    """Format job submission details in a panel with priority indicators."""
    # Priority visual indicator and description
    if priority >= 4:
        priority_display = f"🔥 {priority} (High Priority)"
        priority_color = "red"
        priority_desc = "Will be processed first"
    elif priority >= 2:
        priority_display = f"⚡ {priority} (Normal Priority)"
        priority_color = "yellow"
        priority_desc = "Standard processing order"
    else:
        priority_display = f"🐌 {priority} (Low Priority)"
        priority_color = "blue"
        priority_desc = "Will be processed when idle"
    
    # Target icon
    target_icons = {
        'emulator': '📱',
        'device': '📲',
        'browserstack': '☁️'
    }
    target_icon = target_icons.get(target.lower(), '🎯')
    
    panel = Panel.fit(
        f"[bold white]Organization ID:[/] {org_id}\n"
        f"[bold white]App Version ID:[/] {app_version_id}\n"
        f"[bold white]Test Path:[/] {test_path}\n"
        f"[bold white]Priority:[/] [{priority_color}]{priority_display}[/{priority_color}]\n"
        f"[dim]             {priority_desc}[/dim]\n"
        f"[bold white]Target:[/] {target_icon} {target.title()}",
        title="[bold blue]Job Submission Details",
        border_style="blue"
    )
    console.print(panel)

def format_job_result(job_id: int, status: str, created_at: str, priority: int = None):
    """Format job result with color-coded status and priority info."""
    status_colors = {
        'queued': 'yellow',
        'running': 'blue',
        'completed': 'green',
        'failed': 'red'
    }
    color = status_colors.get(status.lower(), 'white')
    
    # Status with icon
    status_icons = {
        'queued': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌'
    }
    status_icon = status_icons.get(status.lower(), '❓')
    status_display = f"{status_icon} {status.upper()}"
    
    # Build content
    content = (
        f"[bold white]Job ID:[/] {job_id}\n"
        f"[bold white]Status:[/] [{color}]{status_display}[/{color}]\n"
        f"[bold white]Created at:[/] {created_at}"
    )
    
    # Add priority info if available
    if priority is not None:
        if priority >= 4:
            priority_display = f"🔥 {priority} (High)"
            priority_color = "red"
        elif priority >= 2:
            priority_display = f"⚡ {priority} (Normal)"
            priority_color = "yellow"
        else:
            priority_display = f"🐌 {priority} (Low)"
            priority_color = "blue"
        
        content = content.replace(
            f"[bold white]Created at:[/] {created_at}",
            f"[bold white]Priority:[/] [{priority_color}]{priority_display}[/{priority_color}]\n"
            f"[bold white]Created at:[/] {created_at}"
        )
    
    panel = Panel.fit(
        content,
        title="[bold green]Job Submitted Successfully",
        border_style="green"
    )
    console.print(panel)

def format_job_status(job_id: int, status: str, created_at: str, priority: int = None, target: str = None, device: str = None):
    """Format job status with comprehensive information and visual indicators."""
    status_colors = {
        'queued': 'yellow',
        'running': 'blue',
        'completed': 'green',
        'failed': 'red'
    }
    color = status_colors.get(status.lower(), 'white')
    
    # Status with icon
    status_icons = {
        'queued': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌'
    }
    status_icon = status_icons.get(status.lower(), '❓')
    status_display = f"{status_icon} {status.upper()}"
    
    # Build content
    content = (
        f"[bold white]Job ID:[/] {job_id}\n"
        f"[bold white]Status:[/] [{color}]{status_display}[/{color}]\n"
    )
    
    # Add priority info
    if priority is not None:
        if priority >= 4:
            priority_display = f"🔥 {priority} (High Priority)"
            priority_color = "red"
        elif priority >= 2:
            priority_display = f"⚡ {priority} (Normal Priority)"
            priority_color = "yellow"
        else:
            priority_display = f"🐌 {priority} (Low Priority)"
            priority_color = "blue"
        
        content += f"[bold white]Priority:[/] [{priority_color}]{priority_display}[/{priority_color}]\n"
    
    # Add target info
    if target:
        target_icons = {
            'emulator': '📱',
            'device': '📲',
            'browserstack': '☁️'
        }
        target_icon = target_icons.get(target.lower(), '🎯')
        content += f"[bold white]Target:[/] {target_icon} {target.title()}\n"
    
    # Add device info
    if device and device != 'Not assigned':
        content += f"[bold white]Device:[/] {device}\n"
    
    content += f"[bold white]Created at:[/] {created_at}"
    
    panel = Panel.fit(
        content,
        title="[bold blue]Job Status",
        border_style="blue"
    )
    console.print(panel)

def format_priority_indicator(priority: int) -> str:
    """Get priority indicator with icon and color."""
    if priority >= 4:
        return f"🔥 {priority}"
    elif priority >= 2:
        return f"⚡ {priority}"
    else:
        return f"🐌 {priority}"

def format_status_indicator(status: str) -> str:
    """Get status indicator with icon and color."""
    status_lower = status.lower()
    if status_lower == 'queued':
        return '[yellow]⏳ QUEUED[/yellow]'
    elif status_lower == 'running':
        return '[blue]🔄 RUNNING[/blue]'
    elif status_lower == 'completed':
        return '[green]✅ DONE[/green]'
    elif status_lower == 'failed':
        return '[red]❌ FAILED[/red]'
    else:
        return f'[white]❓ {status.upper()}[/white]'

def print_error(message: str):
    """Print error message in red panel."""
    panel = Panel.fit(
        f"[bold red]{message}[/]",
        title="[bold red]Error",
        border_style="red"
    )
    console.print(panel)

def print_success(message: str, title: str = "Success"):
    """Print success message in green panel."""
    panel = Panel.fit(
        f"[bold green]{message}[/]",
        title=f"[bold green]{title}",
        border_style="green"
    )
    console.print(panel)

def print_warning(message: str, title: str = "Warning"):
    """Print warning message in yellow panel."""
    panel = Panel.fit(
        f"[bold yellow]{message}[/]",
        title=f"[bold yellow]{title}",
        border_style="yellow"
    )
    console.print(panel) 
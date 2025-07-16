import click
from ..client import APIClient, APIError
from ..utils.formatting import format_job_submission, format_job_result, print_error, print_success
from ..utils.validation import validate_test_file
import sys

# Valid target environments
VALID_TARGETS = ['emulator', 'device', 'browserstack']

@click.command()
@click.option('--org-id', required=True, help='Organization ID')
@click.option('--app-version-id', required=True, help='Application version ID')
@click.option('--test', required=True, help='Path to test file')
@click.option('--priority', type=int, default=1, help='Job priority (1-5, default: 1)')
@click.option('--target', type=click.Choice(VALID_TARGETS), default='emulator',
              help='Target environment for test execution')
@click.option('--show-queue-info', is_flag=True, help='Show priority queue information after submission')
def submit(org_id, app_version_id, test, priority, target, show_queue_info):
    """Submit a test job for execution with priority scheduling."""
    try:
        # Validate priority
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")

        # Validate test file
        try:
            test_path = validate_test_file(test)
        except ValueError as e:
            print_error(str(e))
            sys.exit(1)

        # Show what we're about to do
        format_job_submission(org_id, app_version_id, test_path, priority, target)

        # Submit the job
        client = APIClient()
        result = client.submit_job(
            org_id=org_id,
            app_version_id=app_version_id,
            test_path=test_path,
            priority=priority,
            target=target
        )
        
        # Show the result with priority info
        format_job_result(
            job_id=result['job_id'],
            status=result['status'],
            created_at=result['created_at'],
            priority=priority
        )

        # Show priority queue routing info
        if priority >= 4:
            queue_name = "High Priority Queue"
            queue_desc = "🔥 This job will be processed first"
        elif priority >= 2:
            queue_name = "Normal Priority Queue"
            queue_desc = "⚡ This job will be processed in standard order"
        else:
            queue_name = "Low Priority Queue"
            queue_desc = "🐌 This job will be processed when system is idle"
        
        click.echo(f"\n[bold blue]Queue Routing:[/bold blue] {queue_desc}")
        click.echo(f"[dim]Routed to: {queue_name}[/dim]")

        # Try to get grouped jobs with enhanced display
        try:
            grouped_jobs = client.get_grouped_jobs(app_version_id)
            if grouped_jobs and len(grouped_jobs) > 1:
                click.echo(f"\n[bold]Other jobs in this group ({app_version_id}):[/bold]")
                
                # Sort by priority and creation time
                sorted_jobs = sorted(grouped_jobs, key=lambda x: (-x.get('priority', 0), x.get('created_at', '')))
                
                for job in sorted_jobs:
                    if job['job_id'] != result['job_id']:  # Don't show the job we just created
                        job_priority = job.get('priority', 0)
                        
                        # Priority indicator
                        if job_priority >= 4:
                            priority_icon = "🔥"
                        elif job_priority >= 2:
                            priority_icon = "⚡"
                        else:
                            priority_icon = "🐌"
                        
                        # Status indicator
                        status = job.get('status', 'unknown').lower()
                        if status == 'completed':
                            status_icon = "✅"
                        elif status == 'running':
                            status_icon = "🔄"
                        elif status == 'failed':
                            status_icon = "❌"
                        else:
                            status_icon = "⏳"
                        
                        click.echo(f"  • {status_icon} Job {job['job_id']} - {priority_icon}P{job_priority} - {job['status'].upper()}")
        except Exception:
            # Silently ignore if we can't get grouped jobs
            pass

        # Show queue info if requested
        if show_queue_info:
            try:
                import requests
                response = requests.get("http://localhost:8002/queues/status")
                if response.status_code == 200:
                    data = response.json()
                    queue_summary = data.get('queue_summary', {})
                    
                    click.echo(f"\n[bold blue]📊 Current Queue Status:[/bold blue]")
                    for queue_name, stats in queue_summary.items():
                        if stats.get('total_active', 0) > 0:
                            queue_display = queue_name.replace('_', ' ').title()
                            click.echo(f"  • {queue_display}: {stats.get('total_active', 0)} active jobs")
            except:
                # Silently ignore queue status errors
                pass

    except ValueError as ve:
        print_error(str(ve))
        sys.exit(1)
    except APIError as ae:
        print_error(str(ae))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error submitting job: {str(e)}")
        sys.exit(1) 
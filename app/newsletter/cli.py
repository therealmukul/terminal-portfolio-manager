"""Newsletter CLI commands."""

import argparse
import signal
import sys
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from app.config import get_settings
from app.services.newsletter_service import NewsletterService
from app.utils.exceptions import EmailServiceError, NewsletterError


console = Console()


def send_once() -> int:
    """
    Send the newsletter once and exit.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    load_dotenv()
    settings = get_settings()

    console.print(Panel(
        "[bold cyan]Portfolio Newsletter[/bold cyan]\n"
        "[dim]Generating and sending newsletter...[/dim]",
        border_style="cyan",
    ))

    try:
        service = NewsletterService(settings)

        # Check configuration
        if not service.email_service.is_configured():
            console.print("[red]Email not configured![/red]")
            console.print(
                "\nPlease set these environment variables in your .env file:\n"
                "  SMTP_USERNAME=your_email@gmail.com\n"
                "  SMTP_PASSWORD=your_app_password\n"
                "  NEWSLETTER_SENDER_EMAIL=your_email@gmail.com\n"
                "  NEWSLETTER_RECIPIENTS=recipient1@example.com,recipient2@example.com"
            )
            return 1

        recipients = settings.get_newsletter_recipients()
        if not recipients:
            console.print("[red]No recipients configured![/red]")
            console.print(
                "\nSet NEWSLETTER_RECIPIENTS in your .env file:\n"
                "  NEWSLETTER_RECIPIENTS=recipient1@example.com,recipient2@example.com"
            )
            return 1

        # Generate newsletter
        console.print("[dim]Fetching portfolio data...[/dim]")
        console.print("[dim]Fetching news for holdings...[/dim]")
        console.print("[dim]Analyzing news with AI...[/dim]")

        subject, html_content, analysis = service.generate_newsletter()

        # Show preview
        sentiment = analysis.portfolio_sentiment.value.replace("_", " ").upper()
        console.print(f"\n[bold]Subject:[/bold] {subject}")
        console.print(f"[bold]Sentiment:[/bold] {sentiment}")
        console.print(f"[bold]Holdings analyzed:[/bold] {analysis.stocks_analyzed}")
        console.print(f"[bold]Articles analyzed:[/bold] {analysis.total_articles_analyzed}")
        console.print(f"[bold]Recipients:[/bold] {', '.join(recipients)}")

        # Send
        console.print("\n[dim]Sending email...[/dim]")
        service.email_service.send_email(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
        )

        console.print(Panel(
            f"[green]Newsletter sent successfully![/green]\n"
            f"[dim]Sent to {len(recipients)} recipient(s) at {datetime.now().strftime('%I:%M %p')}[/dim]",
            border_style="green",
        ))
        return 0

    except NewsletterError as e:
        console.print(f"[red]Newsletter error: {e}[/red]")
        return 1
    except EmailServiceError as e:
        console.print(f"[red]Email error: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


def run_scheduler() -> int:
    """
    Run the newsletter scheduler daemon.

    Returns:
        Exit code (0 for normal exit, 1 for failure)
    """
    load_dotenv()
    settings = get_settings()

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        console.print("[red]APScheduler not installed. Run: pip install apscheduler[/red]")
        return 1

    # Parse schedule times
    try:
        morning_hour, morning_minute = map(int, settings.newsletter_schedule_morning.split(":"))
        evening_hour, evening_minute = map(int, settings.newsletter_schedule_evening.split(":"))
    except ValueError:
        console.print("[red]Invalid schedule format. Use HH:MM format.[/red]")
        return 1

    # Check configuration
    service = NewsletterService(settings)
    if not service.email_service.is_configured():
        console.print("[red]Email not configured![/red]")
        console.print(
            "\nPlease set these environment variables in your .env file:\n"
            "  SMTP_USERNAME=your_email@gmail.com\n"
            "  SMTP_PASSWORD=your_app_password\n"
            "  NEWSLETTER_SENDER_EMAIL=your_email@gmail.com\n"
            "  NEWSLETTER_RECIPIENTS=recipient1@example.com,recipient2@example.com"
        )
        return 1

    recipients = settings.get_newsletter_recipients()
    if not recipients:
        console.print("[red]No recipients configured![/red]")
        return 1

    def send_newsletter_job():
        """Job function to send newsletter."""
        console.print(f"\n[cyan][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sending scheduled newsletter...[/cyan]")
        try:
            service.send_newsletter()
            console.print(f"[green]Newsletter sent successfully to {len(recipients)} recipient(s)[/green]")
        except Exception as e:
            console.print(f"[red]Failed to send newsletter: {e}[/red]")

    # Create scheduler
    scheduler = BlockingScheduler()

    # Add morning job
    scheduler.add_job(
        send_newsletter_job,
        CronTrigger(hour=morning_hour, minute=morning_minute),
        id="morning_newsletter",
        name=f"Morning Newsletter ({settings.newsletter_schedule_morning})",
    )

    # Add evening job
    scheduler.add_job(
        send_newsletter_job,
        CronTrigger(hour=evening_hour, minute=evening_minute),
        id="evening_newsletter",
        name=f"Evening Newsletter ({settings.newsletter_schedule_evening})",
    )

    # Handle shutdown gracefully
    def shutdown(signum, frame):
        console.print("\n[yellow]Shutting down scheduler...[/yellow]")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Display info
    console.print(Panel(
        "[bold cyan]Portfolio Newsletter Scheduler[/bold cyan]\n\n"
        f"[bold]Morning:[/bold] {settings.newsletter_schedule_morning}\n"
        f"[bold]Evening:[/bold] {settings.newsletter_schedule_evening}\n"
        f"[bold]Recipients:[/bold] {', '.join(recipients)}\n\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        border_style="cyan",
    ))

    # Start scheduler
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    return 0


def main() -> None:
    """Main entry point for newsletter CLI."""
    parser = argparse.ArgumentParser(
        description="Portfolio newsletter - send portfolio news analysis via email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  portfolio-newsletter              # Send newsletter once
  portfolio-newsletter --daemon     # Run scheduler daemon (sends at 8:00 AM and 5:30 PM)
  portfolio-newsletter --test       # Test email configuration

Environment variables (set in .env):
  SMTP_HOST                    SMTP server (default: smtp.gmail.com)
  SMTP_PORT                    SMTP port (default: 587)
  SMTP_USERNAME                Your email address
  SMTP_PASSWORD                Your email password or app password
  NEWSLETTER_SENDER_EMAIL      Sender email address
  NEWSLETTER_SENDER_NAME       Sender name (default: Portfolio Manager)
  NEWSLETTER_RECIPIENTS        Comma-separated recipient emails
  NEWSLETTER_SCHEDULE_MORNING  Morning send time (default: 08:00)
  NEWSLETTER_SCHEDULE_EVENING  Evening send time (default: 17:30)
        """,
    )

    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as a scheduler daemon (sends at configured times)",
    )

    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test email configuration without sending newsletter",
    )

    args = parser.parse_args()

    if args.test:
        sys.exit(test_configuration())
    elif args.daemon:
        sys.exit(run_scheduler())
    else:
        sys.exit(send_once())


def test_configuration() -> int:
    """Test email configuration."""
    load_dotenv()
    settings = get_settings()

    console.print(Panel(
        "[bold cyan]Testing Newsletter Configuration[/bold cyan]",
        border_style="cyan",
    ))

    # Check SMTP settings
    console.print("\n[bold]SMTP Configuration:[/bold]")
    console.print(f"  Host: {settings.smtp_host}")
    console.print(f"  Port: {settings.smtp_port}")
    console.print(f"  Username: {'✓ Set' if settings.smtp_username else '✗ Not set'}")
    console.print(f"  Password: {'✓ Set' if settings.smtp_password else '✗ Not set'}")

    # Check newsletter settings
    console.print("\n[bold]Newsletter Configuration:[/bold]")
    console.print(f"  Sender Email: {settings.newsletter_sender_email or 'Not set'}")
    console.print(f"  Sender Name: {settings.newsletter_sender_name}")

    recipients = settings.get_newsletter_recipients()
    if recipients:
        console.print(f"  Recipients: {', '.join(recipients)}")
    else:
        console.print("  Recipients: [red]Not set[/red]")

    console.print(f"  Morning Schedule: {settings.newsletter_schedule_morning}")
    console.print(f"  Evening Schedule: {settings.newsletter_schedule_evening}")

    # Check AI service
    console.print("\n[bold]AI Service:[/bold]")
    console.print(f"  API Key: {'✓ Set' if settings.anthropic_api_key else '✗ Not set'}")

    # Overall status
    service = NewsletterService(settings)
    issues = []

    if not service.email_service.is_configured():
        issues.append("Email service not fully configured")
    if not recipients:
        issues.append("No recipients configured")
    if not settings.anthropic_api_key:
        issues.append("Anthropic API key not set (required for AI analysis)")

    console.print("\n")
    if issues:
        console.print(Panel(
            "[red]Configuration incomplete:[/red]\n" +
            "\n".join(f"  • {issue}" for issue in issues),
            border_style="red",
        ))
        return 1
    else:
        console.print(Panel(
            "[green]Configuration looks good![/green]\n"
            "Run [bold]portfolio-newsletter[/bold] to send a newsletter.",
            border_style="green",
        ))
        return 0


if __name__ == "__main__":
    main()

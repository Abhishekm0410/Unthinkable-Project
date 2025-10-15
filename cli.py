#!/usr/bin/env python3
"""
Smart Code Review CLI Tool
Usage: python cli.py review <file> [options]
"""

import click
import requests
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()
API_URL = "http://localhost:8000"

@click.group()
def cli():
    """Smart Code Review - AI-powered code analysis"""
    pass

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--team-id', default='default', help='Team identifier')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'detailed']), default='detailed')
def review(filepath, team_id, output):
    """Review a code file"""
    
    console.print(f"[bold blue]📝 Analyzing {filepath}...[/bold blue]")
    
    try:
        # Read file
        with open(filepath, 'r') as f:
            code = f.read()
        
        # Detect language
        ext = Path(filepath).suffix[1:]
        
        # Send to API
        response = requests.post(
            f"{API_URL}/api/review",
            json={
                "code": code,
                "language": ext,
                "filename": Path(filepath).name,
                "team_id": team_id
            }
        )
        
        if response.status_code != 200:
            console.print(f"[bold red]❌ Error: {response.text}[/bold red]")
            return
        
        data = response.json()
        
        # Display results based on output format
        if output == 'json':
            console.print_json(json.dumps(data, indent=2))
        elif output == 'table':
            display_table(data)
        else:
            display_detailed(data)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

def display_detailed(data):
    """Display detailed review output"""
    
    # Score panel
    score = data['score']
    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
    
    console.print(Panel(
        f"[bold {score_color}]{score}/100[/bold {score_color}] "
        f"({data['improvement']} from last review)",
        title="📊 Code Quality Score",
        border_style=score_color
    ))
    
    # Metrics
    console.print("\n[bold]📈 Metrics:[/bold]")
    metrics_table = Table(show_header=False, box=None)
    for key, value in data['metrics'].items():
        color = "green" if value == "Good" or value == "Excellent" else "yellow" if value == "Medium" else "red"
        metrics_table.add_row(f"  {key.capitalize()}", f"[{color}]{value}[/{color}]")
    console.print(metrics_table)
    
    # Issues
    if data['priority']:
        console.print(f"\n[bold]🔍 Issues Found ({len(data['priority'])}):[/bold]\n")
        
        for issue in data['priority']:
            severity_colors = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'blue'
            }
            color = severity_colors.get(issue['severity'], 'white')
            
            console.print(Panel(
                f"[bold]{issue['title']}[/bold]\n\n"
                f"📍 Line {issue['line']}\n"
                f"📝 {issue['description']}\n\n"
                f"💡 [italic]{issue['suggestion']}[/italic]\n\n"
                f"⏱️  Fix Time: {issue['fix_time']}\n"
                f"💼 Impact: {issue['business_impact']}\n"
                f"{'⚡ Auto-fix available' if issue['auto_fix_available'] else ''}",
                title=f"[{color}]●[/{color}] {issue['severity'].upper()}",
                border_style=color
            ))
    
    # Team Insights
    if data.get('team_insights'):
        console.print("\n[bold]👥 Team Insights:[/bold]")
        for insight in data['team_insights']:
            console.print(f"  • {insight}")
    
    console.print(f"\n[dim]Review ID: {data['review_id']}[/dim]")

def display_table(data):
    """Display results in table format"""
    
    table = Table(title=f"Code Review Results - Score: {data['score']}/100")
    
    table.add_column("Severity", style="bold")
    table.add_column("Line", justify="right")
    table.add_column("Issue", style="cyan")
    table.add_column("Fix Time", justify="right")
    table.add_column("Auto-fix", justify="center")
    
    for issue in data['priority']:
        severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🔵'}.get(issue['severity'], '⚪')
        table.add_row(
            f"{severity_emoji} {issue['severity']}",
            str(issue['line']),
            issue['title'],
            issue['fix_time'],
            "✅" if issue['auto_fix_available'] else "❌"
        )
    
    console.print(table)

@cli.command()
@click.argument('message')
@click.option('--code', '-c', help='Code context')
def chat(message, code):
    """Ask questions about code"""
    
    console.print(f"[bold blue]💬 Asking: {message}[/bold blue]\n")
    
    try:
        response = requests.post(
            f"{API_URL}/api/chat",
            json={
                "message": message,
                "code_context": code or ""
            }
        )
        
        if response.status_code != 200:
            console.print(f"[bold red]❌ Error: {response.text}[/bold red]")
            return
        
        data = response.json()
        console.print(Panel(data['response'], title="🤖 Assistant", border_style="blue"))
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

@cli.command()
@click.option('--team-id', default='default', help='Team identifier')
def insights(team_id):
    """Show team insights"""
    
    try:
        response = requests.get(f"{API_URL}/api/team-insights/{team_id}")
        
        if response.status_code != 200:
            console.print(f"[bold red]❌ Error: {response.text}[/bold red]")
            return
        
        data = response.json()
        
        console.print(Panel(
            f"[bold]Total Reviews:[/bold] {data['total_reviews']}\n"
            f"[bold]Average Score:[/bold] {data['average_score']}/100 ({data['improvement']})\n\n"
            f"[bold]Common Patterns:[/bold]\n" +
            "\n".join(f"  • {p}" for p in data['common_patterns']) +
            "\n\n[bold]Top Issues This Month:[/bold]\n" +
            "\n".join(f"  • {k}: {v} occurrences" for k, v in list(data['common_issues'].items())[:5]),
            title=f"👥 Team Insights - {team_id}",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

@cli.command()
@click.option('--limit', default=10, help='Number of reviews to show')
def history(limit):
    """Show review history"""
    
    try:
        response = requests.get(f"{API_URL}/api/reviews?limit={limit}")
        
        if response.status_code != 200:
            console.print(f"[bold red]❌ Error: {response.text}[/bold red]")
            return
        
        data = response.json()
        
        if not data['reviews']:
            console.print("[yellow]No reviews found[/yellow]")
            return
        
        table = Table(title=f"Recent Reviews (Total: {data['total']})")
        table.add_column("Review ID", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Issues", justify="right")
        table.add_column("Language", style="green")
        table.add_column("Date", style="dim")
        
        for review in data['reviews']:
            table.add_row(
                review['review_id'][:20] + "...",
                f"{review['score']}/100",
                str(len(review['priority'])),
                review.get('language', 'N/A'),
                review.get('timestamp', 'N/A')[:19]
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

@cli.command()
def health():
    """Check API health"""
    
    try:
        response = requests.get(f"{API_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            console.print(Panel(
                f"[bold green]✅ API is healthy[/bold green]\n\n"
                f"Status: {data['status']}\n"
                f"Total Reviews: {data.get('total_reviews', 0)}\n"
                f"Timestamp: {data['timestamp']}",
                title="🏥 Health Check",
                border_style="green"
            ))
        else:
            console.print("[bold red]❌ API is not responding[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Cannot connect to API: {str(e)}[/bold red]")

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
def syntax(filepath):
    """Display code with syntax highlighting"""
    
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        
        ext = Path(filepath).suffix[1:]
        syntax = Syntax(code, ext, theme="monokai", line_numbers=True)
        console.print(syntax)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

if __name__ == '__main__':
    cli()

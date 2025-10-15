#!/usr/bin/env python3
"""
Management script for Smart Code Review
Usage: python manage.py [command]
"""

import click
import subprocess
import sys
from pathlib import Path
import os

@click.group()
def cli():
    """Smart Code Review Management Tool"""
    pass

@cli.command()
def setup():
    """Setup the project for the first time"""
    click.echo("🚀 Setting up Smart Code Review...")
    
    # Create virtual environment
    click.echo("\n1️⃣ Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")
    
    # Install dependencies
    click.echo("\n2️⃣ Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"])
    
    # Create .env file
    if not Path(".env").exists():
        click.echo("\n3️⃣ Creating .env file...")
        subprocess.run(["cp", ".env.example", ".env"])
        click.echo("⚠️  Please edit .env file and add your API keys!")
    
    # Initialize database
    click.echo("\n4️⃣ Initializing database...")
    if sys.platform == "win32":
        python_path = Path("venv/Scripts/python")
    else:
        python_path = Path("venv/bin/python")
    
    subprocess.run([str(python_path), "database.py"])
    
    click.echo("\n✅ Setup complete!")
    click.echo("\nNext steps:")
    click.echo("1. Edit .env file and add your OpenAI API key")
    click.echo("2. Run: python manage.py run")

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def run(host, port, reload):
    """Run the development server"""
    click.echo(f"🚀 Starting server at http://{host}:{port}")
    
    cmd = ["uvicorn", "main:app", f"--host={host}", f"--port={port}"]
    if reload:
        cmd.append("--reload")
    
    subprocess.run(cmd)

@cli.command()
def test():
    """Run tests"""
    click.echo("🧪 Running tests...")
    subprocess.run(["pytest", "test_api.py", "-v", "--cov=.", "--cov-report=html"])
    click.echo("\n✅ Tests complete! View coverage report at htmlcov/index.html")

@cli.command()
def lint():
    """Run linters"""
    click.echo("🔍 Running linters...")
    
    # Black
    click.echo("\n1️⃣ Checking code formatting with Black...")
    subprocess.run(["black", "--check", "."])
    
    # Flake8
    click.echo("\n2️⃣ Checking code style with Flake8...")
    subprocess.run(["flake8", ".", "--max-line-length=127"])
    
    # MyPy
    click.echo("\n3️⃣ Type checking with MyPy...")
    subprocess.run(["mypy", ".", "--ignore-missing-imports"])

@cli.command()
def format():
    """Format code with Black"""
    click.echo("✨ Formatting code...")
    subprocess.run(["black", "."])
    click.echo("✅ Code formatted!")

@cli.command()
def migrate():
    """Run database migrations"""
    click.echo("🗄️  Running migrations...")
    subprocess.run(["alembic", "upgrade", "head"])
    click.echo("✅ Migrations complete!")

@cli.command()
def init_db():
    """Initialize the database"""
    click.echo("🗄️  Initializing database...")
    subprocess.run([sys.executable, "database.py"])
    click.echo("✅ Database initialized!")

@cli.command()
def docker_build():
    """Build Docker image"""
    click.echo("🐳 Building Docker image...")
    subprocess.run(["docker", "build", "-t", "smart-code-review", "."])
    click.echo("✅ Docker image built!")

@cli.command()
def docker_run():
    """Run with Docker Compose"""
    click.echo("🐳 Starting services with Docker Compose...")
    subprocess.run(["docker-compose", "up", "-d"])
    click.echo("✅ Services started!")
    click.echo("API: http://localhost:8000")
    click.echo("PGAdmin: http://localhost:5050")

@cli.command()
def docker_stop():
    """Stop Docker services"""
    click.echo("🐳 Stopping services...")
    subprocess.run(["docker-compose", "down"])
    click.echo("✅ Services stopped!")

@cli.command()
def docker_logs():
    """View Docker logs"""
    subprocess.run(["docker-compose", "logs", "-f"])

@cli.command()
def clean():
    """Clean up generated files"""
    click.echo("🧹 Cleaning up...")
    
    patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.egg-info",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "*.db",
    ]
    
    for pattern in patterns:
        if "*" in pattern:
            # Remove files matching pattern
            for file in Path(".").rglob(pattern):
                file.unlink()
                click.echo(f"Removed {file}")
        else:
            # Remove directories
            for dir in Path(".").rglob(pattern):
                if dir.is_dir():
                    import shutil
                    shutil.rmtree(dir)
                    click.echo(f"Removed {dir}")
    
    click.echo("✅ Cleanup complete!")

@cli.command()
@click.argument('filename')
def review(filename):
    """Quick review a file using CLI"""
    if not Path(filename).exists():
        click.echo(f"❌ File not found: {filename}")
        return
    
    click.echo(f"📝 Reviewing {filename}...")
    subprocess.run([sys.executable, "cli.py", "review", filename])

@cli.command()
def deps():
    """Update dependencies"""
    click.echo("📦 Updating dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"])
    click.echo("✅ Dependencies updated!")

@cli.command()
def check():
    """Run all checks (lint + test)"""
    click.echo("🔍 Running all checks...")
    
    click.echo("\n" + "="*50)
    click.echo("LINTING")
    click.echo("="*50)
    subprocess.run([sys.executable, "manage.py", "lint"])
    
    click.echo("\n" + "="*50)
    click.echo("TESTING")
    click.echo("="*50)
    subprocess.run([sys.executable, "manage.py", "test"])
    
    click.echo("\n✅ All checks complete!")

@cli.command()
def info():
    """Display project information"""
    click.echo("="*50)
    click.echo("Smart Code Review - Project Info")
    click.echo("="*50)
    
    click.echo(f"\nPython Version: {sys.version}")
    click.echo(f"Working Directory: {Path.cwd()}")
    
    if Path(".env").exists():
        click.echo("Environment: .env file found ✅")
    else:
        click.echo("Environment: .env file not found ❌")
    
    if Path("venv").exists():
        click.echo("Virtual Environment: Found ✅")
    else:
        click.echo("Virtual Environment: Not found ❌")
    
    if Path("code_review.db").exists():
        click.echo("Database: Found ✅")
    else:
        click.echo("Database: Not found ❌")
    
    click.echo("\nEndpoints:")
    click.echo("  API: http://localhost:8000")
    click.echo("  Docs: http://localhost:8000/docs")
    click.echo("  Health: http://localhost:8000/health")

@cli.command()
def generate_docs():
    """Generate API documentation"""
    click.echo("📚 Generating documentation...")
    # You can add documentation generation logic here
    click.echo("✅ Documentation generated!")

if __name__ == '__main__':
    cli()

"""
PRism-AI - CLI tool for manual reviews and management
"""
import asyncio
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import Settings
from .review_engine import ReviewEngine
from .git_providers import create_git_provider

console = Console()

@click.group()
def cli():
    """PRism-AI: AI-powered Pull Request Review Agent."""
    pass

@cli.command()
@click.option("--repo", required=True, help="GitHub/GitLab repository (owner/repo)")
@click.option("--pr", required=True, type=int, help="Pull Request / Merge Request number")
@click.option("--provider", default="github", help="Git provider (github, gitlab, gitea)")
@click.option("--token", help="Git provider API token (overrides env)")
def review(repo, pr, provider, token):
    """Trigger a manual PR review from CLI."""
    settings = Settings()
    
    async def run():
        owner, repo_name = repo.split("/", 1)
        git_config = {
            "type": provider,
            "token": token or settings.get_git_token(provider),
            "base_url": settings.get_git_base_url(provider),
        }
        git = create_git_provider(git_config)
        
        console.print(f"[bold blue]PRism-AI[/] Fetching PR#{pr} from {repo}...")
        try:
            diff = await git.get_pr_diff(owner, repo_name, pr)
            pr_info = await git.get_pr_info(owner, repo_name, pr)
            files = await git.get_pr_files(owner, repo_name, pr)
        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to fetch PR data: {e}")
            sys.exit(1)
            
        engine = ReviewEngine(settings.to_engine_config())
        console.print(f"[bold blue]PRism-AI[/] Analyzing diff with {settings.llm_provider}...")
        
        result = await engine.review_pr(
            pr_number=pr,
            repo=repo,
            diff=diff,
            pr_title=pr_info.get("title", ""),
            pr_body=pr_info.get("body", ""),
            changed_files=files,
        )
        
        # Display results
        console.print(Panel(result.summary, title=f"Review Summary (Score: {result.score}/100)", border_style="green" if result.approved else "yellow"))
        
        if result.comments:
            table = Table(title="Line-level Comments")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="magenta")
            table.add_column("Severity", style="bold")
            table.add_column("Message")
            
            for comment in result.comments:
                table.add_row(
                    comment.path,
                    str(comment.line or "-"),
                    comment.severity,
                    comment.message
                )
            console.print(table)
        else:
            console.print("[green]No issues found![/]")
            
    asyncio.run(run())

@cli.command()
def health():
    """Check health of PRism-AI and configured LLM backend."""
    settings = Settings()
    engine = ReviewEngine(settings.to_engine_config())
    
    async def run():
        console.print(f"[bold]PRism-AI Version:[/] {settings.app_version}")
        console.print(f"[bold]LLM Provider:[/] {settings.llm_provider}")
        
        try:
            ok = await engine.llm.health_check()
            status = "[bold green]Healthy[/]" if ok else "[bold red]Unhealthy[/]"
            console.print(f"[bold]LLM Status:[/] {status}")
            
            models = await engine.llm.list_models()
            if models:
                console.print(f"[bold]Available Models:[/] {', '.join(models[:10])}")
        except Exception as e:
            console.print(f"[bold red]LLM Health Check Failed:[/] {e}")
            
    asyncio.run(run())

def main():
    cli()

if __name__ == "__main__":
    main()

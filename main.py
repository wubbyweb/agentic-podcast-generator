#!/usr/bin/env python3
"""
Agentic System CLI Entry Point
Handles user input and initiates the Master Agent workflow
"""

# Load environment variables from .env file before importing config
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
import logging
from typing import Optional

import click

from agents.master_agent import MasterAgent
from config.settings import config
from database.connection import init_database
from services.logger import setup_logging

@click.command()
@click.argument('topic', required=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--session-id', type=int, help='Resume existing session')
@click.option('--output-format', type=click.Choice(['json', 'text']), default='text',
              help='Output format for results')
def main(
    topic: str,
    verbose: bool,
    session_id: Optional[int],
    output_format: str
):
    """Process a topic through the agentic system pipeline.

    TOPIC: The topic to process through the agent system
    """
    asyncio.run(async_main(topic, verbose, session_id, output_format))


async def async_main(
    topic: str,
    verbose: bool,
    session_id: Optional[int],
    output_format: str
):
    try:
        # Validate configuration
        config.validate_config()

        # Setup logging
        log_level = "DEBUG" if verbose else config.log_level
        setup_logging(level=log_level)

        logger = logging.getLogger(__name__)
        logger.info("Starting Agentic System...")

        # Initialize database
        await init_database()
        logger.info("Database initialized")

        # Create and run Master Agent
        async with MasterAgent() as master:
            logger.info(f"Processing topic: {topic}")

            if session_id:
                logger.info(f"Resuming session: {session_id}")

            result = await master.process_topic(topic, session_id=session_id)

            # Output results
            if output_format == 'json':
                import json
                click.echo(json.dumps(result, indent=2))
            else:
                display_results(result)

            logger.info(f"Processing complete. Session ID: {result['session_id']}")

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Application error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def display_results(result: dict) -> None:
    """Display results in a user-friendly format."""

    click.echo("\n" + "="*60)
    click.echo("🤖 AGENTIC SYSTEM RESULTS")
    click.echo("="*60)

    click.echo(f"\n📋 Session ID: {result['session_id']}")
    click.echo(f"📝 Topic: {result['topic']}")

    if 'analysis' in result:
        click.echo("\n🔍 Topic Analysis:")
        analysis = result['analysis']
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                click.echo(f"  • {key.title()}: {value}")

    if 'keywords' in result and result['keywords']:
        click.echo("\n🏷️ Keywords:")
        for keyword in result['keywords'][:10]:  # Show first 10
            click.echo(f"  • {keyword}")

    if 'hashtags' in result and result['hashtags']:
        click.echo("\n#️⃣ Hashtags:")
        hashtags_str = " ".join(result['hashtags'][:10])  # Show first 10
        click.echo(f"  {hashtags_str}")

    if 'linkedin_post' in result:
        click.echo("\n💼 LinkedIn Post:")
        click.echo("-" * 40)
        click.echo(result['linkedin_post'])
        click.echo("-" * 40)

    if 'voice_dialog' in result:
        click.echo("\n🎙️ Voice Dialog Script:")
        click.echo("-" * 40)
        click.echo(result['voice_dialog'])
        click.echo("-" * 40)

    if 'research_summary' in result:
        click.echo("\n📚 Research Summary:")
        click.echo(result['research_summary'])

    click.echo("\n" + "="*60)
    click.echo("✅ Processing Complete!")
    click.echo("="*60)

if __name__ == "__main__":
    main()
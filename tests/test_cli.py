"""Tests for the skillsmd CLI."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from skillsmd.cli import app, __version__


runner = CliRunner()


class TestHelpCommand:
    """Test --help command output."""

    def test_should_display_help_message(self):
        """Help message should contain usage information."""
        result = runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.stdout
        assert 'Commands' in result.stdout
        assert 'add' in result.stdout
        assert 'list' in result.stdout
        assert 'init' in result.stdout
        assert 'find' in result.stdout
        assert 'check' in result.stdout
        assert 'update' in result.stdout
        assert 'remove' in result.stdout


class TestVersionCommand:
    """Test --version command output."""

    def test_should_display_version_number(self):
        """Version command should display the version."""
        result = runner.invoke(app, ['--version'])
        assert result.exit_code == 0
        # Version should be in format x.y.z
        assert re.match(r'^\d+\.\d+\.\d+\n?$', result.stdout.strip())

    def test_should_match_version_constant(self):
        """Version output should match __version__."""
        result = runner.invoke(app, ['--version'])
        assert __version__ in result.stdout

    def test_v_short_alias(self):
        """Version should be same for -v and --version."""
        version_output = runner.invoke(app, ['--version'])
        v_output = runner.invoke(app, ['-v'])
        assert version_output.stdout == v_output.stdout


class TestNoArguments:
    """Test CLI behavior with no arguments."""

    def test_should_display_banner(self):
        """With no arguments, should display the banner."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert 'The open agent skills ecosystem' in result.stdout
        assert 'add' in result.stdout.lower()
        assert 'list' in result.stdout.lower()
        assert 'find' in result.stdout.lower()
        assert 'check' in result.stdout.lower()
        assert 'update' in result.stdout.lower()


class TestUnknownCommand:
    """Test CLI behavior with unknown commands."""

    def test_should_show_error_for_unknown_command(self):
        """Unknown command should show error message."""
        result = runner.invoke(app, ['unknown-command'])
        assert result.exit_code != 0
        assert 'No such command' in result.stderr or 'Usage:' in result.stderr


class TestLogoDisplay:
    """Test logo display behavior."""

    def test_should_not_display_logo_for_list_command(self):
        """List command should not display logo."""
        result = runner.invoke(app, ['list'])
        # Logo contains box drawing characters or ASCII art - check it's not there
        assert '███████' not in result.stdout  # Unicode logo marker
        assert '/ ___/' not in result.stdout  # ASCII logo marker

    def test_should_not_display_logo_for_check_command(self):
        """Check command should not display logo."""
        result = runner.invoke(app, ['check'])
        assert '███████' not in result.stdout
        assert '/ ___/' not in result.stdout

    def test_should_not_display_logo_for_update_command(self):
        """Update command should not display logo."""
        result = runner.invoke(app, ['update'])
        assert '███████' not in result.stdout
        assert '/ ___/' not in result.stdout

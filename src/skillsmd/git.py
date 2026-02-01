"""Git operations for the skillsmd CLI."""

import shutil
import tempfile
from pathlib import Path

from git import Repo
from git.exc import GitCommandError

CLONE_TIMEOUT_S = 60


class GitCloneError(Exception):
    """Exception raised when git clone fails."""

    def __init__(
        self,
        message: str,
        url: str,
        is_timeout: bool = False,
        is_auth_error: bool = False,
    ):
        super().__init__(message)
        self.url = url
        self.is_timeout = is_timeout
        self.is_auth_error = is_auth_error


async def clone_repo(url: str, ref: str | None = None) -> str:
    """
    Clone a git repository to a temporary directory.

    Args:
        url: The git URL to clone
        ref: Optional branch/tag to checkout

    Returns:
        Path to the temporary directory containing the clone

    Raises:
        GitCloneError: If cloning fails
    """
    temp_dir = tempfile.mkdtemp(prefix='skills-')

    try:
        # Build clone arguments
        clone_kwargs = {
            'depth': 1,
        }
        if ref:
            clone_kwargs['branch'] = ref

        # Clone the repository
        Repo.clone_from(url, temp_dir, **clone_kwargs)
        return temp_dir

    except GitCommandError as e:
        # Clean up temp dir on failure
        shutil.rmtree(temp_dir, ignore_errors=True)

        error_message = str(e)
        is_timeout = 'timed out' in error_message.lower()
        is_auth_error = any(
            msg in error_message
            for msg in [
                'Authentication failed',
                'could not read Username',
                'Permission denied',
                'Repository not found',
            ]
        )

        if is_timeout:
            raise GitCloneError(
                f'Clone timed out after {CLONE_TIMEOUT_S}s. This often happens with private repos that require authentication.\n'
                '  Ensure you have access and your SSH keys or credentials are configured:\n'
                '  - For SSH: ssh-add -l (to check loaded keys)\n'
                '  - For HTTPS: gh auth status (if using GitHub CLI)',
                url,
                is_timeout=True,
            ) from e

        if is_auth_error:
            raise GitCloneError(
                f'Authentication failed for {url}.\n'
                '  - For private repos, ensure you have access\n'
                "  - For SSH: Check your keys with 'ssh -T git@github.com'\n"
                "  - For HTTPS: Run 'gh auth login' or configure git credentials",
                url,
                is_auth_error=True,
            ) from e

        raise GitCloneError(
            f'Failed to clone {url}: {error_message}',
            url,
        ) from e

    except Exception as e:
        # Clean up temp dir on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise GitCloneError(
            f'Failed to clone {url}: {e}',
            url,
        ) from e


async def cleanup_temp_dir(dir_path: str) -> None:
    """
    Safely clean up a temporary directory.

    Validates that the path is within the system temp directory to prevent
    deletion of arbitrary paths.
    """
    temp_base = Path(tempfile.gettempdir()).resolve()
    target = Path(dir_path).resolve()

    # Validate the path is within temp directory
    try:
        target.relative_to(temp_base)
    except ValueError:
        raise ValueError('Attempted to clean up directory outside of temp directory')

    shutil.rmtree(dir_path, ignore_errors=True)

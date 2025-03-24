"""
Shell command execution utilities for Typer/Rich applications.

This module provides functions to execute shell commands with rich formatting 
and visual feedback using the Rich library. It handles command execution, 
output capturing, and error reporting in a user-friendly way.

Key features:
- Rich output formatting with syntax highlighting
- Real-time execution feedback with spinners
- Structured command results with exit codes and output
- Support for executing multiple commands sequentially
- Integration with Typer CLI applications

Functions:
    execute: Run a single shell command with rich output
    execute_multiple: Run multiple shell commands in sequence
    create_typer_app: Create a Typer application with shell execution commands

Example:
    ```python
    from shell_executor import execute
    
    # Run a simple command
    result = execute("ls -la")
    
    # Check if successful
    if result.success:
        print(f"Command succeeded with output: {result.stdout}")
    else:
        print(f"Command failed with error: {result.stderr}")
    ```
"""
import subprocess
import shlex
from typing import List, Dict, Optional, Union, Tuple, Any, NamedTuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn

class CommandResult(NamedTuple):
    """Class to store the result of a command execution."""
    command: str
    return_code: int
    stdout: str
    stderr: str
    success: bool
    
    def __str__(self) -> str:
        """String representation of the command result."""
        return f"Command: {self.command}\nSuccess: {self.success}\nReturn Code: {self.return_code}"
    
    def __bool__(self) -> bool:
        """Boolean representation of the command result."""
        return self.success


def execute(command: str, 
            env: Optional[Dict[str, str]] = None,
            cwd: Optional[str] = None,
            shell: bool = False,
            timeout: Optional[int] = None,
            quiet: bool = False,
            console: Optional[Console] = None,
            show_commands: bool = True,
            show_output: bool = True,
            show_errors: bool = True,
            capture_output: bool = True) -> CommandResult:
    """
    Execute a shell command and return the result.
    
    Args:
        command: The command to execute.
        env: Environment variables to set for the command.
        cwd: Working directory for the command.
        shell: Whether to execute the command in a shell.
        timeout: Timeout for the command in seconds.
        quiet: Whether to suppress all output.
        show_commands: Whether to display commands before execution.
        show_output: Whether to display command output after execution.
        show_errors: Whether to display command errors after execution.
        capture_output: Whether to capture command output or stream it directly.
        spinner_style: Style to use for the spinner when executing commands.
        
    Returns:
        CommandResult: The result of the command execution.
    """
    console = console
    
    if show_commands and not quiet:
        cmd_syntax = Syntax(command, "bash", theme="monokai", word_wrap=True)
        console.print(Panel(cmd_syntax, title="Executing Command", border_style="command"))
    
    if not shell:
        command_list = shlex.split(command)
    else:
        command_list = command
    
    try:
        if capture_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                if not quiet:
                    task = progress.add_task(description="Running command...", total=None)
                
                process = subprocess.run(
                    command_list,
                    env=env,
                    cwd=cwd,
                    shell=shell,
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                
                if not quiet:
                    progress.update(task, completed=True, description="Command completed")
        else:
            process = subprocess.run(
                command_list,
                env=env,
                cwd=cwd,
                shell=shell,
                timeout=timeout
            )
            stdout = ""
            stderr = ""
    
        if capture_output:
            stdout = process.stdout
            stderr = process.stderr
        
        success = process.returncode == 0
        
        if show_output and stdout and not quiet and capture_output:
            out_syntax = Syntax(stdout, "text", theme="monokai", word_wrap=True)
            console.print(Panel(out_syntax, title="Command Output", border_style="success" if success else "info"))
        
        if show_errors and stderr and not quiet and capture_output:
            err_syntax = Syntax(stderr, "text", theme="monokai", word_wrap=True)
            console.print(Panel(err_syntax, title="Command Errors", border_style="error"))
        
        return CommandResult(
            command=command,
            return_code=process.returncode,
            stdout=stdout if capture_output else "",
            stderr=stderr if capture_output else "",
            success=success
        )
        
    except subprocess.TimeoutExpired:
        if not quiet:
            console.print(f"[error]Command timed out after {timeout} seconds[/error]")
        return CommandResult(
            command=command,
            return_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False
        )
        
    except Exception as e:
        if not quiet:
            console.print(f"[error]Error executing command: {str(e)}[/error]")
        return CommandResult(
            command=command,
            return_code=-1,
            stdout="",
            stderr=str(e),
            success=False
        )


def execute_multiple(commands: List[str], 
                     env: Optional[Dict[str, str]] = None,
                     cwd: Optional[str] = None,
                     shell: bool = False,
                     timeout: Optional[int] = None,
                     stop_on_error: bool = True,
                     quiet: bool = False,
                     console: Optional[Console] = None,
                     show_commands: bool = True,
                     show_output: bool = True,
                     show_errors: bool = True,
                     capture_output: bool = True) -> List[CommandResult]:
    """
    Execute multiple commands in sequence.
    
    Args:
        commands: List of commands to execute.
        env: Environment variables to set for the commands.
        cwd: Working directory for the commands.
        shell: Whether to execute the commands in a shell.
        timeout: Timeout for each command in seconds.
        stop_on_error: Whether to stop execution if a command fails.
        quiet: Whether to suppress all output.
        console: Rich console to use for output. If None, the default console is used.
        show_commands: Whether to display commands before execution.
        show_output: Whether to display command output after execution.
        show_errors: Whether to display command errors after execution.
        capture_output: Whether to capture command output or stream it directly.
        spinner_style: Style to use for the spinner when executing commands.
        
    Returns:
        List[CommandResult]: The results of the command executions.
    """
    console = console
    results = []
    
    for cmd in commands:
        result = execute(
            cmd, env, cwd, shell, timeout, quiet, console,
            show_commands, show_output, show_errors, capture_output
        )
        results.append(result)
        
        if stop_on_error and not result.success:
            if not quiet:
                console.print(f"[error]Stopping execution due to command failure[/error]")
            break
            
    return results

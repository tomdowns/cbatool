"""
Error handling utilities for CBAtool v2.0.

This module contains utilities for error handling, including custom exception
classes and error handling decorators.
"""

import traceback
import logging
import functools
from typing import Callable, Any, Optional, Type, Dict, List, Union

# Configure logging
logger = logging.getLogger(__name__)


class CBAError(Exception):
    """Base exception class for all CBAtool custom exceptions."""
    pass


class FileError(CBAError):
    """Exception raised for file-related errors."""
    def __init__(self, message: str, file_path: Optional[str] = None):
        self.file_path = file_path
        self.message = f"File error: {message}"
        if file_path:
            self.message += f" (file: {file_path})"
        super().__init__(self.message)


class DataError(CBAError):
    """Exception raised for data-related errors."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.details = details or {}
        self.message = f"Data error: {message}"
        super().__init__(self.message)


class AnalysisError(CBAError):
    """Exception raised for analysis-related errors."""
    def __init__(self, message: str, analysis_step: Optional[str] = None):
        self.analysis_step = analysis_step
        self.message = f"Analysis error: {message}"
        if analysis_step:
            self.message += f" (step: {analysis_step})"
        super().__init__(self.message)


class VisualizationError(CBAError):
    """Exception raised for visualization-related errors."""
    def __init__(self, message: str, viz_type: Optional[str] = None):
        self.viz_type = viz_type
        self.message = f"Visualization error: {message}"
        if viz_type:
            self.message += f" (type: {viz_type})"
        super().__init__(self.message)


def exception_handler(
    func: Optional[Callable] = None,
    reraise: bool = False,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    error_type: Optional[Type[Exception]] = None
) -> Callable:
    """
    Decorator for handling exceptions in functions.
    
    Args:
        func: The function to decorate.
        reraise: Whether to re-raise the exception after handling.
        default_return: Value to return if an exception occurs.
        log_level: Logging level for the exception message.
        error_type: Specific type of exception to catch.
        
    Returns:
        Decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get exception details
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_traceback = traceback.format_exc()
                
                # Log the exception
                log_msg = f"{exc_type} in {func.__name__}: {exc_msg}"
                logger.log(log_level, log_msg)
                
                # Log traceback at debug level
                logger.debug(exc_traceback)
                
                # Reraise if requested
                if reraise:
                    raise
                
                # Otherwise return default value
                return default_return
        return wrapper
    
    # Handle case where decorator is used with or without arguments
    if func is None:
        return decorator
    return decorator(func)


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution.
    
    Args:
        func: The function to decorate.
        
    Returns:
        Decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Executing {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Completed {func.__name__}")
        return result
    return wrapper


def validate_input(
    validators: Dict[str, Callable[[Any], bool]],
    error_messages: Optional[Dict[str, str]] = None
) -> Callable:
    """
    Decorator to validate function inputs.
    
    Args:
        validators: Dictionary mapping argument names to validator functions.
        error_messages: Optional dictionary mapping argument names to error messages.
        
    Returns:
        Decorated function.
    """
    error_messages = error_messages or {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function argument names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    arg_value = bound_args.arguments[arg_name]
                    if not validator(arg_value):
                        error_msg = error_messages.get(
                            arg_name, 
                            f"Invalid value for '{arg_name}': {arg_value}"
                        )
                        raise ValueError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_file_errors(func: Callable) -> Callable:
    """
    Decorator specifically for handling file-related errors.
    
    Args:
        func: The function to decorate.
        
    Returns:
        Decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            file_path = str(e).split("'")[1] if "'" in str(e) else None
            raise FileError(f"File not found: {str(e)}", file_path)
        except PermissionError as e:
            file_path = str(e).split("'")[1] if "'" in str(e) else None
            raise FileError(f"Permission denied: {str(e)}", file_path)
        except IsADirectoryError as e:
            file_path = str(e).split("'")[1] if "'" in str(e) else None
            raise FileError(f"Expected a file, got a directory: {str(e)}", file_path)
        except IOError as e:
            file_path = getattr(e, "filename", None)
            raise FileError(f"I/O error: {str(e)}", file_path)
    return wrapper

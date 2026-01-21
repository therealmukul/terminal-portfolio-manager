"""Stock Analysis Agent - A terminal-based stock analysis tool."""

__version__ = "0.1.0"

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("terminal-portfolio-manager")
    except PackageNotFoundError:
        pass
except ImportError:
    pass

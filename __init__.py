"""
Playwright Tools Package

This package contains all the Playwright browser automation tools for the AI Browser Agent.
The tools are organized into different modules for better maintainability.
"""

# Import the main tools class
from .playwright_advanced_newtools import PlaywrightAdvancedTools

# Import additional tools from logs directory if available
try:
    import sys
    import os
    logs_path = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if os.path.exists(logs_path):
        sys.path.insert(0, logs_path)
        from playwright_advanced_newtools import PlaywrightAdvancedTools as LogsPlaywrightTools
        sys.path.remove(logs_path)
        
        # Create a combined tools class that includes both sets of tools
        class CombinedPlaywrightTools(PlaywrightAdvancedTools):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Initialize the logs tools instance
                self.logs_tools = LogsPlaywrightTools(*args, **kwargs)
                
                # Copy methods from logs tools that don't exist in main tools
                for attr_name in dir(self.logs_tools):
                    if (attr_name.startswith('playwright_') and 
                        not attr_name.startswith('playwright__') and
                        not hasattr(self, attr_name)):
                        setattr(self, attr_name, getattr(self.logs_tools, attr_name))
        
        # Use the combined class
        PlaywrightTools = CombinedPlaywrightTools
        print("🔧 Combined tools from main and logs directories")
    else:
        # Fallback to main tools only
        PlaywrightTools = PlaywrightAdvancedTools
        print("📁 Using main tools only (logs directory not found)")
        
except Exception as e:
    print(f"⚠️ Could not import additional tools from logs: {e}")
    # Create an alias for backward compatibility with AI_Browser_agent.py
    # The agent expects a class called 'PlaywrightTools'
    PlaywrightTools = PlaywrightAdvancedTools

# Import any other tool classes or functions from other modules
try:
    from .proactive_cookie_learning import ProactiveCookieLearning
except (ImportError, SyntaxError):
    # Handle both import errors and syntax errors in the module
    ProactiveCookieLearning = None

# Make the main classes available at package level
__all__ = [
    'PlaywrightTools',
    'PlaywrightAdvancedTools', 
    'ProactiveCookieLearning'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'AI Browser Agent'
__description__ = 'Comprehensive Playwright browser automation tools'

# Tool discovery helper for the AI agent
def get_available_tools():
    """
    Return a list of all available playwright tools.
    This helps the AI agent discover all available tools.
    """
    tools = []
    
    # Get all methods from PlaywrightAdvancedTools that start with 'playwright_'
    import inspect
    for name, method in inspect.getmembers(PlaywrightAdvancedTools, predicate=inspect.isfunction):
        if name.startswith('playwright_'):
            tools.append(name)
    
    return tools

def get_tool_descriptions():
    """
    Return a dictionary of tool names and their descriptions.
    """
    descriptions = {}
    
    import inspect
    for name, method in inspect.getmembers(PlaywrightAdvancedTools, predicate=inspect.isfunction):
        if name.startswith('playwright_'):
            doc = inspect.getdoc(method)
            descriptions[name] = doc.split('\n')[0] if doc else f"Playwright tool: {name}"
    
    return descriptions

# Initialize logging for the package
import logging
logger = logging.getLogger(__name__)
logger.info(f"Playwright Tools package loaded with {len(get_available_tools())} tools")

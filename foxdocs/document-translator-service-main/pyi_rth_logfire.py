# PyInstaller runtime hook for logfire and torch
# Disables source code inspection in frozen apps

import sys
import os

# Set environment variables to disable various inspections
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'
os.environ['PYTORCH_JIT'] = '0'  # Disable PyTorch JIT compilation
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Monkey-patch inspect module to prevent errors
if getattr(sys, 'frozen', False):
    import inspect
    _original_getsource = inspect.getsource
    _original_getsourcelines = inspect.getsourcelines
    _original_getsourcefile = inspect.getsourcefile
    
    def _dummy_getsource(obj):
        """Return empty source for frozen apps"""
        return ""
    
    def _dummy_getsourcelines(obj):
        """Return empty source lines for frozen apps"""
        return ([], 0)
    
    def _dummy_getsourcefile(obj):
        """Return None for frozen apps"""
        return None
    
    inspect.getsource = _dummy_getsource
    inspect.getsourcelines = _dummy_getsourcelines
    inspect.getsourcefile = _dummy_getsourcefile
    
    # Patch torch._sources if it gets imported
    _original_import = __builtins__.__import__
    
    def _patched_import(name, *args, **kwargs):
        module = _original_import(name, *args, **kwargs)
        
        # Patch torch._sources.parse_def to prevent source parsing
        if name == 'torch._sources' or (hasattr(module, '__name__') and module.__name__ == 'torch._sources'):
            if hasattr(module, 'parse_def'):
                def _dummy_parse_def(*args, **kwargs):
                    # Return a minimal AST that won't cause errors
                    import ast
                    return ast.parse("def dummy(): pass").body[0]
                module.parse_def = _dummy_parse_def
        
        # Patch torch._jit_internal to disable overload checking
        if name == 'torch._jit_internal' or (hasattr(module, '__name__') and module.__name__ == 'torch._jit_internal'):
            if hasattr(module, '_check_overload_body'):
                def _dummy_check_overload_body(*args, **kwargs):
                    pass  # Do nothing
                module._check_overload_body = _dummy_check_overload_body
        
        return module
    
    __builtins__.__import__ = _patched_import


"""
PyInstaller runtime hook for PaddleX dependency checks.

This hook patches PaddleX's dependency checking mechanism to work in PyInstaller bundles.
PaddleX checks for package metadata which PyInstaller doesn't include by default.

CRITICAL: This must run BEFORE paddlex is imported by the application.
"""

import sys

# Only patch when running from PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print("[PyInstaller-Hook] Initializing PaddleX patch...")
    
    try:
        # Import and patch paddlex.utils.deps IMMEDIATELY
        # This ensures the patch is in place before any OCR code runs
        import paddlex.utils.deps
        
        # Store original functions for debugging
        _original_require_extra = paddlex.utils.deps.require_extra
        _original_require_deps = paddlex.utils.deps.require_deps
        
        def patched_require_extra(extra, obj_name=None, alt=None):
            """
            Patched version of require_extra that skips dependency checks.
            
            In PyInstaller, all dependencies are already bundled into the EXE.
            The metadata files (.dist-info) might not be available, but the actual
            modules are present. This function short-circuits the check.
            
            Args:
                extra: Extra dependency group (e.g., 'ocr', 'det', etc.)
                obj_name: Name of the object requiring the dependency
                alt: Alternative package name
            
            Returns:
                None (always succeeds)
            """
            # In frozen environment, skip all dependency checks
            # If a module is truly missing, we'll get ImportError later
            print(f"[PyInstaller-Hook] Skipping extra check: {extra} (obj: {obj_name})")
            return
        
        def patched_require_deps(*deps, obj_name=None):
            """
            Patched version of require_deps that skips dependency checks.
            
            This function checks for specific package dependencies like pypdfium2,
            opencv-contrib-python, etc. In PyInstaller, these are already bundled,
            so we skip the check.
            
            Args:
                *deps: List of dependency names to check
                obj_name: Name of the object requiring the dependencies
            
            Returns:
                None (always succeeds)
            """
            # In frozen environment, skip all dependency checks
            deps_str = ', '.join(deps) if deps else 'none'
            print(f"[PyInstaller-Hook] Skipping deps check: [{deps_str}] (obj: {obj_name})")
            return
        
        # Replace both functions
        paddlex.utils.deps.require_extra = patched_require_extra
        paddlex.utils.deps.require_deps = patched_require_deps
        
        print("[PyInstaller-Hook] ✅ PaddleX dependency checks successfully disabled")
        print("[PyInstaller-Hook] ✅ Patched: require_extra() and require_deps()")
        print("[PyInstaller-Hook] All dependencies are assumed to be bundled in the EXE")
        
    except ImportError as e:
        print(f"[PyInstaller-Hook] ⚠️ Could not import paddlex.utils.deps: {e}")
        print("[PyInstaller-Hook] This is OK if paddlex will be imported later")
    except Exception as e:
        print(f"[PyInstaller-Hook] ❌ Error patching PaddleX: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[PyInstaller-Hook] Not in frozen mode, skipping PaddleX patch")


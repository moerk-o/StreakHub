"""Debug test to check Python path and import."""

import os
import sys


def test_debug_paths():
    """Debug Python path and imports."""
    print("\n=== DEBUG INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"__file__ path: {__file__}")
    print(f"tests directory: {os.path.dirname(__file__)}")
    print(f"project root: {os.path.dirname(os.path.dirname(__file__))}")

    print("\nPython path:")
    for i, p in enumerate(sys.path[:10]):
        print(f"  [{i}] {p}")

    tests_dir = os.path.dirname(__file__)
    custom_components_path = os.path.join(tests_dir, "custom_components")
    streakhub_path = os.path.join(custom_components_path, "streakhub")

    print("\n=== FILE CHECKS ===")
    print(f"tests/custom_components exists: {os.path.exists(custom_components_path)}")
    print(f"tests/custom_components/streakhub exists: {os.path.exists(streakhub_path)}")
    print(
        f"streakhub/__init__.py exists: {os.path.exists(os.path.join(streakhub_path, '__init__.py'))}"
    )

    # List files in custom_components
    if os.path.exists(custom_components_path):
        print(f"Files in custom_components: {os.listdir(custom_components_path)}")

    # List files in streakhub
    if os.path.exists(streakhub_path):
        files = os.listdir(streakhub_path)[:10]
        print(f"Files in streakhub: {files}")

    # Try import
    print("\n=== IMPORT TEST ===")
    try:
        import custom_components

        print("✅ custom_components imported")
        print(f"custom_components.__file__: {custom_components.__file__}")
        print(f"custom_components.__path__: {getattr(custom_components, '__path__', 'N/A')}")
    except Exception as e:
        print(f"❌ custom_components import failed: {e}")

    try:
        import custom_components.streakhub

        print("✅ custom_components.streakhub imported")
    except Exception as e:
        print(f"❌ custom_components.streakhub import failed: {e}")

    assert True

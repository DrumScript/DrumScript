#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting the DrumScript build and publish process..."

# Step 1: Clean old build directories to prevent uploading old versions
echo "Cleaning dist/ and build/ directories..."
rm -rf dist/ build/

# Step 2: Build the package using uv and log the output
echo "Building the package..."
mkdir -p scripts/logs/wheel
uv build | tee -a scripts/logs/wheel/build.log

# Step 3: Check the distribution files with twine
echo "Running twine check on distribution files..."
uv run twine check dist/*

# Step 4: Publish to TestPyPI (Commented out by default. Remove the '#' to use this step)
# echo "Publishing to TestPyPI..."
# mkdir -p scripts/logs/drumscript-pypitest
# uv run twine upload --repository testpypi dist/* | tee -a scripts/logs/drumscript-pypitest/pypitest.log

# Step 5: Publish to the main PyPI repository and log the output
echo "Publishing to PyPI..."
mkdir -p scripts/logs/drumscript-pypi
uv run twine upload dist/* | tee -a scripts/logs/drumscript-pypi/pypi.log

echo "DrumScript release process complete!"
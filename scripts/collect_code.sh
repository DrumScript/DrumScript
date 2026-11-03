#!/bin/bash
# ensure running ` chmod +x collect_code.sh` to initiatise
# use `./collect_code.sh` to run
# Define the output file name
# Configuration

# OUTPUT_FILE="drumscript_production_review.txt"
OUTPUT_FILE="drumscript_full_review.txt"
# OUTPUT_FILE="drumscript_audit_$(date +%Y%m%d).txt"
TARGET_DIR="drumscript"
PYPROJECT="pyproject.toml"

# Reset/Create Output File
: > "$OUTPUT_FILE"   # `:` is a no-op; a bare `>` trips shellcheck SC2188

echo "----------------------------------------------------------"
echo "Starting Audit: $(date)"
echo "Target: $TARGET_DIR"
echo "----------------------------------------------------------"

# 1. METADATA SECTION (pyproject.toml)
{
    echo "================================================================================"
    echo " BUILD SPECIFICATION: $PYPROJECT"
    echo "================================================================================"
} >> "$OUTPUT_FILE"

if [ -f "$PYPROJECT" ]; then
    echo "Found $PYPROJECT. Extracting build metadata..."
    cat "$PYPROJECT" >> "$OUTPUT_FILE"
else
    echo "WARNING: $PYPROJECT not found in root directory." >> "$OUTPUT_FILE"
fi

echo -e "\n\n" >> "$OUTPUT_FILE"

# 2. FILE MANIFEST (Summary of what is being included)
{
    echo "================================================================================"
    echo " TRACKED SOURCE FILES MANIFEST"
    echo "================================================================================"
} >> "$OUTPUT_FILE"

# Using git ls-files to respect .gitignore
# --cached: tracked files | --others: untracked | --exclude-standard: use .gitignore
git ls-files "$TARGET_DIR" --cached --others --exclude-standard | grep '\.py$' | while read -r file; do
    line_count=$(wc -l < "$file")
    printf "%-50s | %s lines\n" "$file" "$line_count" >> "$OUTPUT_FILE"
done

echo -e "\n\n" >> "$OUTPUT_FILE"

# 3. SOURCE CODE SECTION
{
    echo "================================================================================"
    echo " COMPLETE SOURCE CODE"
    echo "================================================================================"
} >> "$OUTPUT_FILE"

git ls-files "$TARGET_DIR" --cached --others --exclude-standard | grep '\.py$' | while read -r file; do
    echo "Processing content for: $file"
    
    {
        echo "--------------------------------------------------------------------------------"
        echo " FILE: $file"
        echo "--------------------------------------------------------------------------------"
        cat "$file"
        echo -e "\n"
    } >> "$OUTPUT_FILE"
done

echo "----------------------------------------------------------"
echo "Audit Complete! File generated: $OUTPUT_FILE"
echo "You now have the build spec + the code in one transparent view."

# ---------------------------------------------------------------------------
# SUPERSEDED: the lines below are terminal OUTPUT from a past run that was
# accidentally appended to this script (a `>` that should have been a `>>`,
# or a stray paste). Bash tried to execute them: 44 `command not found`
# errors and exit code 127 on every run. backup.sh pipes this script to a log
# and never checks its exit code, so it failed silently. Commented out rather
# than deleted, per project convention. Safe to remove wholesale.
# ---------------------------------------------------------------------------
# ----------------------------------------------------------
# Starting Audit: Thu Mar 26 20:29:54 GMT 2026
# Target: drumscript
# ----------------------------------------------------------
# Found pyproject.toml. Extracting build metadata...
# Processing content for: drumscript/__init__.py
# Processing content for: drumscript/audio_processor/__init__.py
# Processing content for: drumscript/audio_processor/_classifier.py
# Processing content for: drumscript/audio_processor/audio_loader.py
# Processing content for: drumscript/audio_processor/feature_extractor.py
# Processing content for: drumscript/audio_processor/onset_detector.py
# Processing content for: drumscript/audio_processor/stem_splitter.py
# Processing content for: drumscript/audio_processor/tempo_detector.py
# Processing content for: drumscript/audio_processor/tempogram.py
# Processing content for: drumscript/drum_classifier/__init__.py
# Processing content for: drumscript/drum_classifier/classify.py
# Processing content for: drumscript/main.py
# Processing content for: drumscript/notation_generator/__init__.py
# Processing content for: drumscript/notation_generator/_midi_exporter.py
# Processing content for: drumscript/notation_generator/_pdf_exporter.py
# Processing content for: drumscript/notation_generator/constants.py
# Processing content for: drumscript/notation_generator/helpers.py
# Processing content for: drumscript/notation_generator/midi_exporter.py
# Processing content for: drumscript/notation_generator/pdf_exporter.py
# Processing content for: drumscript/notation_generator/score_builder.py
# Processing content for: drumscript/utils/__init__.py
# Processing content for: drumscript/utils/analyze_closed_hat_physics.py
# Processing content for: drumscript/utils/analyze_crash_physics.py
# Processing content for: drumscript/utils/analyze_high_tom_physics.py
# Processing content for: drumscript/utils/analyze_kick_physics.py
# Processing content for: drumscript/utils/analyze_low_tom_physics.py
# Processing content for: drumscript/utils/analyze_mid_tom_physics.py
# Processing content for: drumscript/utils/analyze_open_hat_physics.py
# Processing content for: drumscript/utils/analyze_ride_physics.py
# Processing content for: drumscript/utils/analyze_snare_physics.py
# Processing content for: drumscript/utils/analyze_tom_physics.py
# Processing content for: drumscript/utils/config.py
# Processing content for: drumscript/utils/ffmpeg_installer.py
# Processing content for: drumscript/utils/get_event_frequencies.py
# Processing content for: drumscript/utils/measure_hat_frequency.py
# Processing content for: drumscript/utils/measure_kick_frequency.py
# Processing content for: drumscript/utils/measure_snare_frequency.py
# ----------------------------------------------------------
# Audit Complete! File generated: drumscript_full_review.txt
# You now have the build spec + the code in one transparent view.----------------------------------------------------------
#
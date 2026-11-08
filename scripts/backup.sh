#!/bin/bash
#
# Usage: run from the project root:
#     ./scripts/backup.sh >> scripts/logs/backup.log
#
# Backs up the drumscript/ folder and the drumscript_full_review.txt
# bundle to .archive/ with a timestamped, descriptive filename.
#
# Sibling-script dependency: this script calls ./scripts/collect_code.sh
# to regenerate drumscript_full_review.txt before backing it up.

# Create the archive directories if they don't exist
mkdir -p .archive/DrumScript__project_folder__archive
mkdir -p .archive/drumscript_full_review__archive.txt

# Prompt for the necessary variables.
# `read -r`: -r treats backslashes literally rather than as escape characters.
# This is almost always what you want for interactive prompts (per shellcheck SC2162).
read -r -p "Is this BEFORE or AFTER the change? (Type BEFORE or AFTER): " TIMING
read -r -p "What is the reason for backing up? (e.g., fixing_tempo_bug): " REASON
read -r -p "What is the backup number for today? (e.g., 1, 2): " BACKUP_NUM

# Generate the date string in ddd-dd-mmm-yyy format (lowercased)
DATE_STR=$(date +"%a%d%b%Y" | tr '[:upper:]' '[:lower:]')

# Construct the shared suffix
SUFFIX="${TIMING}_${REASON}__${DATE_STR}"

# --- Step 1: Backup the drumscript folder ---
FOLDER_BACKUP_NAME="drumscript__LAST__backup${BACKUP_NUM}__${SUFFIX}"
cp -r drumscript/ "$FOLDER_BACKUP_NAME"
mv "$FOLDER_BACKUP_NAME" .archive/DrumScript__project_folder__archive/
echo "Backed up folder to: .archive/DrumScript__project_folder__archive/$FOLDER_BACKUP_NAME"

# --- Step 2: Backup the full review text file ---
# We unconditionally run the collection script so the text file ALWAYS perfectly matches the folder backup above.
echo "Generating latest drumscript_full_review.txt via collect_code.sh..."
# Note: collect_code.sh now lives under scripts/ rather than at project root.
# This script must still be invoked from the project root.
./scripts/collect_code.sh > collect_code.log 2>&1

# Safety check: Verify the file actually exists now before trying to move it
if [ ! -f "drumscript_full_review.txt" ]; then
    echo "WARNING: drumscript_full_review.txt does not exist and could not be generated!"
else
    FILE_BACKUP_NAME="drumscript_full_review__backup${BACKUP_NUM}__${SUFFIX}.txt"
    cp drumscript_full_review.txt "$FILE_BACKUP_NAME"
    mv "$FILE_BACKUP_NAME" .archive/drumscript_full_review__archive.txt/
    echo "Backed up file to: .archive/drumscript_full_review__archive.txt/$FILE_BACKUP_NAME"
fi

echo "Backup complete!"
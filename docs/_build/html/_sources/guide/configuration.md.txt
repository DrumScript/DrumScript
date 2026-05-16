    
# Configuration

## Onset Detection Settings
You can tweak how sensitive the drum detection is by adjusting the threshold.

* **`threshold` (float, default=0.5):** Lower values detect quieter hits (more false positives). Higher values miss ghost notes (fewer false positives).

Example:
``` python
ds.detect_onsets(audio, threshold=0.3) # More sensitive
```

## Output Settings

* **`format`:** Choose between `'pdf'`, `'musicxml'`, or `'midi'`.
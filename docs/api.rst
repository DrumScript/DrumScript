.. _api:

API Reference
=============

This is the auto-generated API reference for DrumScript.

Core Functions
--------------
.. autosummary::
   :toctree: generated
   :nosignatures:

   drumscript.extract_stems
   drumscript.detect_tempo
   drumscript.main

Audio Processing
----------------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.audio_processor.audio_loader
   drumscript.audio_processor.stem_splitter
   drumscript.audio_processor.tempo_detector
   drumscript.audio_processor.onset_detector
   drumscript.audio_processor.feature_extractor

Classification & Notation
-------------------------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.drum_classifier.classify
   drumscript.notation_generator.constants
   drumscript.notation_generator.helpers
   drumscript.notation_generator.score_builder
   drumscript.notation_generator.pdf_exporter

Utilities
---------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.utils.ffmpeg_installer
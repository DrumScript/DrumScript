.. _api:

API Reference
=============

This is the auto-generated API reference for DrumScript.

Core Functions
--------------
.. autosummary::
   :toctree: generated
   :nosignatures:

   extract_stems
   detect_tempo

Audio Processing
----------------
.. autosummary::
   :toctree: generated
   :recursive:

   audio_processor.audio_loader
   audio_processor.stem_splitter
   audio_processor.tempo_detector
   audio_processor.onset_detector
   audio_processor.feature_extractor

Classification & Notation
-------------------------
.. autosummary::
   :toctree: generated
   :recursive:

   drum_classifier.classify
   notation_generator.score_builder
   notation_generator.pdf_exporter

Utilities
---------
.. autosummary::
   :toctree: generated
   :recursive:

   utils.ffmpeg_installer
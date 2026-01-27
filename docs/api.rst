.. _api:

API Reference
=============

This is the auto-generated API reference for DrumScript.

   The examples below can also be used as:
   
   .. code-block:: python

      import drumscript as ds
      ds.notation_generator.constants

Configuration & Constants
-------------------------
DrumScript uses a set of global constants to ensure audio processing consistency. 
These are **not** hidden magic numbers; they are exposed here for transparency.

.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.notation_generator.constants

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
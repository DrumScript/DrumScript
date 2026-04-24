.. _api:

API Reference
=============

This is the auto-generated API reference for DrumScript.

   The examples below can also be used as:
   
   .. code-block:: python

      import drumscript as ds
      ds.detect_tempo()

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

   drumscript.main
   drumscript.extract_stems
   drumscript.detect_tempo
   drumscript.export_pdf
   drumscript.export_midi
   drumscript.export_xml

Audio Processing
----------------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.audio_processor.audio_loader
   drumscript.audio_processor.stem_splitter
   drumscript.audio_processor.stem_splitter.extract_stems
   drumscript.audio_processor.stem_splitter.extract_drum_stem
   drumscript.audio_processor.stem_splitter.mix_stems
   drumscript.audio_processor.stem_splitter.separate_stems
   drumscript.audio_processor.tempo_detector
   drumscript.audio_processor.onset_detector
   drumscript.audio_processor.feature_extractor

Classification 
-----------------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.drum_classifier.classify
   drumscript.drum_classifier.classify.classify_rudiment_events
   drumscript.drum_classifier.classify.classify_event
   drumscript.drum_classifier.classify.classify_events
   drumscript.drum_classifier.classify.classify_idiophone
   drumscript.drum_classifier.classify.classify_membranophone
   drumscript.drum_classifier.classify.extract_features
   drumscript.drum_classifier.classify.get_audio_slice


Score Builders
-----------------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.notation_generator.constants
   drumscript.notation_generator.helpers
   drumscript.notation_generator.score_builder
   drumscript.notation_generator.pdf_exporter
   drumscript.notation_generator.midi_exporter
   drumscript.notation_generator.xml_exporter

Utilities
---------
.. autosummary::
   :toctree: generated
   :recursive:

   drumscript.utils.ffmpeg_installer
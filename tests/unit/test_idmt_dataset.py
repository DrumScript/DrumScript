from __future__ import annotations

import argparse

import numpy as np

from drumscript.datasets import idmt


class TestIdmtDataset:
    def test_parse_annotation_filters_events_by_instrument_and_pitch(self, tmp_path):
        annotation = tmp_path / "RealDrum01_00#MIX.xml"
        annotation.write_text(
            """
            <annotations>
              <event><instrument>KD</instrument><onsetSec>0.1</onsetSec></event>
              <event><instrument>SD</instrument><onsetSec>0.2</onsetSec></event>
              <event><pitch>42</pitch><onsetSec>0.3</onsetSec></event>
            </annotations>
            """
        )

        assert np.array_equal(idmt.parse_annotation(annotation, "KD"), np.array([0.1]))
        assert np.array_equal(idmt.parse_annotation(annotation, "SD"), np.array([0.2]))
        assert np.array_equal(idmt.parse_annotation(annotation, "HH"), np.array([0.3]))

    def test_iter_items_pairs_mix_files_with_reference_annotations(self, tmp_path):
        audio_dir = tmp_path / "audio"
        annotation_dir = tmp_path / "annotation_xml"
        audio_dir.mkdir()
        annotation_dir.mkdir()
        mix_path = audio_dir / "RealDrum01_00#MIX.wav"
        mix_path.write_bytes(b"placeholder")
        (annotation_dir / "RealDrum01_00#MIX.xml").write_text(
            """
            <annotations>
              <event><instrument>KD</instrument><onsetSec>0.1</onsetSec></event>
              <event><instrument>SD</instrument><onsetSec>0.2</onsetSec></event>
              <event><instrument>HH</instrument><onsetSec>0.3</onsetSec></event>
            </annotations>
            """
        )

        items = list(idmt.iter_items(argparse.Namespace(root=str(tmp_path), subset=None)))

        assert len(items) == 1
        item = items[0]
        assert item.track_id == "RealDrum01_00#MIX.wav"
        assert item.audio_path == mix_path
        assert item.bucket == "RealDrum"
        assert np.array_equal(item.references["KD"], np.array([0.1]))
        assert np.array_equal(item.references["SD"], np.array([0.2]))
        assert np.array_equal(item.references["HH"], np.array([0.3]))

    def test_get_annotation_path_prefers_instrument_specific_file(self, tmp_path):
        audio_dir = tmp_path / "audio"
        annotation_dir = tmp_path / "annotation_xml"
        audio_dir.mkdir()
        annotation_dir.mkdir()
        mix_path = audio_dir / "RealDrum01_00#MIX.wav"
        mix_path.write_bytes(b"placeholder")
        generic = annotation_dir / "RealDrum01_00#KD.xml"
        specific = annotation_dir / "RealDrum01_00#SD.xml"
        generic.write_text("<annotations />")
        specific.write_text("<annotations />")

        assert idmt.get_annotation_path(mix_path, "SD") == specific

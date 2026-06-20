from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


def load_benchmark_run():
    module_path = Path(__file__).resolve().parents[2] / "benchmarks" / "run.py"
    spec = importlib.util.spec_from_file_location("benchmark_run", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestBenchmarkRun:
    def test_only_registers_verified_idmt_adapter(self):
        benchmark_run = load_benchmark_run()

        assert list(benchmark_run.ADAPTERS) == ["idmt"]

    def test_evaluate_per_instrument_maps_drumscript_labels_to_dataset_codes(self):
        benchmark_run = load_benchmark_run()

        metrics = benchmark_run.evaluate_per_instrument(
            predictions={
                "kick": [0.0],
                "hi_hat_closed": [1.0],
                "hi_hat_open": [2.0],
            },
            references={
                "KD": np.array([0.0]),
                "HH": np.array([1.0, 2.0]),
            },
            code_to_labels={
                "KD": ["kick"],
                "HH": ["hi_hat_closed", "hi_hat_open"],
            },
        )

        assert metrics["KD"]["precision"] == pytest.approx(1.0)
        assert metrics["KD"]["recall"] == pytest.approx(1.0)
        assert metrics["KD"]["f_measure"] == pytest.approx(1.0)
        assert metrics["HH"]["precision"] == pytest.approx(1.0)
        assert metrics["HH"]["recall"] == pytest.approx(1.0)
        assert metrics["HH"]["f_measure"] == pytest.approx(1.0)

    def test_onset_metrics_returns_named_precision_recall_f_measure(self):
        benchmark_run = load_benchmark_run()

        metrics = benchmark_run.onset_metrics(
            reference=np.array([0.0, 1.0]),
            estimated=np.array([0.0]),
        )

        assert metrics["precision"] == pytest.approx(1.0)
        assert metrics["recall"] == pytest.approx(0.5)
        assert metrics["f_measure"] == pytest.approx(2 / 3)

    def test_evaluate_item_returns_none_when_annotations_are_missing(self, monkeypatch, tmp_path):
        benchmark_run = load_benchmark_run()
        item = benchmark_run.BenchmarkItem(
            track_id="missing",
            audio_path=tmp_path / "missing.wav",
            references={},
        )
        monkeypatch.setattr(
            benchmark_run,
            "predict_instruments",
            lambda path: pytest.fail("prediction should not run for missing annotations"),
        )

        assert benchmark_run.evaluate_item(item, {"KD": ["kick"]}) is None

    def test_count_result_statuses_distinguishes_skipped_from_failed(self, tmp_path):
        benchmark_run = load_benchmark_run()
        items = [
            benchmark_run.BenchmarkItem("evaluated", tmp_path / "evaluated.wav", {"KD": np.array([0.1])}),
            benchmark_run.BenchmarkItem("skipped", tmp_path / "skipped.wav", {}),
            benchmark_run.BenchmarkItem("failed", tmp_path / "failed.wav", {"SD": np.array([0.2])}),
            benchmark_run.BenchmarkItem("empty-metrics", tmp_path / "empty.wav", {"HH": np.array([0.3])}),
        ]
        results = [{"KD": {"precision": 1.0}}, None, None, {}]

        assert benchmark_run.count_result_statuses(items, results) == {
            "files_total": 4,
            "files_evaluated": 2,
            "files_skipped_no_annotations": 1,
            "files_failed": 1,
        }

    def test_predict_instruments_uses_existing_drumscript_pipeline_functions(self, monkeypatch, tmp_path):
        benchmark_run = load_benchmark_run()
        audio_path = tmp_path / "RealDrum01_00#MIX.wav"
        audio_path.write_bytes(b"placeholder")
        audio = np.array([0.0, 0.5, 1.0], dtype=np.float32)
        normalised = np.array([0.0, 0.25, 0.5], dtype=np.float32)

        monkeypatch.setattr(benchmark_run, "load_audio", lambda path, sr: (audio, sr))
        monkeypatch.setattr(benchmark_run, "normalise_audio", lambda y: normalised)
        monkeypatch.setattr(benchmark_run, "detect_onsets", lambda y, sr: [0.5, 0.1])

        def classify_events(y, sr, onsets):
            assert y is normalised
            assert onsets == [0.5, 0.1]
            return [
                {"time_sec": 0.5, "instruments": ["snare"]},
                {"time_sec": 0.1, "instruments": ["kick", "hi_hat_closed"]},
            ]

        monkeypatch.setattr(benchmark_run, "classify_events", classify_events)

        assert benchmark_run.predict_instruments(audio_path) == {
            "hi_hat_closed": [0.1],
            "kick": [0.1],
            "snare": [0.5],
        }

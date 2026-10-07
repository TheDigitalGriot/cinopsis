# Lifted test - Agent-Reach at the pinned sha, exercising scripts/reach.
# Upstream test code is verbatim between the LIFT fences; changed lines end in '# seam:'.

# >>> LIFT agent-reach@a19a171f tests/test_core.py:1-29
# -*- coding: utf-8 -*-
"""Tests for AgentReach core class."""

import pytest

from reach.config import Config  # seam: package import
from reach.core import AgentReach  # seam: package import


@pytest.fixture
def eyes(tmp_path):
    config = Config(config_path=tmp_path / "config.yaml")
    return AgentReach(config=config)


class TestAgentReach:
    def test_init(self, eyes):
        assert eyes.config is not None

    def test_doctor(self, eyes):
        results = eyes.doctor()
        assert isinstance(results, dict)
        assert "youtube" in results  # seam: registry scope: Cinopsis carries YouTube + its sources
        assert all("status" in r for r in results.values())  # seam: registry scope: no github channel

    def test_doctor_report(self, eyes):
        report = eyes.doctor_report()
        assert isinstance(report, str)
        assert "Cinopsis doctor" in report  # seam: English UI
# <<< LIFT

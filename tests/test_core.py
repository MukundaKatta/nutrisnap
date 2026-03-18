"""Tests for Nutrisnap."""
from src.core import Nutrisnap
def test_init(): assert Nutrisnap().get_stats()["ops"] == 0
def test_op(): c = Nutrisnap(); c.analyze(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Nutrisnap(); [c.analyze() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Nutrisnap(); c.analyze(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Nutrisnap(); r = c.analyze(); assert r["service"] == "nutrisnap"

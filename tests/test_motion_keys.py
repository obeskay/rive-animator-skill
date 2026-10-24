import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import motion_keys as K


class TestMotionKeys(unittest.TestCase):
    def test_self_test(self):
        K.self_test()

    def test_flow_never_stops_mid_chain(self):
        # a pose between a rising and a rising segment keeps moving: track would stop there
        pts = K.flow_points([(0, 0), (10, 5), (20, 20)])
        self.assertGreater(pts[1][2], 0)

    def test_flow_holds_at_extremes(self):
        # a turning point gets zero speed, so the curve cannot overshoot it
        pts = K.flow_points([(0, 0), (10, 5), (20, 0)])
        self.assertEqual(pts[1][2], 0)

    def test_wave_cli_rejects_a_period_that_pops(self):
        self.assertEqual(K.main(["wave", "--amp", "1", "--period", "70", "--length", "240"]), 2)

    def test_keyed_block(self):
        xml = K.keyed("0:10", {17: K.track_xml([(0, 1), (7, 0.1), (20, 1, "out")], indent="")})
        self.assertIn('<KeyedObject objectId="0:10">', xml)
        self.assertIn('x1="0.23"', xml)   # the reopening eases out
        self.assertIn('x1="0.77"', xml)   # the closing travels


if __name__ == "__main__":
    unittest.main()

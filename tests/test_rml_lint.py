import unittest
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import rml_lint


class TestRmlLint(unittest.TestCase):
    def test_valid_rml(self):
        rml = """<Rive version="1" kind="fragment">
            <Artboard defaultStateMachineId="0:20" width="200" height="200" name="Valid">
                <Shape x="0" y="0" name="S"><Ellipse width="50" height="50"/><Fill><SolidColor colorValue="FFFF0000"/></Fill></Shape>
                <StateMachine name="SM" id="0:20"><StateMachineLayer name="L"/></StateMachine>
            </Artboard>
        </Rive>"""
        issues = rml_lint.lint_rml_text(rml)
        errors = [i for i in issues if i.severity == rml_lint.ERROR]
        self.assertEqual(len(errors), 0, [e.message for e in errors])

    def test_degree_rotation_warning(self):
        rml = """<Rive version="1" kind="fragment">
            <Artboard width="200" height="200" name="Deg">
                <Shape rotation="180" name="S"><Ellipse width="50" height="50"/></Shape>
            </Artboard>
        </Rive>"""
        issues = rml_lint.lint_rml_text(rml)
        codes = [i.code for i in issues]
        self.assertIn("RML004", codes)

    def _codes(self, body, loop=""):
        rml = f"""<Rive version="1" kind="fragment">
            <Artboard defaultStateMachineId="0:20" width="200" height="200" name="A">
                <Shape name="S" id="0:10"><Ellipse width="50" height="50"/><Fill><SolidColor colorValue="FFFF0000" id="0:11"/></Fill></Shape>
                {body}
            </Artboard>
        </Rive>"""
        return [i.code for i in rml_lint.lint_rml_text(rml)]

    def test_dead_input(self):
        codes = self._codes("""<StateMachine name="SM" id="0:20"><StateMachineNumber name="speed" id="0:21"/>
            <StateMachineLayer name="L"/></StateMachine>""")
        self.assertIn("RML011", codes)

    def test_snap_to_pose(self):
        sm = """<LinearAnimation duration="1" name="Off" id="0:30"/><LinearAnimation duration="1" name="On" id="0:31"/>
            <StateMachine name="SM" id="0:20"><StateMachineBool name="on" id="0:21"/><StateMachineLayer name="L">
            <AnimationState animationId="0:30" id="0:23"><StateTransition stateToId="0:24"{d}>
            <TransitionBoolCondition inputId="0:21"/></StateTransition></AnimationState>
            <AnimationState animationId="0:31" id="0:24"/></StateMachineLayer></StateMachine>"""
        self.assertIn("RML012", self._codes(sm.format(d="")))
        self.assertNotIn("RML012", self._codes(sm.format(d=' duration="200"')))

    def test_loop_seam(self):
        anim = """<LinearAnimation loopValue="loop" duration="60" name="Pulse" id="0:30"><KeyedObject objectId="0:10">
            <KeyedProperty propertyKey="{k}"><KeyFrameDouble value="{a}" frame="0" interpolationType="linear"/>
            <KeyFrameDouble value="{b}" frame="60" interpolationType="linear"/></KeyedProperty></KeyedObject></LinearAnimation>"""
        self.assertIn("RML013", self._codes(anim.format(k=18, a=1, b=0.3)))
        self.assertNotIn("RML013", self._codes(anim.format(k=15, a=0, b=6.2831853)))   # a full turn closes

    def test_double_keyframe_on_colour(self):
        anim = """<LinearAnimation duration="10" name="C" id="0:30"><KeyedObject objectId="0:11">
            <KeyedProperty propertyKey="37"><KeyFrameDouble value="1" frame="0"/></KeyedProperty></KeyedObject></LinearAnimation>"""
        self.assertIn("RML008", self._codes(anim))

    def test_dead_input_without_id(self):
        codes = self._codes("""<StateMachine name="SM" id="0:20"><StateMachineBool name="on"/>
            <StateMachineLayer name="L"/></StateMachine>""")
        self.assertIn("RML011", codes)

    def test_snap_from_any_state(self):
        sm = """<LinearAnimation duration="1" name="Off" id="0:30"/>
            <StateMachine name="SM" id="0:20"><StateMachineTrigger name="t" id="0:21"/><StateMachineLayer name="L">
            <AnyState><StateTransition stateToId="0:24"><TransitionTriggerCondition inputId="0:21"/></StateTransition></AnyState>
            <AnimationState animationId="0:30" id="0:24"/></StateMachineLayer></StateMachine>"""
        self.assertIn("RML012", self._codes(sm))

    def test_exit_time_return_snaps_only_when_it_lands_elsewhere(self):
        sm = """<LinearAnimation duration="1" name="Rest" id="0:30"><KeyedObject objectId="0:10"><KeyedProperty propertyKey="16">
            <KeyFrameDouble value="1" frame="0"/></KeyedProperty></KeyedObject></LinearAnimation>
            <LinearAnimation duration="20" name="Pop" id="0:31"><KeyedObject objectId="0:10"><KeyedProperty propertyKey="16">
            <KeyFrameDouble value="1" frame="0" interpolationType="linear"/><KeyFrameDouble value="{end}" frame="20"/>
            </KeyedProperty></KeyedObject></LinearAnimation>
            <StateMachine name="SM" id="0:20"><StateMachineTrigger name="t" id="0:21"/><StateMachineLayer name="L">
            <AnimationState animationId="0:30" id="0:23"><StateTransition stateToId="0:24" duration="1">
            <TransitionTriggerCondition inputId="0:21"/></StateTransition></AnimationState>
            <AnimationState animationId="0:31" id="0:24"><StateTransition stateToId="0:23" enableExitTime="true"
            exitTimeIsPercetange="true" exitTime="100"/></AnimationState></StateMachineLayer></StateMachine>"""
        self.assertNotIn("RML012", self._codes(sm.format(end=1)))
        self.assertIn("RML012", self._codes(sm.format(end=1.3)))

    def test_degrees_in_a_rotation_key(self):
        anim = """<LinearAnimation duration="60" name="Spin" id="0:30"><KeyedObject objectId="0:10"><KeyedProperty propertyKey="15">
            <KeyFrameDouble value="0" frame="0" interpolationType="linear"/><KeyFrameDouble value="{v}" frame="60"/>
            </KeyedProperty></KeyedObject></LinearAnimation>"""
        self.assertIn("RML004", self._codes(anim.format(v=360)))
        self.assertNotIn("RML004", self._codes(anim.format(v=12.5663706)))   # two full turns in radians

    def test_blank_attributes_do_not_crash(self):
        anim = """<LinearAnimation loopValue="loop" duration="" name="B" id="0:30"><KeyedObject objectId="0:10">
            <KeyedProperty propertyKey="13"><KeyFrameDouble value="" frame="0"/><KeyFrameDouble value="1" frame="9"/>
            </KeyedProperty></KeyedObject></LinearAnimation>"""
        self.assertIsInstance(self._codes(anim), list)

    def test_hand_typed_full_turn_closes(self):
        anim = """<LinearAnimation loopValue="loop" duration="60" name="S" id="0:30"><KeyedObject objectId="0:10">
            <KeyedProperty propertyKey="15"><KeyFrameDouble value="0" frame="0" interpolationType="linear"/>
            <KeyFrameDouble value="6.2832" frame="60"/></KeyedProperty></KeyedObject></LinearAnimation>"""
        self.assertNotIn("RML013", self._codes(anim))


if __name__ == "__main__":
    unittest.main()

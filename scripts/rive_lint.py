#!/usr/bin/env python3
"""Inspect and lint a Rive (.riv) runtime binary. Stdlib only, Python 3.8+.

    python3 rive_lint.py public/mascot.riv          # summary + copy-paste wiring
    python3 rive_lint.py public/*.riv --quiet       # only files with issues
    python3 rive_lint.py mascot.riv --json          # machine-readable
    python3 rive_lint.py mascot.riv --dump          # every object, for debugging
    python3 rive_lint.py --self-test

A .riv is a header, a table of contents typing the property keys the writer
thought a runtime might not know, then a flat stream of objects. This reads
the stream the way rive-runtime's importer does -- registry types first, table
of contents second -- so every name it prints is one the runtime will resolve.
Nothing is guessed from string patterns.

For a project you author with the Rive CLI, `rive inspect <dir> --json` is the
richer tool: it sees the source. This one is for binaries without a source:
editor exports, files already sitting in a repo.

Exit code 0 when no error-level issue is found, 1 otherwise, 2 for bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

ERROR, WARN, INFO = "error", "warn", "info"
_ORDER = {ERROR: 0, WARN: 1, INFO: 2}
SYMBOL = {ERROR: "x", WARN: "!", INFO: "-"}

# -- wire format ------------------------------------------------------------
UINT, STRING, DOUBLE, COLOR, BOOL = 0, 1, 2, 3, 4

# property key -> wire type, generated from rive-runtime
# include/rive/generated/core_registry.hpp (propertyFieldId). A file's own
# table of contents only types keys the writer thought a runtime might not
# know, so it cannot replace this table; it extends it.
PROP_TYPES = {
    int(k): int(v) for k, v in (pair.split(":") for pair in """
    4:1 5:0 7:2 8:2 9:2 10:2 11:2 12:2 13:2 14:2 15:2 16:2 17:2 18:2 20:2 21:2
    23:0 24:2 25:2 26:2 31:2 32:4 33:2 34:2 35:2 37:3 38:3 39:2 40:0 41:4 42:2 46:2
    47:2 48:0 49:0 50:4 51:0 53:0 55:1 56:0 57:0 58:2 59:0 60:0 61:0 62:4 63:2 64:2
    65:2 66:2 67:0 68:0 69:0 70:2 79:2 80:2 81:2 82:2 83:2 84:2 85:2 86:2 87:2 88:3
    89:2 90:2 91:2 92:0 93:0 94:4 95:0 96:2 97:2 98:2 99:2 100:2 101:2 102:0 103:0 104:2
    105:2 106:2 107:2 108:2 109:2 110:0 111:0 112:0 113:0 114:2 115:2 116:2 117:0 118:0 119:0 120:0
    121:0 122:0 123:2 124:2 125:0 126:2 127:2 128:0 129:0 136:0 138:1 140:2 141:4 149:0 151:0 152:0
    155:0 156:0 157:2 158:0 160:0 161:2 162:2 163:2 164:4 165:0 166:2 167:0 168:0 171:0 172:2 173:0
    174:4 175:0 177:2 178:0 179:0 180:0 181:4 182:2 183:2 184:2 185:2 186:2 187:2 188:4 189:4 190:4
    191:4 192:4 193:4 194:4 195:0 196:4 197:0 198:0 199:2 200:2 201:4 202:2 203:1 204:0 206:0 207:2
    208:2 210:0 212:1 215:2 216:2 218:0 221:0 222:0 223:1 224:0 225:0 227:0 228:0 229:2 236:0 237:0
    238:4 239:2 240:0 243:2 245:4 246:1 248:1 249:0 268:1 269:0 270:0 271:0 272:0 273:0 274:2 279:0
    280:1 281:0 284:0 285:2 286:2 287:0 288:2 289:0 292:2 296:0 297:2 298:0 299:2 300:2 301:0 302:0
    303:2 304:2 305:2 306:2 307:2 308:2 312:0 313:0 315:4 316:0 317:2 318:2 319:2 320:0 321:2 322:2
    323:2 324:2 325:0 326:0 327:2 328:2 329:2 330:2 331:2 332:2 333:4 334:2 335:0 336:2 337:2 338:2
    339:2 340:2 349:0 350:0 356:0 357:0 359:1 362:1 363:2 364:4 365:4 366:2 367:2 368:2 369:2 370:2
    371:2 372:2 373:2 376:4 377:0 378:0 380:2 381:2 389:0 390:2 392:0 393:0 399:0 400:0 405:0 406:2
    407:2 408:0 410:2 411:2 412:0 414:0 415:0 416:2 417:2 418:0 419:4 420:4 494:0 498:2 499:2 500:2
    501:2 502:2 503:2 504:2 505:2 506:2 507:2 508:2 509:2 510:2 511:2 512:2 513:2 514:2 515:2 516:2
    517:2 518:2 519:2 523:2 524:2 530:2 536:0 537:0 538:0 541:4 549:0 550:0 554:0 555:3 557:1 560:0
    561:1 566:0 572:1 574:0 575:2 577:0 578:1 579:1 582:1 583:0 586:0 587:0 588:1 589:0 590:0 591:0
    592:2 593:4 596:0 597:0 598:0 599:0 604:0 605:0 606:4 607:0 608:0 609:0 610:0 611:0 612:0 613:0
    614:0 615:0 616:0 617:0 618:0 619:0 620:0 621:0 622:0 623:0 624:0 625:0 626:0 627:0 628:0 629:0
    630:0 631:0 632:0 634:4 635:1 636:2 637:0 638:3 639:4 640:2 641:2 642:2 643:2 644:2 645:2 647:4
    650:0 651:3 652:2 653:0 654:1 655:0 656:0 660:0 662:1 663:2 664:2 665:0 666:0 667:0 668:0 669:0
    672:0 673:0 675:2 676:4 679:0 681:2 682:0 683:0 685:0 686:0 687:0 689:0 690:2 691:4 692:2 693:4
    697:2 698:2 699:2 700:2 703:4 705:0 706:2 707:2 708:0 709:0 711:1 713:0 714:0 715:0 716:2 717:2
    718:2 719:2 722:0 724:4 725:0 726:0 727:0 728:2 729:2 730:2 731:0 734:4 743:0 744:1 745:0 746:0
    747:0 748:0 749:2 750:2 751:2 752:4 756:2 757:0 758:0 759:2 760:2 761:2 762:2 763:2 764:0 765:0
    766:1 770:4 775:0 776:0 777:2 778:0 779:4 781:2 782:4 783:2 784:2 785:2 786:2 800:0 806:2 807:2
    808:2 809:2 810:2 811:2 814:0 816:0 817:1 818:2 823:0 824:0 835:0 836:3 846:0 848:0 850:4 851:4
    858:0 859:2 860:2 864:2 865:2 866:1 868:1 870:0 871:1 872:0 873:0 874:0 875:0 876:0 887:0 888:2
    889:2 891:4 892:0 893:0 894:2 895:4 907:2 908:2 911:1 912:0 914:4 920:1 921:4 922:0 926:1 930:0
    931:0 932:0 934:0 935:0 952:0 953:4 954:4 955:4 956:0 957:0 962:0 963:1 965:0 966:0 971:0 972:0
    973:0 974:0 975:2 976:2 977:0 979:4 980:0 981:0 982:0 983:1 984:1 985:1 986:0 987:0 988:0 989:4
    990:4 991:4 992:4 993:4 994:4 995:4 996:4 997:4 998:0 1000:4 1001:4 1002:4 1003:4 1004:4 1005:4 1006:4
    1007:4 1008:4 1009:4 1010:0 1011:0 1014:4 1015:0 1018:0 1019:0 1020:0 1021:0 1022:0 1023:2 1024:2 1025:4 1026:0
    1027:0 1028:0 1029:2 1033:0 1040:2 1041:2 1045:0 1046:0 1047:0 1048:0 1049:0 1050:0 1057:2 1058:2 1059:0 1061:0
    1062:0 1063:2 1064:0 1065:2 1066:2 1067:2 1068:0 1069:2 1070:2 1071:2 1073:0 1074:0 1075:0 1076:0 1077:0 1078:0
    1087:0 1094:0 1095:4 1098:4 1099:4
""".split())
}
# Serialised like strings (length + bytes) but not text.
BYTES_KEYS = {212, 223, 359, 582, 588, 711, 866, 868, 871, 911, 920, 963}

# Object type keys this tool interprets. Everything else is walked and counted.
ARTBOARD = 1
LINEAR_ANIMATION, STATE_MACHINE, LAYER = 31, 53, 57
INPUT_TYPES = {56: "Number", 58: "Trigger", 59: "Boolean"}
STATE_TYPES = {61, 62, 63, 64, 73, 76, 528}
TRANSITION_TYPES = {65, 78}
LISTENER_TYPES = {114: "single", 654: "general"}
FIRE_EVENT = 169
EVENT_TYPES = {128: "Event", 131: "OpenUrlEvent", 407: "AudioEvent"}
TEXT_RUN = 135
NESTED_ARTBOARD_TYPES = {92, 451, 452}
BONE_TYPES = {40, 41}
FILE_ASSET_CONTENTS = 106
ASSET_TYPES = {105: "image", 141: "font", 406: "audio", 529: "script", 605: "component"}
VIEW_MODEL, DATA_ENUM = 435, 438
VM_PROPERTY_TYPES = {
    431: "number", 443: "string", 448: "boolean", 440: "color", 509: "enum",
    439: "enum", 511: "enum", 502: "trigger", 434: "list", 436: "viewModel",
    598: "artboard", 584: "asset", 585: "image", 563: "symbol", 564: "symbolListIndex",
}
TYPE_NAMES = {
    1: "Artboard", 2: "Node", 3: "Shape", 4: "Ellipse", 5: "StraightVertex",
    6: "CubicDetachedVertex", 7: "Rectangle", 8: "Triangle", 16: "PointsPath",
    17: "LinearGradient", 18: "SolidColor", 19: "GradientStop", 20: "Fill",
    22: "RadialGradient", 23: "Backboard", 24: "Stroke", 25: "KeyedObject",
    26: "KeyedProperty", 28: "CubicEaseInterpolator", 30: "KeyFrameDouble",
    31: "LinearAnimation", 34: "CubicAsymmetricVertex", 35: "CubicMirroredVertex",
    37: "KeyFrameColor", 40: "Bone", 41: "RootBone", 42: "ClippingShape", 43: "Skin",
    44: "Tendon", 45: "Weight", 47: "TrimPath", 48: "DrawTarget", 49: "DrawRules",
    50: "KeyFrameId", 51: "Polygon", 52: "Star", 53: "StateMachine",
    56: "StateMachineNumber", 57: "StateMachineLayer", 58: "StateMachineTrigger",
    59: "StateMachineBool", 61: "AnimationState", 62: "AnyState", 63: "EntryState",
    64: "ExitState", 65: "StateTransition", 68: "TransitionTriggerCondition",
    70: "TransitionNumberCondition", 71: "TransitionBoolCondition",
    73: "BlendStateDirect", 74: "BlendAnimation", 75: "BlendAnimation1D",
    76: "BlendState1DInput", 77: "BlendAnimationDirect", 78: "BlendStateTransition",
    81: "IKConstraint", 82: "DistanceConstraint", 83: "TransformConstraint",
    84: "KeyFrameBool", 87: "TranslationConstraint", 88: "ScaleConstraint",
    89: "RotationConstraint", 92: "NestedArtboard", 95: "NestedStateMachine",
    96: "NestedSimpleAnimation", 98: "NestedRemapAnimation", 100: "Image",
    105: "ImageAsset", 106: "FileAssetContents", 109: "Mesh", 114: "StateMachineListenerSingle",
    115: "ListenerTriggerChange", 117: "ListenerBoolChange", 118: "ListenerNumberChange",
    122: "NestedTrigger", 123: "NestedBool", 124: "NestedNumber", 126: "ListenerAlignTarget",
    127: "CustomPropertyNumber", 128: "Event", 129: "CustomPropertyBoolean",
    130: "CustomPropertyString", 131: "OpenUrlEvent", 134: "Text", 135: "TextValueRun",
    137: "TextStylePaint", 138: "CubicValueInterpolator", 141: "FontAsset",
    142: "KeyFrameString", 147: "Solo", 148: "Joystick", 165: "FollowPathConstraint",
    168: "ListenerFireEvent", 169: "StateMachineFireEvent", 174: "ElasticInterpolator",
    406: "AudioAsset", 407: "AudioEvent", 409: "LayoutComponent", 420: "LayoutComponentStyle",
    435: "ViewModel", 437: "ViewModelInstance", 438: "DataEnumCustom", 446: "DataBind",
    447: "DataBindContext", 450: "KeyFrameUint", 451: "NestedArtboardLeaf",
    452: "NestedArtboardLayout", 482: "TransitionViewModelCondition",
    529: "ScriptAsset", 605: "ComponentAsset", 654: "StateMachineListener",
}
TYPE_NAMES.update({k: "ViewModelProperty(%s)" % v for k, v in VM_PROPERTY_TYPES.items()})

# property keys
P_NAME = (4, 55, 138, 203, 557, 572)   # Component, Animation, StateMachineComponent, Asset, ViewModelComponent, DataEnumCustom
P_WIDTH, P_HEIGHT, P_DEFAULT_SM = 7, 8, 236
P_FPS, P_DURATION, P_LOOP = 56, 57, 59
P_NUMBER_VALUE, P_BOOL_VALUE = 140, 141
P_LISTENER_TYPE, P_LISTENER_TARGET = 225, 224
P_TEXT, P_ARTBOARD_ID, P_BYTES, P_CDN_UUID = 268, 197, 212, 359

LOOP_NAMES = {0: "one-shot", 1: "loop", 2: "ping-pong"}
LISTENER_NAMES = [
    "enter", "exit", "down", "up", "move", "event", "click", "componentProvided",
    "textInput", "dragStart", "dragEnd", "viewModel", "drag", "focus", "blur",
    "keyboard", "semanticAction", "gamepad",
]


# -- reading ----------------------------------------------------------------
class Malformed(Exception):
    pass


class Reader:
    __slots__ = ("data", "pos")

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def eof(self):
        return self.pos >= len(self.data)

    def byte(self):
        if self.pos >= len(self.data):
            raise Malformed("unexpected end of file at byte %d" % self.pos)
        value = self.data[self.pos]
        self.pos += 1
        return value

    def varuint(self):
        result = 0
        shift = 0
        while True:
            b = self.byte()
            result |= (b & 0x7F) << shift
            if not b & 0x80:
                return result
            shift += 7
            if shift > 63:
                raise Malformed("varuint longer than 64 bits at byte %d" % self.pos)

    def take(self, count):
        if self.pos + count > len(self.data):
            raise Malformed(
                "unexpected end of file at byte %d (wanted %d more)" % (self.pos, count)
            )
        chunk = self.data[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def u32(self):
        return struct.unpack("<I", self.take(4))[0]

    def f32(self):
        return struct.unpack("<f", self.take(4))[0]


def parse(data):
    """Header, table of contents, then every object as (type_key, props, offset).

    Mirrors readRuntimeObject() in rive-runtime/src/file.cpp: a property the
    registry knows is read by its registered type, anything else by the table
    of contents, and a key neither can type leaves the rest of the stream
    unreadable.
    """
    r = Reader(data)
    if bytes(r.take(4)) != b"RIVE":
        raise Malformed("not a Rive file: header is %r, expected b'RIVE'" % bytes(data[:4]))
    major, minor, file_id = r.varuint(), r.varuint(), r.varuint()
    keys = []
    while True:
        key = r.varuint()
        if key == 0:
            break
        keys.append(key)
    toc = {}
    word, bit = 0, 8
    for key in keys:  # four keys per uint32, two bits each
        if bit == 8:
            word, bit = r.u32(), 0
        toc[key] = (word >> bit) & 3
        bit += 2

    objects = []
    while not r.eof():
        offset = r.pos
        type_key = r.varuint()
        props = {}
        while True:
            key = r.varuint()
            if key == 0:
                break
            kind = PROP_TYPES.get(key, toc.get(key))
            if kind is None:
                raise Malformed(
                    "property key %d at byte %d is unknown to the runtime and absent "
                    "from the file's table of contents" % (key, r.pos)
                )
            if kind == UINT:
                value = r.varuint()
            elif kind == STRING:
                raw = bytes(r.take(r.varuint()))
                value = raw if key in BYTES_KEYS else raw.decode("utf-8", "replace")
            elif kind == DOUBLE:
                value = r.f32()
            elif kind == COLOR:
                value = r.u32()
            else:  # BOOL is a single byte
                value = r.byte() == 1
            props[key] = value
        objects.append((type_key, props, offset))
    return {"major": major, "minor": minor, "file_id": file_id, "toc": toc, "objects": objects}


# -- model ------------------------------------------------------------------
def _name(props):
    for key in P_NAME:
        if isinstance(props.get(key), str):
            return props[key]
    return None


def build(objects):
    """Group the flat stream by ownership.

    The stream is ordered: an artboard, then everything in it; a state
    machine, then its inputs, layers and states; an asset, then its bytes.
    References that survive to the runtime are indices, not editor ids: an
    artboard's defaultStateMachineId is an index into its own machines.
    """
    model = {"artboards": [], "viewModels": [], "enums": [], "assets": [],
             "objects": len(objects), "types": Counter()}
    artboard = machine = view_model = asset = None
    for type_key, props, _ in objects:
        model["types"][type_key] += 1
        name = _name(props)
        if type_key == ARTBOARD:
            artboard = {
                "name": name, "width": props.get(P_WIDTH), "height": props.get(P_HEIGHT),
                "defaultStateMachine": props.get(P_DEFAULT_SM),
                "animations": [], "stateMachines": [], "events": [], "textRuns": [],
                "nestedArtboards": [], "bones": 0,
            }
            model["artboards"].append(artboard)
            machine = None
        elif type_key == LINEAR_ANIMATION and artboard is not None:
            fps = props.get(P_FPS, 60) or 60
            frames = props.get(P_DURATION, 60)
            artboard["animations"].append({
                "name": name, "fps": fps, "frames": frames,
                "seconds": round(frames / fps, 3),
                "loop": LOOP_NAMES.get(props.get(P_LOOP, 0), "loop %r" % props.get(P_LOOP)),
            })
        elif type_key == STATE_MACHINE and artboard is not None:
            machine = {"name": name, "inputs": [], "layers": [], "listeners": [],
                       "states": 0, "transitions": 0, "firedEvents": 0}
            artboard["stateMachines"].append(machine)
        elif type_key in INPUT_TYPES and machine is not None:
            kind = INPUT_TYPES[type_key]
            if kind == "Number":
                default = round(props.get(P_NUMBER_VALUE, 0.0), 4)
            elif kind == "Boolean":
                default = bool(props.get(P_BOOL_VALUE, False))
            else:
                default = None
            machine["inputs"].append({"name": name, "type": kind, "default": default})
        elif type_key == LAYER and machine is not None:
            machine["layers"].append(name)
        elif type_key in STATE_TYPES and machine is not None:
            machine["states"] += 1
        elif type_key in TRANSITION_TYPES and machine is not None:
            machine["transitions"] += 1
        elif type_key in LISTENER_TYPES and machine is not None:
            index = props.get(P_LISTENER_TYPE)
            if LISTENER_TYPES[type_key] == "general":
                kind = "general"
            else:
                kind = LISTENER_NAMES[index] if isinstance(index, int) and index < len(LISTENER_NAMES) else str(index)
            machine["listeners"].append({"name": name, "type": kind, "target": props.get(P_LISTENER_TARGET)})
        elif type_key == FIRE_EVENT and machine is not None:
            machine["firedEvents"] += 1
        elif type_key in EVENT_TYPES and artboard is not None:
            artboard["events"].append({"name": name, "type": EVENT_TYPES[type_key]})
        elif type_key == TEXT_RUN and artboard is not None:
            artboard["textRuns"].append({"name": name, "text": props.get(P_TEXT, "")})
        elif type_key in NESTED_ARTBOARD_TYPES and artboard is not None:
            artboard["nestedArtboards"].append({"name": name, "artboard": props.get(P_ARTBOARD_ID)})
        elif type_key in BONE_TYPES and artboard is not None:
            artboard["bones"] += 1
        elif 203 in props:  # every Asset subclass carries Asset.name
            asset = {"name": name, "type": ASSET_TYPES.get(type_key, "type %d" % type_key),
                     "bytes": 0, "cdn": bool(props.get(P_CDN_UUID))}
            model["assets"].append(asset)
        elif type_key == FILE_ASSET_CONTENTS and asset is not None:
            asset["bytes"] += len(props.get(P_BYTES, b""))
        elif type_key == VIEW_MODEL:
            view_model = {"name": name, "properties": []}
            model["viewModels"].append(view_model)
        elif type_key in VM_PROPERTY_TYPES and view_model is not None:
            view_model["properties"].append({"name": name, "type": VM_PROPERTY_TYPES[type_key]})
        elif type_key == DATA_ENUM:
            model["enums"].append(name)

    for ab in model["artboards"]:
        index = ab["defaultStateMachine"]
        machines = ab["stateMachines"]
        ab["defaultStateMachine"] = (
            machines[index]["name"] if isinstance(index, int) and 0 <= index < len(machines) else None
        )
        for nested in ab["nestedArtboards"]:
            index = nested["artboard"]
            if isinstance(index, int) and 0 <= index < len(model["artboards"]):
                nested["artboard"] = model["artboards"][index]["name"]
    model["types"] = {TYPE_NAMES.get(k, "type %d" % k): v for k, v in sorted(model["types"].items())}
    return model


# -- lint -------------------------------------------------------------------
def lint(parsed, model, size):
    issues = []

    def add(code, severity, message, hint=""):
        issues.append({"code": code, "severity": severity, "message": message, "hint": hint})

    if parsed["major"] != 7:
        add("RV002", WARN,
            "format version %d.%d; current runtimes read major version 7" % (parsed["major"], parsed["minor"]),
            "Re-export from a current editor or rebuild with the CLI.")
    if not model["artboards"]:
        add("RV003", ERROR, "no artboard; nothing can be displayed")

    for ab in model["artboards"]:
        label = 'artboard "%s"' % ab["name"]
        if not ab["stateMachines"]:
            add("RV004", INFO, "%s has no state machine; it can only play timelines" % label,
                "Load it with animations: '<name>' rather than stateMachines:. "
                "Nothing in it can react to input or data.")
        elif ab["defaultStateMachine"] is None:
            add("RV007", INFO, "%s has no default state machine" % label,
                "A runtime given no stateMachines: option falls back to the first "
                "animation. Name the machine explicitly.")
        for sm in ab["stateMachines"]:
            slabel = 'state machine "%s"' % sm["name"]
            if not sm["layers"]:
                add("RV009", WARN, "%s has no layers; it can never change state" % slabel)
            if not sm["inputs"] and not sm["listeners"]:
                add("RV005", INFO, "%s has no inputs and no listeners; it runs on its own" % slabel,
                    "Nothing the host sets will change it. If it was meant to react, "
                    "the inputs did not make it into the export.")
            seen = {}
            for inp in sm["inputs"]:
                raw = inp["name"] or ""
                key = raw.strip().lower()
                if key in seen and seen[key] != raw:
                    add("RV006", WARN, '%s: inputs "%s" and "%s" differ only by case or spacing'
                        % (slabel, seen[key], raw),
                        "useStateMachineInput matches the exact string; keep one spelling.")
                elif key in seen:
                    add("RV006", WARN, '%s: duplicate input name "%s"' % (slabel, raw))
                seen.setdefault(key, raw)
                if raw != raw.strip():
                    add("RV011", WARN, '%s: input "%s" has leading or trailing whitespace' % (slabel, raw),
                        "The runtime matches the exact string, so the trimmed name in code will not find it.")
        for anim in ab["animations"]:
            if not anim["frames"]:
                add("RV010", WARN, '%s: animation "%s" has zero duration' % (label, anim["name"]))
        w, h = ab["width"], ab["height"]
        if isinstance(w, (int, float)) and isinstance(h, (int, float)) and (w <= 0 or h <= 0):
            add("RV012", ERROR, '%s has invalid dimensions %g×%g; canvas will be 0×0 or clipped' % (label, w, h),
                "Set positive width and height on the Artboard.")

    for asset in model["assets"]:
        if asset["bytes"] > 150_000:
            add("RV008", WARN, '%s asset "%s" embeds %s' % (asset["type"], asset["name"], _kb(asset["bytes"])),
                "Fonts and bitmaps dominate .riv size. Subset the font, downscale the "
                "image, or host it on the Rive CDN and load it at runtime.")
    embedded = sum(a["bytes"] for a in model["assets"])
    if size > 1_000_000 and embedded < size // 2:
        add("RV008", WARN, "file is %s with only %s in assets; the vector content itself is heavy" % (_kb(size), _kb(embedded)),
            "Look for paths with thousands of vertices or duplicated artboards.")
    issues.sort(key=lambda i: (_ORDER[i["severity"]], i["code"]))
    return issues


# -- output -----------------------------------------------------------------
def _kb(n):
    return "%.1f KB" % (n / 1024.0) if n < 1_000_000 else "%.2f MB" % (n / 1_048_576.0)


def _ident(name):
    parts = re.findall(r"[A-Za-z0-9]+", name or "")
    if not parts:
        return "input"
    head, *rest = parts
    ident = head[:1].lower() + head[1:] + "".join(p[:1].upper() + p[1:] for p in rest)
    return ident if not ident[:1].isdigit() else "_" + ident


def _wiring_react(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    opts = ["src: '/%s'" % path.name]
    if many:
        opts.append("artboard: '%s'" % ab["name"])
    if sm:
        opts.append("stateMachines: '%s'" % sm["name"])
    elif ab["animations"]:
        opts.append("animations: '%s'" % ab["animations"][0]["name"])
    opts.append("autoplay: true")
    lines.append("const { rive, RiveComponent } = useRive({ %s });" % ", ".join(opts))
    for m in machines:
        for inp in m["inputs"]:
            ident = _ident(inp["name"])
            use = {"Boolean": "%s.value = true" % ident, "Number": "%s.value = 42" % ident,
                   "Trigger": "%s.fire()" % ident}[inp["type"]]
            lines.append("const %s = useStateMachineInput(rive, '%s', '%s');  // %s: %s"
                         % (ident, m["name"], inp["name"], inp["type"], use))
        kinds = sorted({l["type"] for l in m["listeners"]})
        if kinds:
            lines.append("// '%s' handles %s itself via listeners; do not also wire DOM events"
                         % (m["name"], ", ".join(kinds)))
    for run in ab["textRuns"]:
        lines.append("rive.setTextRunValue('%s', '...');  // currently %r" % (run["name"], run["text"][:30]))
    for ev in ab["events"]:
        lines.append("rive.on(EventType.RiveEvent, (e) => e.data.name === '%s' && ...);" % ev["name"])
    return lines


def _wiring_vue(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import { onMounted, ref } from 'vue';")
    lines.append("import { Rive, Layout, Fit, Alignment } from '@rive-app/canvas';")
    lines.append("const canvas = ref(null);")
    lines.append("let riveInstance = null;")
    lines.append("onMounted(() => {")
    lines.append("  riveInstance = new Rive({")
    lines.append("    src: '/%s'," % path.name)
    lines.append("    canvas: canvas.value,")
    lines.append("    autoplay: true,")
    if many:
        lines.append("    artboard: '%s'," % ab["name"])
    if sm:
        lines.append("    stateMachines: '%s'," % sm_str)
    lines.append("    onLoad: () => {")
    lines.append("      riveInstance.resizeDrawingSurfaceToCanvas();")
    if sm and sm["inputs"]:
        lines.append("      const inputs = riveInstance.stateMachineInputs('%s');" % sm_str)
        for inp in sm["inputs"]:
            ident = _ident(inp["name"])
            lines.append("      const %s = inputs.find(i => i.name === '%s');" % (ident, inp["name"]))
    lines.append("    },")
    lines.append("  });")
    lines.append("});")
    return lines


def _wiring_svelte(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import { onMount } from 'svelte';")
    lines.append("import { Rive } from '@rive-app/canvas';")
    lines.append("let canvas, rive;")
    lines.append("onMount(() => {")
    lines.append("  rive = new Rive({")
    lines.append("    src: '/%s'," % path.name)
    lines.append("    canvas,")
    lines.append("    autoplay: true,")
    if sm:
        lines.append("    stateMachines: '%s'," % sm_str)
    lines.append("    onLoad: () => rive.resizeDrawingSurfaceToCanvas(),")
    lines.append("  });")
    lines.append("  return () => rive.cleanup();")
    lines.append("});")
    return lines


def _wiring_web(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import { Rive } from '@rive-app/canvas';")
    lines.append("const canvas = document.getElementById('rive-canvas');")
    lines.append("const r = new Rive({")
    lines.append("  src: '/%s'," % path.name)
    lines.append("  canvas,")
    lines.append("  autoplay: true,")
    if many:
        lines.append("  artboard: '%s'," % ab["name"])
    if sm:
        lines.append("  stateMachines: '%s'," % sm_str)
    lines.append("  onLoad: () => {")
    lines.append("    r.resizeDrawingSurfaceToCanvas();")
    if sm and sm["inputs"]:
        lines.append("    const inputs = r.stateMachineInputs('%s');" % sm_str)
        for inp in sm["inputs"]:
            ident = _ident(inp["name"])
            lines.append("    const %s = inputs.find(i => i.name === '%s');" % (ident, inp["name"]))
    lines.append("  },")
    lines.append("});")
    return lines


def _wiring_flutter(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import 'package:rive/rive.dart';")
    if sm and sm["inputs"]:
        for inp in sm["inputs"]:
            smi_type = {"Boolean": "SMIBool?", "Number": "SMINumber?", "Trigger": "SMITrigger?"}.get(inp["type"], "dynamic")
            lines.append("%s _%s;" % (smi_type, _ident(inp["name"])))
    lines.append("void _onRiveInit(Artboard artboard) {")
    if sm:
        lines.append("  final controller = StateMachineController.fromArtboard(artboard, '%s');" % sm_str)
        lines.append("  if (controller != null) {")
        lines.append("    artboard.addController(controller);")
        for inp in sm["inputs"]:
            smi = {"Boolean": "SMIBool", "Number": "SMINumber", "Trigger": "SMITrigger"}.get(inp["type"], "dynamic")
            cast = {"Boolean": "bool", "Number": "double", "Trigger": "void"}.get(inp["type"], "dynamic")
            if inp["type"] == "Trigger":
                lines.append("    _%s = controller.findInput('%s') as %s?;" % (_ident(inp["name"]), inp["name"], smi))
            else:
                lines.append("    _%s = controller.findInput<%s>('%s') as %s?;" % (_ident(inp["name"]), cast, inp["name"], smi))
        lines.append("  }")
    lines.append("}")
    artboard_arg = ", artboard: '%s'" % ab["name"] if many else ""
    lines.append("// Widget: RiveAnimation.asset('assets/%s', onInit: _onRiveInit%s)" % (path.name, artboard_arg))
    return lines


def _wiring_swiftui(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import SwiftUI")
    lines.append("import RiveRuntime")
    lines.append("@StateObject private var rive = RiveViewModel(")
    lines.append("    fileName: \"%s\"," % path.stem)
    if sm:
        lines.append("    stateMachineName: \"%s\"," % sm_str)
    if many:
        lines.append("    artboardName: \"%s\"," % ab["name"])
    lines.append("    autoPlay: true")
    lines.append(")")
    lines.append("// In View body: rive.view().frame(width: 300, height: 300)")
    if sm and sm["inputs"]:
        for inp in sm["inputs"]:
            ident = inp["name"]
            if inp["type"] == "Boolean":
                lines.append("// rive.setInput(\"%s\", value: true)" % ident)
            elif inp["type"] == "Number":
                lines.append("// rive.setInput(\"%s\", value: 42.0)" % ident)
            elif inp["type"] == "Trigger":
                lines.append("// rive.triggerInput(\"%s\")" % ident)
    return lines


def _wiring_android(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("// In layout: <app.rive.runtime.kotlin.RiveAnimationView app:riveResource=\"@raw/%s\" ... />" % path.stem)
    lines.append("val riveView = findViewById<RiveAnimationView>(R.id.riveView)")
    if sm and sm["inputs"]:
        for inp in sm["inputs"]:
            ident = inp["name"]
            if inp["type"] == "Boolean":
                lines.append("riveView.setBooleanState(\"%s\", \"%s\", true)" % (sm_str, ident))
            elif inp["type"] == "Number":
                lines.append("riveView.setNumberState(\"%s\", \"%s\", 42f)" % (sm_str, ident))
            elif inp["type"] == "Trigger":
                lines.append("riveView.fireState(\"%s\", \"%s\")" % (sm_str, ident))
    return lines


def _wiring_react_native(path, ab, many):
    lines = []
    machines = ab["stateMachines"]
    sm = next((m for m in machines if m["name"] == ab["defaultStateMachine"]), machines[0] if machines else None)
    sm_str = sm["name"] if sm else ""
    lines.append("import Rive, { RiveRef } from '@rive-app/react-native';")
    lines.append("const riveRef = useRef<RiveRef>(null);")
    lines.append("<Rive ref={riveRef} resourceName='%s' stateMachineName='%s' autoplay style={{ width: 300, height: 300 }} />"
                 % (path.stem, sm_str))
    if sm and sm["inputs"]:
        for inp in sm["inputs"]:
            ident = inp["name"]
            if inp["type"] == "Boolean":
                lines.append("// riveRef.current?.setInputState('%s', '%s', true);" % (sm_str, ident))
            elif inp["type"] == "Number":
                lines.append("// riveRef.current?.setInputState('%s', '%s', 42);" % (sm_str, ident))
            elif inp["type"] == "Trigger":
                lines.append("// riveRef.current?.fireState('%s', '%s');" % (sm_str, ident))
    return lines


FRAMEWORK_GENERATORS = {
    "react": ("React (@rive-app/react-canvas)", _wiring_react),
    "vue": ("Vue 3 (@rive-app/canvas)", _wiring_vue),
    "svelte": ("Svelte (@rive-app/canvas)", _wiring_svelte),
    "web": ("Vanilla Web Canvas (@rive-app/canvas)", _wiring_web),
    "flutter": ("Flutter (rive)", _wiring_flutter),
    "swiftui": ("SwiftUI / iOS (RiveRuntime)", _wiring_swiftui),
    "android": ("Android Kotlin (app.rive:rive-android)", _wiring_android),
    "react-native": ("React Native (@rive-app/react-native)", _wiring_react_native),
}


def wiring(path, model, framework="react"):
    """The exact strings the runtime will resolve, ready to paste."""
    many = len(model["artboards"]) > 1
    selected = list(FRAMEWORK_GENERATORS.keys()) if framework == "all" else [framework]
    sections = []
    for fw in selected:
        if fw not in FRAMEWORK_GENERATORS:
            continue
        title, gen_func = FRAMEWORK_GENERATORS[fw]
        fw_lines = []
        for ab in model["artboards"]:
            fw_lines.extend(gen_func(path, ab, many))
        if model["viewModels"] and fw in ("react", "web", "vue"):
            fw_lines.append("// data binding: autoBind: true, then rive.viewModelInstance")
            for vm in model["viewModels"]:
                for prop in vm["properties"][:4]:
                    fw_lines.append("//   .%s('%s')  (%s)" % (prop["type"], prop["name"], vm["name"]))
        sections.append((title, fw_lines))
    return sections


def report(path, size, parsed, model, issues, framework="react"):
    out = []
    n_ab = len(model["artboards"])
    out.append("%s  %s  ·  format %d.%d  ·  %d artboard%s  ·  %d objects"
               % (path.name, _kb(size), parsed["major"], parsed["minor"], n_ab, "" if n_ab == 1 else "s", model["objects"]))
    for ab in model["artboards"]:
        out.append("")
        w, h = ab["width"], ab["height"]
        dims = "  %g×%g" % (w, h) if isinstance(w, (int, float)) and isinstance(h, (int, float)) else ""
        out.append('Artboard "%s"%s' % (ab["name"], dims))
        if ab["animations"]:
            out.append("  animations (%d)" % len(ab["animations"]))
            for a in ab["animations"]:
                out.append("    %-26s %4d frames @%-3d %5.2fs  %s" % (a["name"], a["frames"], a["fps"], a["seconds"], a["loop"]))
        for sm in ab["stateMachines"]:
            tag = "  (default)" if sm["name"] == ab["defaultStateMachine"] else ""
            out.append('  state machine "%s"%s  %d layer%s · %d states · %d transitions · %d listener%s'
                       % (sm["name"], tag, len(sm["layers"]), "" if len(sm["layers"]) == 1 else "s",
                          sm["states"], sm["transitions"], len(sm["listeners"]), "" if len(sm["listeners"]) == 1 else "s"))
            if sm["inputs"]:
                out.append("    inputs (%d)" % len(sm["inputs"]))
                for inp in sm["inputs"]:
                    default = "" if inp["default"] is None else "  default %s" % inp["default"]
                    out.append("      %-24s %-8s%s" % (inp["name"], inp["type"], default))
            if sm["listeners"]:
                out.append("    listeners: " + ", ".join(
                    "%s (%s)" % (l["name"], l["type"]) if l["name"] else l["type"] for l in sm["listeners"]))
            if sm["firedEvents"]:
                out.append("    fires %d event%s from states" % (sm["firedEvents"], "" if sm["firedEvents"] == 1 else "s"))
        if ab["textRuns"]:
            out.append("  text runs: " + ", ".join('"%s" = %r' % (r["name"], r["text"][:24]) for r in ab["textRuns"]))
        if ab["events"]:
            out.append("  events: " + ", ".join('"%s" (%s)' % (e["name"], e["type"]) for e in ab["events"]))
        if ab["nestedArtboards"]:
            out.append("  nested artboards: " + ", ".join(
                '"%s" -> %s' % (n["name"] or "(unnamed)", n["artboard"]) for n in ab["nestedArtboards"]))
        if ab["bones"]:
            out.append("  bones: %d (rigged)" % ab["bones"])
    if model["viewModels"]:
        out.append("")
        out.append("View models (data binding)")
        for vm in model["viewModels"]:
            props = ", ".join("%s:%s" % (p["name"], p["type"]) for p in vm["properties"]) or "no properties"
            out.append('  "%s": %s' % (vm["name"], props))
    if model["assets"]:
        out.append("")
        out.append("Embedded assets")
        for a in model["assets"]:
            out.append("  %-10s %-28s %10s%s" % (a["type"], a["name"], _kb(a["bytes"]) if a["bytes"] else "(not embedded)", "  cdn" if a["cdn"] else ""))
    
    sections = wiring(path, model, framework=framework)
    for title, lines in sections:
        if lines:
            out.append("")
            out.append("Wire it (%s):" % title)
            out.extend("  " + line for line in lines)
    out.append("")
    if not issues:
        out.append("OK  no issues")
    else:
        for issue in issues:
            out.append("  %s %s  %s" % (SYMBOL[issue["severity"]], issue["code"], issue["message"]))
            if issue["hint"]:
                out.append("      %s" % issue["hint"])
    return "\n".join(out)
    out.append("")
    if not issues:
        out.append("OK  no issues")
    else:
        for issue in issues:
            out.append("  %s %s  %s" % (SYMBOL[issue["severity"]], issue["code"], issue["message"]))
            if issue["hint"]:
                out.append("      %s" % issue["hint"])
    return "\n".join(out)


def dump(parsed):
    out = []
    for index, (type_key, props, offset) in enumerate(parsed["objects"]):
        shown = {}
        for key, value in props.items():
            if isinstance(value, bytes):
                value = "<%d bytes>" % len(value)
            elif isinstance(value, float):
                value = round(value, 4)
            shown[key] = value
        out.append("#%-5d @%-7d %-28s %s" % (index, offset, TYPE_NAMES.get(type_key, "type %d" % type_key), shown))
    return "\n".join(out)


# -- cli --------------------------------------------------------------------
def inspect_file(path):
    data = path.read_bytes()
    try:
        parsed = parse(data)
        truncated = None
    except Malformed as exc:
        return None, [{"code": "RV001", "severity": ERROR, "message": str(exc),
                       "hint": "The runtime would reject this file (\"Problem loading file; may be corrupt!\"). "
                               "Re-export it; a partial upload or a git LFS pointer are the usual causes."}], len(data)
    model = build(parsed["objects"])
    issues = lint(parsed, model, len(data))
    return (parsed, model), issues, len(data)


# The 140-byte file the Rive CLI builds for `rive create`: one artboard, one
# background fill, one animation, one state machine with one layer.
_FIXTURE = bytes.fromhex(
    "52495645070300c401ec010000000000170001c40100ec0100070000fa43080000fa4304"
    "08417274626f61726400" "14040a4261636b67726f756e64050000" "122528282828ff0405436f6c6f72050100"
    "1f370b416e696d6174696f6e203100" "35370f5374617465204d616368696e65203100"
    "398a01074c617965722031003e0040003f00419701030" "03d95010000"
)


def self_test():
    parsed = parse(_FIXTURE)
    assert (parsed["major"], parsed["minor"]) == (7, 3), parsed
    assert parsed["toc"] == {196: 0, 236: 0}, parsed["toc"]
    model = build(parsed["objects"])
    ab, = model["artboards"]
    assert ab["name"] == "Artboard" and (ab["width"], ab["height"]) == (500.0, 500.0), ab
    assert [a["name"] for a in ab["animations"]] == ["Animation 1"], ab["animations"]
    assert ab["animations"][0]["frames"] == 60 and ab["animations"][0]["loop"] == "one-shot"
    sm, = ab["stateMachines"]
    assert sm["name"] == "State Machine 1" and sm["layers"] == ["Layer 1"], sm
    assert sm["states"] == 4 and sm["transitions"] == 1 and sm["inputs"] == [], sm
    assert ab["defaultStateMachine"] == "State Machine 1", ab["defaultStateMachine"]
    codes = {i["code"] for i in lint(parsed, model, len(_FIXTURE))}
    assert codes == {"RV005"}, codes
    for cut in (3, 9, 40, 139):
        try:
            parse(_FIXTURE[:cut])
        except Malformed:
            continue
        raise AssertionError("truncation at %d bytes was not detected" % cut)
    print("self-test OK")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect and lint Rive (.riv) binaries.")
    parser.add_argument("paths", nargs="*", help=".riv files")
    parser.add_argument("-f", "--framework", choices=["react", "vue", "svelte", "web", "flutter", "swiftui", "android", "react-native", "all"], default="react",
                        help="Target framework for copy-paste runtime wiring (default: react)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--dump", action="store_true", help="print every object in the file")
    parser.add_argument("--quiet", action="store_true", help="only print files with issues")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if not args.paths:
        parser.print_usage(sys.stderr)
        return 2

    failed = False
    payload = []
    for index, raw in enumerate(args.paths):
        path = Path(raw)
        if not path.is_file():
            print("rive_lint: no such file: %s" % path, file=sys.stderr)
            return 2
        result, issues, size = inspect_file(path)
        blocking = any(i["severity"] == ERROR for i in issues)
        failed = failed or blocking
        if args.json:
            entry = {"file": str(path), "bytes": size, "ok": not blocking, "issues": issues}
            if result:
                parsed, model = result
                entry.update({"version": "%d.%d" % (parsed["major"], parsed["minor"]), **{k: v for k, v in model.items()}})
            payload.append(entry)
            continue
        if args.quiet and not issues:
            continue
        if index and not args.quiet:
            print("\n" + "=" * 72 + "\n")
        if result is None:
            print("%s  %s" % (path.name, _kb(size)))
            for issue in issues:
                print("  %s %s  %s\n      %s" % (SYMBOL[issue["severity"]], issue["code"], issue["message"], issue["hint"]))
            continue
        parsed, model = result
        if args.dump:
            print(dump(parsed))
            print()
        print(report(path, size, parsed, model, issues, framework=args.framework))
    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

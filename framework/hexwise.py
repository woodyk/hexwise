"""Hexwise v0.1: provider-neutral candidate protocol and bounded smoke evaluator.

No generated machine code is executed on the host. Python standard library only.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = "hexwise/0.1"
PROFILE = "aarch64-leaf-u64-add-v1"
MASK = (1 << 64) - 1


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected),
            "object fields must be exactly: " + ", ".join(expected))


def decode(value):
    require(type(value) is str and re.fullmatch(r"(?:[0-9a-f]{2})+", value) is not None,
            "hex must be nonempty lowercase byte pairs without separators")
    require(len(value) <= 8192, "payload exceeds 4096 bytes")
    return bytes.fromhex(value)


def validate_task(task):
    keys(task, ["protocol", "task_id", "operation", "target_profile", "requirement",
                "addend", "base_sha256", "max_bytes"])
    require(task["protocol"] == VERSION, "unsupported protocol")
    require(type(task["task_id"]) is str and bool(task["task_id"]), "missing task id")
    require(task["operation"] in ("create", "update"), "unsupported operation")
    require(task["target_profile"] == PROFILE, "unsupported target profile")
    require(type(task["requirement"]) is str and bool(task["requirement"]), "missing requirement")
    require(type(task["addend"]) is int and 0 <= task["addend"] <= MASK, "invalid u64 addend")
    require(type(task["max_bytes"]) is int and 4 <= task["max_bytes"] <= 4096
            and task["max_bytes"] % 4 == 0, "invalid instruction byte budget")
    if task["operation"] == "create":
        require(task["base_sha256"] is None, "create must have no base hash")
    else:
        require(type(task["base_sha256"]) is str
                and re.fullmatch(r"[0-9a-f]{64}", task["base_sha256"]) is not None,
                "update requires an exact base hash")


def materialize(task, candidate, base=None):
    """Validate binding and patch preconditions; return bytes without writing files."""
    validate_task(task)
    common = ["protocol", "task_id", "target_profile", "task_sha256", "operation"]
    keys(candidate, common + (["hex"] if task["operation"] == "create" else ["edits"]))
    for field in ("protocol", "task_id", "target_profile", "operation"):
        require(candidate[field] == task[field], "candidate mismatch: " + field)
    require(candidate["task_sha256"] == digest(canonical(task)), "task hash mismatch")
    if task["operation"] == "create":
        require(base is None, "create does not accept a base")
        result = decode(candidate["hex"])
    else:
        require(type(base) is bytes and digest(base) == task["base_sha256"], "base hash mismatch")
        require(len(base) <= task["max_bytes"] and len(base) % 4 == 0, "invalid base size")
        edits = candidate["edits"]
        require(type(edits) is list and 0 < len(edits) <= 1024, "invalid edits list")
        result = bytearray(base)
        previous_end = 0
        for edit in edits:
            keys(edit, ["offset", "before", "after"])
            offset = edit["offset"]
            require(type(offset) is int and offset >= previous_end and offset % 4 == 0,
                    "edits must be sorted, aligned and non-overlapping")
            before, after = decode(edit["before"]), decode(edit["after"])
            require(len(before) == len(after) and len(before) % 4 == 0,
                    "v0.1 patches replace whole instructions without changing length")
            end = offset + len(before)
            require(end <= len(base), "edit outside base")
            require(base[offset:end] == before, "expected bytes mismatch")
            result[offset:end] = after
            previous_end = end
        result = bytes(result)
    require(len(result) <= task["max_bytes"] and len(result) % 4 == 0,
            "candidate exceeds byte budget or instruction alignment")
    return result


def inspect_payload(data):
    """Recognize only ADD X0,X0,#imm12 (unshifted) followed by RET X30.

    This deliberately tiny interpreter is a protocol smoke test, not an ISA emulator.
    Unknown instructions, early returns, branches, memory and system calls fail closed.
    """
    require(bool(data) and len(data) % 4 == 0, "invalid instruction alignment")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    require(words[-1] == 0xD65F03C0, "missing final RET X30")
    immediates = []
    for word in words[:-1]:
        require(word & 0xFFC003FF == 0x91000000, "instruction outside smoke profile")
        immediates.append((word >> 10) & 0xFFF)
    return immediates


def evaluate(task, data):
    validate_task(task)
    immediates = inspect_payload(data)
    # Fixed evaluator-owned cases. Public smoke cases, never advertised as held out.
    inputs = [0, 1, 2, 4095, 4096, (1 << 32)-1, 1 << 32, (1 << 63)-1,
              1 << 63, MASK-1, MASK]
    failures = []
    for value in inputs:
        actual = value
        for immediate in immediates:
            actual = (actual + immediate) & MASK
        expected = (value + task["addend"]) & MASK
        if actual != expected:
            failures.append({"input": value, "expected": expected, "actual": actual})
    return {"evaluator": "restricted-interpreter/0.1", "status": "fail" if failures else "pass",
            "cases": len(inputs), "failures": failures,
            "claim_scope": "public smoke cases under restricted instruction semantics",
            "native_execution": "not_run", "executable_container": "not_applicable"}


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 1024 * 1024, "JSON document exceeds 1 MiB")
    return json.loads(raw, object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task")
    parser.add_argument("candidate", nargs="?")
    parser.add_argument("--base")
    parser.add_argument("--out", help="new output directory; existing paths are refused")
    parser.add_argument("--task-hash", action="store_true")
    args = parser.parse_args()
    try:
        task = load(args.task)
        validate_task(task)
        if args.task_hash:
            print(digest(canonical(task)))
            return 0
        require(args.candidate is not None and args.out is not None, "candidate and --out are required")
        candidate = load(args.candidate)
        base = Path(args.base).read_bytes() if args.base else None
        data = materialize(task, candidate, base)
        report = {"protocol": VERSION, "task_sha256": digest(canonical(task)),
                  "candidate_manifest_sha256": digest(canonical(candidate)),
                  "base_sha256": task["base_sha256"], "artifact_sha256": digest(data),
                  "artifact_bytes": len(data), "structural_status": "pass"}
        try:
            report["behavior"] = evaluate(task, data)
        except ValueError as error:
            report["behavior"] = {"status": "unsupported", "reason": str(error),
                                  "native_execution": "not_run"}
        output = Path(args.out)
        output.mkdir(parents=True, exist_ok=False)
        (output / "candidate.bin").write_bytes(data)
        (output / "task.json").write_bytes(canonical(task) + b"\n")
        (output / "candidate.json").write_bytes(canonical(candidate) + b"\n")
        if base is not None:
            (output / "base.bin").write_bytes(base)
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0 if report["behavior"]["status"] == "pass" else 1
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

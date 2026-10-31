# tools/frost_ceremony.py — the coordinator's tool
import subprocess, json, hashlib, os
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

CEREMONY_TOOL = "/usr/local/bin/frost-dkg"  # hash-verified at start

@dataclass
class CeremonyState:
    ceremony_id: str
    threshold: int
    max_signers: int
    participants: list[str]          # participant IDs, e.g. ["P1", "P2", "P3", "P4", "P5"]
    round1_hashes: dict[str, str]    # participant -> hash
    round1_all_hash: str = ""
    round2_hashes: dict[str, dict[str, str]] = {}  # sender -> recipient -> hash
    complaints: list[dict] = None
    group_pubkey: str = ""
    status: str = "initialised"

    def __post_init__(self):
        if self.complaints is None:
            self.complaints = []

    def save(self, path: Path):
        path.write_text(json.dumps(asdict(self), indent=2, default=str))

# ── Setup ──────────────────────────────────────────────────────────────────

def init_ceremony(threshold: int, max_signers: int,
                  participants: list[str]) -> CeremonyState:
    if len(participants) != max_signers:
        raise ValueError("participants count must equal max_signers")
    if not (2 <= threshold <= max_signers):
        raise ValueError("threshold must be 2..max_signers")
    return CeremonyState(
        ceremony_id=f"dkg-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        threshold=threshold, max_signers=max_signers,
        participants=participants,
    )

# ── Round 1: collect commitments from participants ──────────────────────────

def collect_round1(state: CeremonyState, incoming_dir: Path, out: Path):
    """Called by coordinator after participants place their round1 files."""
    for pid in state.participants:
        f = incoming_dir / f"round1-{pid}.json"
        if not f.exists():
            raise RuntimeError(f"missing round1 from {pid}")
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        state.round1_hashes[pid] = h

    # Verify all hashes against what was read aloud in the room
    for pid, expected in state.round1_hashes.items():
        read_aloud = input(f"Paste read-aloud hash for {pid} (or 'skip'): ").strip()
        if read_aloud and read_aloud != expected:
            raise RuntimeError(f"hash mismatch for {pid}: {read_aloud} != {expected}")

    # Merge via the ceremony tool
    inputs = [str(incoming_dir / f"round1-{pid}.json") for pid in state.participants]
    r = subprocess.run(
        [CEREMONY_TOOL, "coordinator", "round1-merge",
         "--inputs", *inputs, "--output", str(out / "round1-all.json")],
        capture_output=True, text=True, check=True,
    )
    state.round1_all_hash = hashlib.sha256((out / "round1-all.json").read_bytes()).hexdigest()
    state.status = "round1-complete"
    return r.stdout

# ── Round 2: route shares ───────────────────────────────────────────────────

def route_round2(state: CeremonyState, incoming_dir: Path, out: Path):
    """Called after participants place their round2 output files."""
    by_recipient = {pid: [] for pid in state.participants}

    for sender in state.participants:
        state.round2_hashes[sender] = {}
        for recipient in state.participants:
            f = incoming_dir / f"round2-{sender}-to-{recipient}.json"
            if not f.exists():
                state.complaints.append({"from": recipient, "against": sender,
                                          "reason": "missing"})
                continue
            state.round2_hashes[sender][recipient] = hashlib.sha256(f.read_bytes()).hexdigest()
            by_recipient[recipient].append(f)

    # Route to each recipient
    for recipient, files in by_recipient.items():
        dest = out / "routed" / recipient
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            (dest / f.name).write_bytes(f.read_bytes())

    if state.complaints:
        state.status = "round2-complaints"
    else:
        state.status = "round2-routed"
    return by_recipient

# ── Finalise ───────────────────────────────────────────────────────────────

def finalise(state: CeremonyState, incoming_dir: Path, out: Path):
    """Called after participants place their finalised share files."""
    if state.complaints:
        raise RuntimeError("unresolved complaints — cannot finalise")

    shares = []
    group_keys = set()
    for pid in state.participants:
        f = incoming_dir / f"participant-{pid}-share.json"
        if not f.exists():
            raise RuntimeError(f"missing finalised share from {pid}")
        share = json.loads(f.read_text())
        shares.append(str(f))
        group_keys.add(share["group_public_key"])

    if len(group_keys) != 1:
        raise RuntimeError(
            f"group public key mismatch across participants: {group_keys}"
        )
    state.group_pubkey = group_keys.pop()

    # Verify via ceremony tool
    r = subprocess.run(
        [CEREMONY_TOOL, "verify-group",
         "--participant-shares", *shares,
         "--expected-threshold", str(state.threshold)],
        capture_output=True, text=True, check=True,
    )
    state.status = "complete"
    return r.stdout

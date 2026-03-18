#!/usr/bin/env python3
"""Seed initial glossary with storage/network technical terms."""

INITIAL_TERMS = [
    ("journal", "journal", True),
    ("pool", "pool", True),
    ("fabric", "fabric", True),
    ("LDEV", "LDEV", True),
    ("HUR", "HUR", True),
    ("GAD", "GAD", True),
    ("ShadowImage", "ShadowImage", True),
    ("TrueCopy", "TrueCopy", True),
    ("quorum", "quorum", True),
    ("snapshot", "snapshot", True),
    ("thin provisioning", "thin provisioning", True),
    ("deduplication", "deduplication", True),
    ("RAID", "RAID", True),
    ("LUN", "LUN", True),
    ("iSCSI", "iSCSI", True),
    ("fibre channel", "fibre channel", True),
    ("NVMe", "NVMe", True),
    ("SSD", "SSD", True),
    ("throughput", "is hacmi", False),
    ("latency", "gecikme", False),
    ("bandwidth", "bant genisligi", False),
    ("replication", "replikasyon", False),
    ("failover", "failover", True),
    ("switchover", "switchover", True),
]


def main():
    print(f"Seeding {len(INITIAL_TERMS)} glossary terms...")

    import csv
    import sys

    writer = csv.writer(sys.stdout)
    writer.writerow(["source_term", "target_term", "do_not_translate"])
    for source, target, dnt in INITIAL_TERMS:
        writer.writerow([source, target, str(dnt).lower()])

    print(f"\nDone. {len(INITIAL_TERMS)} terms ready for import.", file=sys.stderr)


if __name__ == "__main__":
    main()

import argparse
import sys

from agentwatch_a.trace_store import validate_trace_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AgentWatch-A canonical traces.")
    parser.add_argument("--input", "-i", type=str, default="tests/fixtures/tiny_synthetic_traces.jsonl", help="Path to JSONL trace file.")
    args = parser.parse_args()

    total, valid, errors = validate_trace_file(args.input)
    if errors:
        print(f"[-] Validation FAILED for {args.input}")
        print(f"    Valid traces: {valid}/{total}")
        for err in errors[:10]:
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more errors")
        return 1
    else:
        print(f"[+] Validation PASSED for {args.input}")
        print(f"    All {valid}/{total} traces strictly conform to Section 6.1 and Appendix A.")
        return 0

if __name__ == "__main__":
    sys.exit(main())

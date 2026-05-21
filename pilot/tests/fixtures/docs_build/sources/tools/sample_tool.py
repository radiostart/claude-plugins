#!/usr/bin/env python3
"""
sample_tool — docs_build 의 tool 변환 검증용.

요약 한 줄.
"""
import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="sample_tool",
        description="샘플 도구.",
    )
    parser.add_argument("--mode", choices=["a", "b"], default="a")
    args = parser.parse_args()
    print(f"mode={args.mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

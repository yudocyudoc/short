"""CLI local: python -m arena.cli prepare|validate|adjudicate ..."""
import argparse
from .core import load_json, save_json, view_for_lane, seal_submission, adjudicate, LANES


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("case")
    prep.add_argument("lane", choices=LANES)
    prep.add_argument("output")
    val = commands.add_parser("validate")
    val.add_argument("visible")
    val.add_argument("submission")
    val.add_argument("output")
    adj = commands.add_parser("adjudicate")
    adj.add_argument("visible")
    adj.add_argument("sealed")
    adj.add_argument("output")
    opts = parser.parse_args()
    if opts.command == "prepare":
        output = view_for_lane(load_json(opts.case), opts.lane)
    elif opts.command == "validate":
        output = seal_submission(load_json(opts.submission), load_json(opts.visible))
    else:
        output = adjudicate(load_json(opts.visible), load_json(opts.sealed))
    save_json(opts.output, output)


if __name__ == "__main__":
    main()

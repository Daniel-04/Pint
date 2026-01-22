import sys
import os
from .parse_papers import parse_papers


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "config.csv"

    if not os.path.isfile(filename):
        print(f"Error: config file '{filename}' not found.")
        print(f"Usage: python -m {__package__} <config.csv>")
        sys.exit(1)

    parse_papers(filename)


if __name__ == "__main__":
    main()

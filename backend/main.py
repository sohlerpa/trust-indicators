import sys
import json
from factcheck import FactCheckManager


def main():
    if len(sys.argv) < 2:
        print("Bitte eine Behauptung angeben.")
        print('Beispiel:')
        print('  python main.py "Deutschland hat 84 Millionen Einwohner"')
        sys.exit(1)

    claim = " ".join(sys.argv[1:])
    manager = FactCheckManager()
    result = manager.factcheck(claim)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


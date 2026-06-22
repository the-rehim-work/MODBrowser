"""Bir dəfə işlədin: AdGuard + EasyList siyahılarını filters/ qovluğuna yükləyir."""

import urllib.request
from pathlib import Path

_DEST = Path(__file__).resolve().parent.parent / "filters"

_LISTS = {
  "adguard_base.txt": "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_2_Base/filter.txt",
  "adguard_tracking.txt": "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_3_Spyware/filter.txt",
  "easylist.txt": "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block.txt",
}


def main() -> None:
  _DEST.mkdir(parents=True, exist_ok=True)
  for name, url in _LISTS.items():
    target = _DEST / name
    try:
      with urllib.request.urlopen(url, timeout=30) as response:
        target.write_bytes(response.read())
      print(f"OK  {name}  ({target.stat().st_size} bayt)")
    except Exception as exc:
      print(f"XETA  {name}  -> {exc}")


if __name__ == "__main__":
  main()

"""mojibake 된 조건식 이름을 실제 한글로 디코드해서 출력."""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOG_PATH = Path(sys.argv[1])
text = LOG_PATH.read_text(encoding="utf-8", errors="replace")

pattern = re.compile(r"\[(\d{3})\]\s+(\S.+?)\s+→")
seen = []
for m in pattern.finditer(text):
    idx, raw = m.group(1), m.group(2).strip()
    try:
        decoded = raw.encode("latin1").decode("cp949")
    except Exception:
        decoded = raw
    seen.append((idx, decoded))

for idx, name in seen:
    print(f"  [{idx}] {name}")
print(f"-- 총 {len(seen)}개")

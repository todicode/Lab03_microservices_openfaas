"""Generate self-contained handlers for the official python3-http-debian template."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
for name, module in (("product-service", "product_service"), ("order-service", "order_service"),
                     ("total-calculator", "total_calculator")):
    target = ROOT / ".generated" / name
    target.mkdir(parents=True, exist_ok=True)
    for source in ("common", module):
        shutil.copyfile(ROOT / "services" / (source + ".py"), target / (source + ".py"))
    (target / "handler.py").write_text(f"from .{module} import handle\n", encoding="utf-8")
    (target / "requirements.txt").write_text("psycopg[binary]==3.2.10\nrequests==2.32.5\n", encoding="utf-8")
    print("Prepared", name)

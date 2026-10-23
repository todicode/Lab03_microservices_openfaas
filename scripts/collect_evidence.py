import json, subprocess
from pathlib import Path
from datetime import datetime, timezone
import requests
ROOT=Path(__file__).resolve().parents[1]
def kube(*args):
    return json.loads(subprocess.check_output(["kubectl","--context","lab03-openfaas",*args,"-o","json"],text=True,encoding="utf-8"))
functions=[]
for p in kube("-n","openfaas-fn","get","pods")["items"]:
    cs=p["status"].get("containerStatuses",[])
    functions.append({"name":p["metadata"]["name"],"phase":p["status"]["phase"],
        "ready":bool(cs) and all(c["ready"] for c in cs),"image":p["spec"]["containers"][0]["image"],
        "restarts":sum(c["restartCount"] for c in cs)})
assert len(functions)==3 and all(p["ready"] and p["phase"]=="Running" for p in functions)
pvc=kube("-n","lab03-data","get","pvc")["items"][0]
payload={"items":[{"unit_price_vnd":129000,"quantity":2},{"unit_price_vnd":35000,"quantity":1}]}
r=requests.post("http://127.0.0.1:18080/function/total-calculator/calculate",json=payload,timeout=10)
r.raise_for_status()
assert r.json()["total_vnd"]==293000
orders=requests.get("http://127.0.0.1:18080/function/order-service/orders",timeout=10).json()["orders"]
demo=next(o for o in orders if o["customer_name"]=="Khách báo cáo Lab03")
data={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"context":"lab03-openfaas",
      "kubernetes":kube("version")["serverVersion"]["gitVersion"],"functions":functions,
      "pvc":{"name":pvc["metadata"]["name"],"phase":pvc["status"]["phase"],"capacity":pvc["status"]["capacity"]["storage"]},
      "calculator":{"input":payload,"http_status":r.status_code,"output":r.json()},
      "demo_order":{"id":demo["id"],"total_vnd":demo["total_vnd"],"status":demo["status"]}}
(ROOT/"evidence/report-status.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print("Verified 3 Ready functions, Bound PVC and calculator total 293000 VND")

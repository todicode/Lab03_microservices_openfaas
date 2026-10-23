"""Verify anonymous Docker Hub pull access without reading any stored credentials."""
import json
from pathlib import Path
import requests
root=Path(__file__).resolve().parents[1]
results=[]
for name in ("product-service","order-service","total-calculator"):
    repo="giabaonguyentran/lab03-"+name
    token_response=requests.get("https://auth.docker.io/token",params={"service":"registry.docker.io","scope":"repository:"+repo+":pull"},timeout=30)
    token_response.raise_for_status()
    token=token_response.json()["token"]
    response=requests.get("https://registry-1.docker.io/v2/"+repo+"/manifests/1.0.0",
        headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json"},timeout=30)
    ok=response.status_code==200
    results.append({"image":"docker.io/"+repo+":1.0.0","anonymous_pull":ok,"digest":response.headers.get("Docker-Content-Digest","")})
    print(repo+": anonymous pull "+("OK" if ok else str(response.status_code)),flush=True)
path=root/"evidence/dockerhub-public.json"
path.write_text(json.dumps(results,indent=2),encoding="utf-8")
if not all(x["anonymous_pull"] for x in results):
    raise SystemExit("One or more image repositories are not public.")

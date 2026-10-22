"""Fetch the exact official OpenFaaS Python template commit used by this lab."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
commit = "7d886f47e60232b0ee9002a64b6af2ef02589b74"
repo = root / ".tools" / "template-source"
repo.mkdir(parents=True, exist_ok=True)
if not (repo / ".git").exists():
    subprocess.run(["git","init",str(repo)],check=True)
subprocess.run(["git","-C",str(repo),"fetch","--depth","1",
                "https://github.com/openfaas/python-flask-template.git",commit],check=True)
subprocess.run(["git","-C",str(repo),"checkout","--detach","FETCH_HEAD"],check=True)
name = "python3-http-debian"
shutil.copytree(repo / "template" / name, root / "template" / name, dirs_exist_ok=True)
print("Official template ready at commit",commit)

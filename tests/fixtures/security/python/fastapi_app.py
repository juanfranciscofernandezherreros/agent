# Corpus: FastAPI (parámetros de ruta y Depends).
import subprocess
from fastapi import Depends, FastAPI

app = FastAPI()


def get_db():
    return None


@app.get("/report/{name}")
def report(name: str, page: int = 1, db=Depends(get_db)):
    subprocess.run(f"generate-report {name}", shell=True)  # expect: SEC-CMDI
    subprocess.run(f"generate-report --page {page}", shell=True)
    return {"ok": True}

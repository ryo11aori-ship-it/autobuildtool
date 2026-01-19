# app/utils.py
from pathlib import Path
import shutil

def safe_rm_tree(p: Path):
    if p.exists() and p.is_dir():
        shutil.rmtree(p)
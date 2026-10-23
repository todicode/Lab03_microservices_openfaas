"""Use the packaged PNG renderer with a PDF exported by Microsoft Word.

The Windows bundled runtime does not include LibreOffice. This adapter changes
only the PDF conversion step, preserving the skill renderer's rasterization.
"""
from pathlib import Path
import importlib.util
import os
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
os.environ['PATH']=str(RUNTIME/'native/poppler/Library/bin')+os.pathsep+os.environ['PATH']
renderer=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents/26.1022.11436/skills/documents/render_docx.py'
spec=importlib.util.spec_from_file_location('report_renderer',renderer)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source=ROOT/'reports/Bao_cao_Lab03_OpenFaaS.pdf'
def word_pdf(doc_path,user_profile,convert_tmp_dir,stem,verbose=False):
    target=Path(convert_tmp_dir)/(stem+'.pdf')
    shutil.copy2(source,target)
    return str(target),'PDF exported by Microsoft Word COM'
module.convert_to_pdf=word_pdf
sys.argv=[str(renderer),str(source.with_suffix('.docx')),'--output_dir',str(ROOT/'reports/qa'),'--dpi','130']
module.main()

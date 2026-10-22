"""CP42 (A2 Tests 2; review item T6 in EVIDENCE/CP31d_INTEGRITY_REVIEW.md): every reference test file can be
imported on its own. A file that imports a repo module at top level must put the repo root on sys.path first
(sys.path.insert), instead of relying on another test file or the runner having done it. Static check (ast), no
test module is imported."""
import ast, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _is_path_insert(node):
    return (isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
            and node.value.func.attr=='insert' and isinstance(node.value.func.value,ast.Attribute)
            and node.value.func.value.attr=='path' and isinstance(node.value.func.value.value,ast.Name)
            and node.value.func.value.value.id=='sys')

def _repo_module(name):
    top=name.split('.')[0]
    return (ROOT/f'{top}.py').is_file() or (ROOT/top/'__init__.py').is_file()

def late_repo_imports(path):
    """Top-level imports of repo modules that come before any top-level sys.path.insert(...)."""
    found=[]
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
        if _is_path_insert(node): return found
        names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module and not node.level else []
        found+=[(node.lineno,n) for n in names if _repo_module(n)]
    return found

class StandaloneImports(unittest.TestCase):
    def test_every_test_file_sets_the_path_before_repo_imports(self):
        bad={f.name:late_repo_imports(f) for f in sorted((ROOT/'tests').glob('test_*.py'))}
        self.assertEqual({k:v for k,v in bad.items() if v},{})
        self.assertGreater(len(bad),40)

if __name__=='__main__':
    unittest.main()

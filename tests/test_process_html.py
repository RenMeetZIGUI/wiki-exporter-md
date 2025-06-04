import types
import sys
import importlib.util
from pathlib import Path

import pytest

class DummyWidget:
    def __init__(self, *a, **k):
        pass
    def grid(self, *a, **k):
        pass
    def pack(self, *a, **k):
        pass
    def config(self, *a, **k):
        pass

def load_process_html(monkeypatch):
    fake_tk = types.ModuleType('tkinter')

    class DummyTk(DummyWidget):
        def title(self, *a, **k):
            pass
        def geometry(self, *a, **k):
            pass
        def resizable(self, *a, **k):
            pass
        def after(self, delay, func=None):
            if func:
                func()
        def mainloop(self, *a, **k):
            pass

    fake_tk.Tk = DummyTk
    fake_tk.Frame = DummyWidget
    fake_tk.Button = DummyWidget
    fake_tk.Label = DummyWidget
    fake_tk.Entry = DummyWidget
    fake_tk.Radiobutton = DummyWidget
    fake_tk.StringVar = lambda value=None: types.SimpleNamespace(get=lambda: value, set=lambda v: None)
    fake_tk.BOTH = 'both'
    fake_tk.messagebox = types.SimpleNamespace(showwarning=lambda *a, **k: None)

    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    path = Path(__file__).resolve().parents[1] / 'wiki_gui.py'
    spec = importlib.util.spec_from_file_location('wiki_gui', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.process_html


def test_process_html_anchor_and_footnote(tmp_path, monkeypatch):
    process_html = load_process_html(monkeypatch)
    html = (
        '<div id="mw-content-text">'
        '<p><a href="#section">Section</a></p>'
        '<p><a href="#cite_note-1">[1]</a></p>'
        '</div>'
    )
    out = process_html('Test', html, 'en', output_dir=str(tmp_path))
    content = (tmp_path / 'Test.md').read_text(encoding='utf-8')
    assert '**Section**' in content
    assert '$^{1}$' in content

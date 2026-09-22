import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
OPERATOR = ROOT / "identity" / "chrome_extension_v1_6" / "lab_dom_operator_v16.js"
FIXTURE = ROOT / "identity" / "chrome_extension_v1_6" / "lab_operator_fixture.html"


@unittest.skipUnless(shutil.which("node"), "Node is required for LAB DOM contract tests")
class LabDomOperatorTests(unittest.TestCase):
    def node(self, script):
        proc = subprocess.run(["node", "-e", script, str(OPERATOR)], capture_output=True,
                              text=True, timeout=10, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_js_syntax(self):
        proc = subprocess.run(["node", "--check", str(OPERATOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_exact_local_fixture_only(self):
        self.node(r'''
const assert=require("node:assert/strict");
const {verifyLabFixture:f}=require(process.argv[1]);
const origin="http://127.0.0.1:8765";
assert.equal(f(origin+"/lab/operator-fixture",origin),true);
for(const url of [
 "https://example.com/lab/operator-fixture",
 "http://localhost:8765/lab/operator-fixture",
 "http://127.0.0.1:8766/lab/operator-fixture",
 origin+"/lab/operator-fixture?q=1",
 origin+"/lab/operator-fixture#frag",
 origin+"/lab/other"
]) assert.equal(f(url,origin),false,url);
assert.equal(f(origin+"/lab/operator-fixture","https://example.com"),false);
''')

    def test_click_type_select_read_complete_on_local_fixture(self):
        self.node(r'''
const assert=require("node:assert/strict");
const {executeLabFixture:execute}=require(process.argv[1]);
global.Event=class Event {constructor(t,o){this.type=t;this.bubbles=o.bubbles}};
const elements={
 "#cerebro-lab-name":{tagName:"INPUT",type:"text",value:"",dispatchEvent(e){this.inputEvent=e.type}},
 "#cerebro-lab-role":{tagName:"SELECT",options:[{value:""},{value:"AUDITOR"}],value:"",dispatchEvent(e){this.changeEvent=e.type}},
 "#cerebro-lab-toggle":{tagName:"BUTTON",pressed:"false",getAttribute(k){return this.pressed},
   click(){this.pressed="true";elements["#cerebro-lab-output"].textContent=
     elements["#cerebro-lab-name"].value+" / "+elements["#cerebro-lab-role"].value+" / ON"}},
 "#cerebro-lab-output":{tagName:"OUTPUT",textContent:"WAITING"}
};
const doc={title:"CEREBRO OPERATOR LAB",querySelector:s=>elements[s]};
const r=execute(doc,"http://127.0.0.1:8765/lab/operator-fixture","http://127.0.0.1:8765");
assert.equal(r.status,"COMPLETED");
for(const k of ["click_verified","type_verified","select_verified","read_verified"])assert.equal(r[k],true,k);
assert.equal(r.external_mutation_performed,false);
assert.equal(r.secret_value_included,false);
assert.equal(elements["#cerebro-lab-name"].inputEvent,"input");
assert.equal(elements["#cerebro-lab-role"].changeEvent,"change");
''')

    def test_wrong_origin_or_dom_never_mutates(self):
        self.node(r'''
const assert=require("node:assert/strict");
const {executeLabFixture:execute}=require(process.argv[1]);
let count=0;
const doc={title:"CEREBRO OPERATOR LAB",querySelector(){count++;return null}};
let r=execute(doc,"https://other.example/lab/operator-fixture","http://127.0.0.1:8765");
assert.equal(r.decision,"FIXTURE_ORIGIN_MISMATCH");
assert.equal(count,0);
r=execute(doc,"http://127.0.0.1:8765/lab/operator-fixture","http://127.0.0.1:8765");
assert.equal(r.decision,"FIXTURE_DOM_MISMATCH");
assert.equal(r.external_mutation_performed,false);
''')

    def test_fixture_is_static_local_and_has_no_form(self):
        s = FIXTURE.read_text(encoding="utf-8")
        self.assertIn('id="cerebro-lab-name"', s)
        self.assertIn('id="cerebro-lab-toggle"', s)
        for forbidden in ("<form", "fetch(", "XMLHttpRequest", "document.cookie",
                          "type=\"password\"", "localStorage", "https://"):
            self.assertNotIn(forbidden, s)
        source = OPERATOR.read_text(encoding="utf-8")
        for forbidden in ("fetch(", "chrome.cookies", "document.cookie", ".submit(",
                          "window.open", "eval("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

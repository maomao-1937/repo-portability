import json, pathlib, shutil, subprocess, sys, tempfile, unittest
SCRIPT=pathlib.Path(__file__).resolve().parents[1].joinpath('repo_portability.py')
class PortabilityTests(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); self.root=pathlib.Path(self.t.name)
 def tearDown(self): self.t.cleanup()
 def cli(self,*args): return subprocess.run([sys.executable,str(SCRIPT),str(self.root),*map(str,args),'--format','json'],capture_output=True,text=True)
 def paths(self,paths,*args):
  p=self.root/'paths.json'; p.write_text(json.dumps(paths)); return self.cli('--paths-file',p,*args)
 def test_clean(self): self.assertEqual(self.paths(['src/main.py','README.md']).returncode,0)
 def test_reserved(self):
  r=self.paths(['CON.txt','a/NUL','COM1.log']); self.assertEqual(r.returncode,1); self.assertIn('reserved_device',r.stdout)
 def test_superscript_reserved_device(self):
  r=self.paths(['COM\u00b9.txt','LPT\u00b2.log','COM\u00b3']); self.assertEqual(r.returncode,1); self.assertEqual(len(json.loads(r.stdout)['findings']),3)
 def test_invalid_chars(self):
  r=self.paths(['bad?.txt','line\n.txt','trail.','space ']); self.assertEqual(r.returncode,1); self.assertIn('invalid_character',r.stdout); self.assertIn('trailing_dot_or_space',r.stdout)
 def test_directory_case_collision(self):
  r=self.paths(['Src/a.py','src/b.py']); self.assertEqual(r.returncode,1); self.assertIn('case_collision',r.stdout)
 def test_file_directory_collision(self):
  r=self.paths(['a','A/file']); self.assertEqual(r.returncode,1); self.assertIn('file_directory_collision',r.stdout)
 def test_max_length(self): self.assertEqual(self.paths(['longname'],'--max-path',3).returncode,1)
 def test_traversal(self): self.assertEqual(self.paths(['../x']).returncode,2)
 def test_absolute(self): self.assertEqual(self.paths(['C:/x']).returncode,2)
 def test_empty_component(self): self.assertEqual(self.paths(['a//b']).returncode,2)
 def test_directory_skips_symlinks_and_dependencies(self):
  (self.root/'node_modules').mkdir(); (self.root/'node_modules'/'bad.').write_text('x'); (self.root/'normal.py').write_text('x'); self.assertEqual(self.cli('--directory').returncode,0)
 def test_git(self):
  if not shutil.which('git'): self.skipTest('git unavailable')
  subprocess.run(['git','init','-q',str(self.root)],check=True,capture_output=True); (self.root/'normal.py').write_text('x'); subprocess.run(['git','-C',str(self.root),'add','normal.py'],check=True,capture_output=True); r=self.cli(); self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(json.loads(r.stdout)['checked_paths'],1)
 def test_unc_rejected(self): self.assertEqual(self.paths(['\\server\\share']).returncode,2)
 def test_not_git(self): self.assertEqual(self.cli().returncode,2)
 def test_directory_symlink(self):
  (self.root/'safe').mkdir(); (self.root/'safe'/'normal.py').write_text('x')
  try: (self.root/'alias').symlink_to(self.root/'safe',target_is_directory=True)
  except OSError: self.skipTest('symlink privilege unavailable')
  r=self.cli('--directory'); self.assertEqual(r.returncode,0); self.assertEqual(json.loads(r.stdout)['checked_paths'],1)
 def test_help(self): self.assertEqual(subprocess.run([sys.executable,str(SCRIPT),'--help'],capture_output=True).returncode,0)
if __name__=='__main__': unittest.main()

import subprocess, os, shutil, threading

from string import Template
from textwrap import dedent
import nbformat

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import uvicorn
import webbrowser, time


class WebFrontend:

    def __init__(self, quiz, web_dir = None):
        self.quiz = quiz
        self.voila = None
        self.tmp_dir = 'tmp_dir'

        self.web_dir = web_dir or 'pyrope/web'
        self.app = FastAPI()
        self.api_host = "0.0.0.0"
        self.api_port = 8000
        self._setup_api()

        self.debug = False

# ------ Rest API ------

    def _setup_api(self):
        self.app.mount("/static", StaticFiles(directory = os.path.join(self.web_dir, 'static')), name="static")

    # Root-Endpunkt: Liefert einfach eine HTML-Datei
        @self.app.get("/")
        def root():
            return FileResponse(os.path.join(self.web_dir, 'index.html'))
        @self.app.get("/structure")
        def get_structure():
            return self._build_structure(self.quiz)
    
    def _start_api(self):
        uvicorn.run(self.app, host=self.api_host, port=self.api_port, log_level="info")

    def _build_structure(self, quiz):
        from pyrope.core import Exercise, Quiz

        structure = {
            "title": quiz.title,
            "navigation": quiz.navigation,
            "weights": quiz.weights,
            "select": quiz.select,
            "shuffle": quiz.shuffle,
            "items": []
        }

        count_exercises = 0
        count_quizzes = 0

        for item in quiz:
            if isinstance(item, Exercise):
                structure["items"].append(f'{count_exercises}_{item.__class__.__name__}.ipynb')
                count_exercises += 1
            elif isinstance(item, Quiz):
                sub_structure = self._build_structure(item)
                sub_structure["title"] = item.title or f'{count_quizzes}_subquiz'
                structure["items"].append(sub_structure)
                count_quizzes += 1

        return structure
        
# ------ Voila/Notebooks ------  

    def _build_notebook_dir(self, quiz, dir, path='', baseweight=1):
        from pyrope.core import Exercise, Quiz

        os.makedirs(dir, exist_ok=True)
        count_exercises = 0
        count_quizzes = 0

        for item in quiz:
            if isinstance(item, Exercise):

                name = item.__class__.__name__
                module = item.__class__.__module__

                nb = nbformat.v4.new_notebook()

                file_name = f'{count_exercises}_{name}'

                path_id = f"{path}/{file_name}"
                
                weight = quiz.weights.get(count_exercises+count_quizzes, 1) * baseweight
                
                tmpl = Template(dedent("""\
                import sys, os, json
                import ipywidgets as widgets
                from IPython.display import Javascript, display
                sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
                from $module import $name
                id = $path_id
                outputspace = widgets.Output()
                display(outputspace)

                def postresult(score, max_score):
                    message = {"type": "results", "id": $path_id, "score": score, "maxScore": max_score}
                    js_code = "window.parent.postMessage(" + json.dumps(message) + ", '*');"
                    with outputspace:
                        display(Javascript(js_code))

                $name(weights=$weight).run(callback=postresult, debug=$debug)
                """))

                code = tmpl.substitute(
                    module=module,
                    name=name,
                    path_id=repr(path_id),
                    weight=repr(weight),
                    debug=repr(self.debug),
                )
                
                nb['cells'] = [nbformat.v4.new_code_cell(code)]

                file = f'{file_name}.ipynb'
                with open(os.path.join(dir, file), 'w') as f:
                    nbformat.write(nb, f)

                count_exercises += 1

            elif isinstance(item, Quiz):
                quiz_name = item.title or f'{count_quizzes}_subquiz'
                subdir = os.path.join(dir, quiz_name)
                next_weight = quiz.weights.get(count_exercises+count_quizzes, 1) * baseweight
                self._build_notebook_dir(item, subdir, f'{path}/{quiz_name}', next_weight)

                count_quizzes += 1

    def _open_voila(self):
        
        settings_str = (
            "{"
            "  'headers': {"
            "    'Content-Security-Policy': \"frame-ancestors 'self' *\""
            "  }, "
            "  'disable_check_xsrf': True"
            "}"
        )
            
        process = subprocess.Popen([
            "voila",
            "tmp_dir",
            "--no-browser",
            "--port=8866",
            "--Voila.ip=0.0.0.0",
            f"--Voila.tornado_settings={settings_str}"
        ])
        return process

# ------ Put it all together ------

    def run(self):
        try:
            self._build_notebook_dir(self.quiz, self.tmp_dir)
            self.api_thread = threading.Thread(target=self._start_api, daemon=True)
            self.api_thread.start()

            self.voila = self._open_voila()

            time.sleep(1)
            webbrowser.open_new_tab(f'http://{self.api_host}:{self.api_port}/')
            self.voila.wait()

        except KeyboardInterrupt:
            print('KeyboardInterrupt received, stopping the server.')
            if self.voila:
                self.voila.terminate()

            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)
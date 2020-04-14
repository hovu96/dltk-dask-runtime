import os
import sys

sys.path.insert(0, os.getenv('DLTK_API_DIR'))

from notebook.services.contents.largefilemanager import LargeFileManager
import jupyterlab_server
import tornado.web
import logging
import urllib

# parameters: #https://github.com/jupyter/notebook/blob/master/notebook/notebookapp.py

notebook_name = "Algo.ipynb"
notebook_version_name = "Algo.version"
notebook_dir = os.getenv('NOTEBOOK_PATH', "/notebooks")
notebook_file_path = os.path.join(notebook_dir, notebook_name)
notebook_version_file = os.path.join(notebook_dir, notebook_version_name)

client_url = os.getenv("CLIENT_URL", "")


class FitHandler(tornado.web.RequestHandler):
    def post(self):
        self.write("fit")


class ApplyHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("apply")


class NotebookHandler(tornado.web.RequestHandler):
    def check_xsrf_cookie(self):
        pass

    def get(self):
        try:
            with open(notebook_file_path, 'r') as f:
                source = f.read()
        except FileNotFoundError:
            source = None
        try:
            with open(notebook_version_file, 'r') as f:
                version = f.read()
        except FileNotFoundError:
            version = -1
        if source is None:
            self.set_status(404)
            return
        self.set_header('X-Notebook-Version', version)
        self.write(source)

    def put(self):
        version = self.request.headers['X-Notebook-Version']
        source = self.request.body.decode()
        with open(notebook_file_path, "w") as f:
            f.write(source)
        with open(notebook_version_file, "w") as f:
            f.write(version)


def generate_deployment_code(model):
    # https://jupyter-notebook.readthedocs.io/en/stable/extending/savehooks.html
    if model['type'] != 'notebook':
        return
    # only run on nbformat v4
    if model['content']['nbformat'] != 4:
        return
    source = ""
    for cell in model['content']['cells']:
        if cell['cell_type'] != 'code':
            continue
        cell_source = cell['source']
        source += cell_source + "\r\n"
    return source


class DaskFileManager(LargeFileManager):
    def save(self, model, path):
        absolute_path = os.path.join(notebook_dir, path.strip("/"))
        is_algo = absolute_path == notebook_file_path
        if is_algo:
            if os.path.exists(absolute_path):
                with open(notebook_file_path, 'r') as f:
                    old_algo_source = f.read()
            else:
                old_algo_source = ""
        result = super().save(model, path)
        if is_algo:
            with open(notebook_file_path, 'r') as f:
                new_algo_source = f.read()
            if new_algo_source != old_algo_source:
                try:
                    with open(notebook_version_file, 'r') as f:
                        version = int(f.read())
                except FileNotFoundError:
                    version = 0
                version += 1
                with open(notebook_version_file, "w") as f:
                    f.write("%s" % version)
                print("increased source code version number to %s" % version)
                deployment_code = generate_deployment_code(model)
                master_code_url = urllib.parse.urljoin(client_url, "code")
                upload_request = urllib.request.Request(
                    master_code_url,
                    data=deployment_code.encode(),
                    method="PUT",
                    headers={
                        "Content-Type": "text/plain",
                        "X-Code-Version": version,
                    }
                )
                urllib.request.urlopen(upload_request)
                print("sent algorithm code to master (version %s)" % version)
        return result


class DaskApp(jupyterlab_server.LabServerApp):
    def start(self):
        self.web_app.add_handlers('.*$', [
            (r"/_dltk/fit", FitHandler),
            (r"/_dltk/apply", ApplyHandler),
            (r"/_dltk/notebook", NotebookHandler),
        ])
        super().start()


if __name__ == "__main__":
    DaskApp.launch_instance(
        port=os.getenv('PORT', 8888),
        open_browser=False,
        root_dir=notebook_dir,
        allow_root=True,
        default_url="/notebooks/%s" % notebook_name,
        # base_url='/jupyterlab/',
        # debug=False,
        token="",
        # password=os.environ.get('HASHED_PWD'),
        ip="0.0.0.0",
        disable_check_xsrf=True,
        contents_manager_class=DaskFileManager
    )

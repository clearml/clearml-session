import base64
import json
import os
import shutil
import socket
import subprocess
import sys
from copy import deepcopy
import getpass
from functools import partial
from tempfile import mkstemp, gettempdir, mkdtemp
from threading import Thread
from time import sleep, time
import datetime
from uuid import uuid4
import tarfile
import platform

import psutil
import requests
from clearml import Task, StorageManager
from clearml.backend_api import Session
from clearml.backend_api.services import tasks
from pathlib import Path

# noinspection SpellCheckingInspection
default_ssh_fingerprint = {
    'ssh_host_ecdsa_key':
        r"-----BEGIN EC PRIVATE KEY-----"+"\n"
        r"MHcCAQEEIOCAf3KEN9Hrde53rqQM4eR8VfCnO0oc4XTEBw0w6lCfoAoGCCqGSM49"+"\n"
        r"AwEHoUQDQgAEn/LlC/1UN1q6myfjs03LJdHY2LB0b1hBjAsLvQnDMt8QE6Rml3UF"+"\n"
        r"QK/UFw4mEqCFCD+dcbyWqFsKxTm6WtFStg=="+"\n"
        r"-----END EC PRIVATE KEY-----"+"\n",

    'ssh_host_ed25519_key':
        r"-----BEGIN OPENSSH PRIVATE KEY-----"+"\n"
        r"b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW"+"\n"
        r"QyNTUxOQAAACDvweeJHnUKtwY7/WRqDJEZTDk8AajWKFt/BXmEI3+A8gAAAJiEMTXOhDE1"+"\n"
        r"zgAAAAtzc2gtZWQyNTUxOQAAACDvweeJHnUKtwY7/WRqDJEZTDk8AajWKFt/BXmEI3+A8g"+"\n"
        r"AAAEBCHpidTBUN3+W8s3qRNkyaJpA/So4vEqDvOhseSqJeH+/B54kedQq3Bjv9ZGoMkRlM"+"\n"
        r"OTwBqNYoW38FeYQjf4DyAAAAEXJvb3RAODQ1NmQ5YTdlYTk4AQIDBA=="+"\n"
        r"-----END OPENSSH PRIVATE KEY-----"+"\n",

    'ssh_host_rsa_key':
        r"-----BEGIN RSA PRIVATE KEY-----"+"\n"
        r"MIIEowIBAAKCAQEAs8R3BrinMM/k9Jak7UqsoONqLQoasYgkeBVOOfRJ6ORYWW5R"+"\n"
        r"WLkYnPPUGRpbcoM1Imh7ODBgKzs0mh5/j3y0SKP/MpvT4bf38e+QGjuC+6fR4Ah0"+"\n"
        r"L5ohGIMyqhAiBoXgj0k2BE6en/4Rb3BwNPMocCTus82SwajzMNgWneRC6GCq2M0n"+"\n"
        r"0PWenhS0IQz7jUlw3JU8z6T3ROPiMBPU7ubBhiNlAzMYPr76Z7J6ZNrCclAvdGkI"+"\n"
        r"YxK7RNq0HwfoUj0UFD9iaEHswDIlNc34p93lP6GIAbh7uVYfGhg4z7HdBoN2qweN"+"\n"
        r"szo7iQX9N8EFP4WfpLzNFteThzgN/bdso8iv0wIDAQABAoIBAQCPvbF64110b1dg"+"\n"
        r"p7AauVINl6oHd4PensCicE7LkmUi3qsyXz6WVfKzVVgr9mJWz0lGSQr14+CR0NZ/"+"\n"
        r"wZE393vkdZWSLv2eB88vWeH8x8c1WHw9yiS1B2YdRpLVXu8GDjh/+gdCLGc0ASCJ"+"\n"
        r"3fsqq5+TBEUF6oPFbEWAsdhryeAiFAokeIVEKkxRnIDvPCP6i0evUHAxEP+wOngu"+"\n"
        r"4XONkixNmATNa1jP2YAjmh3uQbAf2BvDZuywJmqV8fqZa/BwuK3W+R/92t0ySZ5Q"+"\n"
        r"Z7RCZzPzFvWY683/Cfx5+BH3XcIetbcZ/HKuc+TdBvvFgqrLNIJ4OXMp3osjZDMO"+"\n"
        r"YZIE6DdBAoGBAOG8cgm2N+Kl2dl0q1r4S+hf//zPaDorNasvcXJcj/ypy1MdmDXt"+"\n"
        r"whLSAuTN4r8axgbuws2Z870pIGd28koqg78U+pOPabkphloo8Fc97RO28ZJCK2g0"+"\n"
        r"/prPgwSYymkhrvwdzIbI11BPL/rr9cLJ1eYDnzGDSqvXJDL79XxrzwMzAoGBAMve"+"\n"
        r"ULkfqaYVlgY58d38XruyCpSmRSq39LTeTYRWkJTNFL6rkqL9A69z/ITdpSStEuR8"+"\n"
        r"8MXQSsPz8xUhFrA2bEjW7AT0r6OqGbjljKeh1whYOfgGfMKQltTfikkrf5w0UrLw"+"\n"
        r"NQ8USfpwWdFnBGQG0yE/AFknyLH14/pqfRlLzaDhAoGAcN3IJxL03l4OjqvHAbUk"+"\n"
        r"PwvA8qbBdlQkgXM3RfcCB1LeVrB1aoF2h/J5f+1xchvw54Z54FMZi3sEuLbAblTT"+"\n"
        r"irbyktUiB3K7uli90uEjqLfQEVEEYxYcN0uKNsIucmJlG6nKmZnSDlWJp+xS9RH1"+"\n"
        r"4QvujNMYgtMPRm60T4GYAAECgYB6J9LMqik4CDUls/C2J7MH2m22lk5Zg3JQMefW"+"\n"
        r"xRvK3XtxqFKr8NkVd3U2k6yRZlcsq6SFkwJJmdHsti/nFCUcHBO+AHOBqLnS7VCz"+"\n"
        r"XSkAqgTKFfEJkCOgl/U/VJ4ZFcz7xSy1xV1yf4GCFK0v1lsJz7tAsLLz1zdsZARj"+"\n"
        r"dOVYYQKBgC3IQHfd++r9kcL3+vU7bDVU4aKq0JFDA79DLhKDpSTVxqTwBT+/BIpS"+"\n"
        r"8z79zBTjNy5gMqxZp/SWBVWmsO8d7IUk9O2L/bMhHF0lOKbaHQQ9oveCzIwDewcf"+"\n"
        r"5I45LjjGPJS84IBYv4NElptRk/2eFFejr75xdm4lWfpLb1SXPOPB"+"\n"
        r"-----END RSA PRIVATE KEY-----"+"\n",

    'ssh_host_rsa_key__pub':
        r'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCzxHcGuKcwz+T0lqTtSqyg42otChqxiCR4FU459Eno5FhZblFYuRic89QZGlt'
        r'ygzUiaHs4MGArOzSaHn+PfLRIo/8ym9Pht/fx75AaO4L7p9HgCHQvmiEYgzKqECIGheCPSTYETp6f/hFvcHA08yhwJO6zzZLBqPM'
        r'w2Bad5ELoYKrYzSfQ9Z6eFLQhDPuNSXDclTzPpPdE4+IwE9Tu5sGGI2UDMxg+vvpnsnpk2sJyUC90aQhjErtE2rQfB+hSPRQUP2Jo'
        r'QezAMiU1zfin3eU/oYgBuHu5Vh8aGDjPsd0Gg3arB42zOjuJBf03wQU/hZ+kvM0W15OHOA39t2yjyK/T',
    'ssh_host_ecdsa_key__pub':
        r'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ/y5Qv9VDdaupsn47NNyyXR2Niwd'
        r'G9YQYwLC70JwzLfEBOkZpd1BUCv1BcOJhKghQg/nXG8lqhbCsU5ulrRUrY=',
    'ssh_host_ed25519_key__pub': None,
}
config_section_name = 'interactive_session'
config_object_section_ssh = 'SSH'
config_object_section_bash_init = 'interactive_init_script'
artifact_workspace_name = "workspace"
sync_runtime_property = "workspace_sync_ts"
sync_workspace_creating_id = "created_by_session"
__poor_lock = []
__allocated_ports = []


def get_free_port(range_min, range_max):
    global __allocated_ports
    used_ports = [i.laddr.port for i in psutil.net_connections()]
    port = next(i for i in range(range_min, range_max) if i not in used_ports and i not in __allocated_ports)
    __allocated_ports.append(port)
    return port


def _get_env_vars(*var_names, default=None):
    for var_name in var_names:
        value = os.environ.get(var_name, "").strip()
        if value:
            print(f"Using value from {var_name}: {value}")
            return value
    return default


def init_task(param, a_default_ssh_fingerprint):
    # initialize ClearML
    Task.add_requirements('jupyter')
    Task.add_requirements('jupyterlab')
    Task.add_requirements('jupyterlab_git')
    task = Task.init(
        project_name="DevOps",
        task_name="Allocate Jupyter Notebook Instance",
        task_type=Task.TaskTypes.service
    )

    # Add jupyter server base folder
    if Session.check_min_api_version('2.13'):
        param.pop('user_key', None)
        param.pop('user_secret', None)
        param.pop('ssh_password', None)
        task.connect(param, name=config_section_name)
        # noinspection PyProtectedMember
        runtime_prop = dict(task._get_runtime_properties())
        # remove the user key/secret the moment we have it
        param['user_key'] = runtime_prop.pop('_user_key', None)
        param['user_secret'] = runtime_prop.pop('_user_secret', None)
        # no need to reset, we will need it
        param['ssh_password'] = runtime_prop.get('_ssh_password')
        # Force removing properties
        # noinspection PyProtectedMember
        task._edit(runtime=runtime_prop)
        task.reload()
    else:
        task.connect(param, name=config_section_name)

    # connect ssh fingerprint configuration (with fallback if section is missing)
    old_default_ssh_fingerprint = deepcopy(a_default_ssh_fingerprint)
    found_server_ssh_fingerprint = None
    if Session.check_min_api_version('2.20'):
        print("INFO: checking remote ssh server fingerprint from server vault")
        # noinspection PyBroadException
        try:
            res = task.session.send_request(
                "users", "get_vaults",
                params="enabled=true&types=remote_session_ssh_server&"
                       "types=remote_session_ssh_server").json()
            if res.get('data', {}).get('vaults'):
                found_server_ssh_fingerprint = json.loads(res['data']['vaults'][-1]['data'])
                a_default_ssh_fingerprint.update(found_server_ssh_fingerprint)
                print("INFO: loading fingerprint from server vault successfully: {}".format(
                    list(found_server_ssh_fingerprint.keys())))
            else:
                print("INFO: server side fingerprint was not found")
        except Exception as ex:
            print("DEBUG: server side fingerprint parsing error: {}".format(ex))

    if not found_server_ssh_fingerprint:
        try:
            # print("DEBUG: loading fingerprint from task")
            task.connect_configuration(configuration=a_default_ssh_fingerprint, name=config_object_section_ssh)
        except (TypeError, ValueError):
            a_default_ssh_fingerprint.clear()
            a_default_ssh_fingerprint.update(old_default_ssh_fingerprint)

    if param.get('default_docker') and task.running_locally():
        task.set_base_docker("{} --network host".format(param['default_docker']))

    # leave local process, only run remotely
    task.execute_remotely()
    return task


def setup_os_env(param, preserve_env_suffix=None):
    # get rid of all the runtime ClearML
    if preserve_env_suffix is None:
        preserve_env_suffix = (
            "_API_HOST",
            "_WEB_HOST",
            "_FILES_HOST",
            "_CONFIG_FILE",
            "_API_ACCESS_KEY",
            "_API_SECRET_KEY",
            "_API_HOST_VERIFY_CERT",
            "_DOCKER_IMAGE",
            "_DOCKER_BASH_SCRIPT",
        )
    # set default docker image, with network configuration
    if param.get('default_docker', '').strip():
        os.environ["CLEARML_DOCKER_IMAGE"] = param['default_docker'].strip()

    # setup os environment
    env = deepcopy(os.environ)
    for key in os.environ:
        # only set CLEARML_ remove any TRAINS_
        if key.startswith("TRAINS") or (
                key.startswith("CLEARML") and not any(key.endswith(p) for p in preserve_env_suffix)):
            env.pop(key, None)

    return env


def monitor_jupyter_server(fd, local_filename, process, task, jupyter_port, hostnames, param):
    # todo: add auto spin down see: https://tljh.jupyter.org/en/latest/topic/idle-culler.html
    # print stdout/stderr
    prev_line_count = 0
    process_running = True
    if param and param.get("jupyter_token") is not None or param.get("jupyter_password") is not None:
        token = param.get("jupyter_token") or param.get("jupyter_password") or True
    else:
        token = None

    port = None
    tic = time()
    # if more than 30 sec passed, we give up just break
    while process_running and time() - tic < 31:
        process_running = False
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process_running = True

        # noinspection PyBroadException
        try:
            with open(local_filename, "rt") as f:
                # read new lines
                new_lines = f.readlines()
                if not new_lines:
                    continue
            os.lseek(fd, 0, 0)
            os.ftruncate(fd, 0)
        except Exception:
            continue

        print("".join(new_lines))
        prev_line_count += len(new_lines)

        # update task with jupyter notebook server links (port / token)
        line = ''
        for line in new_lines:
            if "http://" not in line and "https://" not in line:
                continue
            parts = line.split('?token=', 1)
            if not token:
                if len(parts) != 2:
                    continue
                token = parts[1]
            port = parts[0].split(':')[-1]
            # try to cast to int
            try:
                port = int(port)  # noqa
            except (TypeError, ValueError):
                continue
            break

        # we could not locate the token, try again
        if not token or not port:
            continue

        # we ignore the reported port, because jupyter server will get confused
        # if we have multiple servers running and will point to the wrong port/server
        task.set_parameter(name='properties/jupyter_port', value=str(jupyter_port))
        if token and token != True:
            jupyter_url = '{}://{}:{}?token={}'.format(
                'https' if "https://" in line else 'http', hostnames, jupyter_port, token)
        else:
            jupyter_url = '{}://{}:{}'.format('https' if "https://" in line else 'http', hostnames, jupyter_port)
            token = ""

        # update the task with the correct links and token
        if Session.check_min_api_version("2.13"):
            # noinspection PyProtectedMember
            runtime_prop = task._get_runtime_properties()
            runtime_prop['_jupyter_token'] = str(token)
            runtime_prop['_jupyter_url'] = str(jupyter_url)
            # noinspection PyProtectedMember
            task._set_runtime_properties(runtime_prop)
        else:
            task.set_parameter(name='properties/jupyter_token', value=str(token))
            task.set_parameter(name='properties/jupyter_url', value=jupyter_url)

        print('\nJupyter Lab URL: {}\n'.format(jupyter_url))
        # if we got here, we have a token and we can leave
        break

    return process


def start_vscode_server(hostname, hostnames, param, task, env, bind_ip="127.0.0.1", port=None):
    if not param.get("vscode_server"):
        return

    # get vscode version and python extension version
    # they are extremely flaky, this combination works, most do not.
    vscode_version = '4.103.1'
    python_ext_version = '2025.12.0'
    if param.get("vscode_version"):
        vscode_version_parts = param.get("vscode_version").split(':')
        vscode_version = vscode_version_parts[0]
        if len(vscode_version_parts) > 1:
            python_ext_version = vscode_version_parts[1]

    # make a copy of env and remove the pythonpath from it.
    env = dict(**env)
    env.pop('PYTHONPATH', None)

    # example of CLEARML_SESSION_VSCODE_PY_EXT value
    # 'https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-python/vsextensions/python/2022.12.0/vspackage'
    # (see https://marketplace.visualstudio.com/items?itemName=ms-python.python).
    python_ext_download_link = os.environ.get("CLEARML_SESSION_VSCODE_PY_EXT")

    # example of CLEARML_SESSION_VSCODE_SERVER_DEB value
    # 'https://github.com/coder/code-server/releases/download/v4.96.2/code-server_4.96.2_amd64.deb'
    # (see https://github.com/coder/code-server/releases)

    code_server_deb_download_link = \
        os.environ.get("CLEARML_SESSION_VSCODE_SERVER_DEB") or \
        os.environ.get("CLEARML_SESSION_VSCODE_SERVER_TGZ") or \
        'https://github.com/coder/code-server/releases/download/v{version}/code-server-{version}'

    if platform.machine() == "aarch64":
        platform_type = "arm64"
    else:
        platform_type = "amd64"

    # support x86/arm dnf/deb
    if (not code_server_deb_download_link.endswith(".deb") and not code_server_deb_download_link.endswith(".rpm")
            and not code_server_deb_download_link.endswith(".tar.gz") and not code_server_deb_download_link.endswith(".tgz")):
        code_server_deb_download_link += "-linux-{}.tar.gz".format(platform_type)

    is_vscode_tgz = code_server_deb_download_link.endswith(".tar.gz") or code_server_deb_download_link.endswith(".tgz")
    pre_installed = False
    python_ext = None

    base_path = Path.home() / ".local" 
    base_vscode_ext_dir = base_path / "share" / "code-server"

    # find a free tcp port
    port = get_free_port(9000, 9100) if not port else int(port)

    # check if preinstalled
    # noinspection PyBroadException
    try:
        vscode_path = shutil.which("code-server")
        if vscode_path:
            print("INFO: found existing vscode code-server at ({}) using it".format(vscode_path))
    except Exception:
        vscode_path = None

    if not vscode_path:
        # installing VSCODE:
        try:
            python_ext = StorageManager.get_local_copy(
                python_ext_download_link.format(python_ext_version),
                extract_archive=False) if python_ext_download_link else None
            download_url = code_server_deb_download_link.format(version=vscode_version)
            code_server_dl = StorageManager.get_local_copy(download_url, extract_archive=False)
            if not code_server_dl:
                raise ValueError("Failed downloading vscode-server: {}".format(download_url))
            
            if is_vscode_tgz:
                def extract_tar(base_path):
                    base_vscode_ext_dir = base_path / "share" / "code-server"
                    base_vscode_ext_dir.mkdir(parents=True, exist_ok=True)
                    target_path = base_path / "bin" /"code-server"
                    target_path.mkdir(parents=True, exist_ok=True)
                    with tarfile.open(code_server_dl, "r:gz") as tar:
                        if sys.version_info >= (3, 12):
                            tar.extractall(path=target_path, filter='fully_trusted')
                        else:
                            tar.extractall(path=target_path)
                    return target_path, base_vscode_ext_dir

                try:
                    base_path = Path.home() / ".local" 
                    target_path, base_vscode_ext_dir = extract_tar(base_path)
                    
                except Exception:
                    try:
                        base_path = Path(gettempdir()) / ".clearml.local" 
                        target_path, base_vscode_ext_dir = extract_tar(base_path)
                    except Exception as ex:
                        print("ERROR: FAILED extracting and installing vscode code-server: {}".format(ex))
                        target_path = base_vscode_ext_dir = None

                if not target_path:
                    print("ERROR: FAILED extracting and installing vscode code-server: leaving")
                else:
                    extracted_dir = next(Path(target_path).glob("code-server-{}-linux-{}".format(vscode_version, platform_type)))
                    # add it to path
                    env["PATH"] = os.environ["PATH"] = os.environ.get("PATH", "") + ":{}".format(os.path.join(os.path.abspath(extracted_dir), "bin")) 
            else:
                if shutil.which("dnf") and not shutil.which("dpkg"):
                    os.system("dnf install -y {}".format(code_server_dl))
                else:
                    os.system("dpkg -i {}".format(code_server_dl))

            vscode_path = 'code-server'    
        
        except Exception as ex:
            print("Failed installing vscode server: {}".format(ex))
            vscode_path = None
    
    # check if installed
    if not vscode_path:
        print('Error: Cannot install code-server (not root) and could not find code-server executable, skipping.')
        task.set_parameter(name='properties/vscode_port', value=str(-1))
        return

    cwd = (
        os.path.expandvars(os.path.expanduser(param["user_base_directory"]))
        if param["user_base_directory"]
        else os.getcwd()
    )
    # make sure we have the needed cwd
    # noinspection PyBroadException
    try:
        Path(cwd).mkdir(parents=True, exist_ok=True)
    except Exception:
        print("Warning: failed setting user base directory [{}] reverting to ~/".format(cwd))
        cwd = os.path.expanduser("~/")

    print("Running VSCode Server on {} [{}] port {} at {}".format(hostname, hostnames, port, cwd))
    print("VSCode Server available: http://{}:{}/\n".format(hostnames, port))
    user_folder = os.path.expanduser(
        _get_env_vars(
            "CLEARML_VSCODE_USER_DATA_DIR",
            "CLEARML_SESSION_VSCODE_USER_DATA_DIR",
            default=os.path.join(cwd, ".vscode/user/"),
        )
    )
    exts_folder = os.path.expanduser(
        _get_env_vars(
            "CLEARML_VSCODE_EXTENSIONS_DIR",
            "CLEARML_SESSION_VSCODE_EXTENSIONS_DIR",
            default=os.path.join(cwd, ".vscode/exts/"),
        )
    )
    proc = None

    try:
        fd, local_filename = mkstemp()
        if pre_installed:
            user_folder = os.path.expanduser(
                _get_env_vars(
                    "CLEARML_VSCODE_USER_DATA_DIR",
                    "CLEARML_SESSION_VSCODE_USER_DATA_DIR",
                    default=base_vscode_ext_dir.as_posix(),
                )
            )
            if not os.path.isdir(user_folder):
                user_folder = None
                exts_folder = None
            else:
                exts_folder = os.path.expanduser(
                    _get_env_vars(
                        "CLEARML_VSCODE_EXTENSIONS_DIR",
                        "CLEARML_SESSION_VSCODE_EXTENSIONS_DIR",
                        default=(base_vscode_ext_dir / "extensions").as_posix(),
                    )
                )
        else:
            vscode_extensions = param.get("vscode_extensions") or ""
            vscode_extensions_cmd = []
            jupyter_ext_version = True
            for ext in vscode_extensions.split(","):
                ext = ext.strip()
                if not ext:
                    continue

                if ext.startswith("ms-python.python"):
                    python_ext_version = python_ext = None
                elif ext.startswith("ms-toolsai.jupyter"):
                    jupyter_ext_version = None

                vscode_extensions_cmd += ["--install-extension", ext]

            if python_ext:
                vscode_extensions_cmd += ["--install-extension", "{}".format(python_ext)]
            elif python_ext_version:
                vscode_extensions_cmd += ["--install-extension", "ms-python.python@{}".format(python_ext_version)]

            if jupyter_ext_version:
                vscode_extensions_cmd += ["--install-extension", "ms-toolsai.jupyter"]

            print("VScode extensions: {}".format(vscode_extensions_cmd))
            subprocess.Popen(
                [
                    vscode_path,
                    "--auth",
                    "none",
                    "--bind-addr",
                    "{}:{}".format(bind_ip, port),
                    "--user-data-dir", user_folder,
                    "--extensions-dir", exts_folder,
                ] + vscode_extensions_cmd,
                env=env,
                stdout=fd,
                stderr=fd,
            )

        if user_folder:
            # set user level configuration
            settings = Path(os.path.expanduser(os.path.join(user_folder, 'User/settings.json')))
            settings.parent.mkdir(parents=True, exist_ok=True)
            # noinspection PyBroadException
            try:
                with open(settings.as_posix(), 'rt') as f:
                    base_json = json.load(f)
            except Exception:
                base_json = {}
            # noinspection PyBroadException
            try:
                # Notice we are Not using "python.defaultInterpreterPath": sys.executable,
                # because for some reason it breaks the auto python interpreter setup
                base_json.update({
                    "extensions.autoCheckUpdates": False,
                    "extensions.autoUpdate": False,
                    "python.pythonPath": sys.executable,
                    "terminal.integrated.shell.linux": "/bin/bash" if Path("/bin/bash").is_file() else None,
                    "security.workspace.trust.untrustedFiles": "open",
                    # "security.workspace.trust.startupPrompt": "never",
                    "security.workspace.trust.enabled": False,
                    "telemetry.telemetryLevel": "off",
                })
                with open(settings.as_posix(), 'wt') as f:
                    json.dump(base_json, f)
            except Exception:
                pass

            # set machine level configuration
            settings = Path(os.path.expanduser(os.path.join(user_folder, 'Machine/settings.json')))
            settings.parent.mkdir(parents=True, exist_ok=True)
            # noinspection PyBroadException
            try:
                with open(settings.as_posix(), 'rt') as f:
                    base_json = json.load(f)
            except Exception:
                base_json = {}

            # noinspection PyBroadException
            try:
                # "python.defaultInterpreterPath" is a machine level setting
                base_json.update({
                    "python.defaultInterpreterPath": sys.executable,
                })
                with open(settings.as_posix(), 'wt') as f:
                    json.dump(base_json, f)
            except Exception:
                pass

        proc = subprocess.Popen(
            ['bash', '-c',
             '{} --auth none --bind-addr {}:{} --disable-update-check {} {}'.format(
                 vscode_path, bind_ip, port,
                 '--user-data-dir \"{}\"'.format(user_folder) if user_folder else '',
                 '--extensions-dir \"{}\"'.format(exts_folder) if exts_folder else '')],
            env=env,
            stdout=fd,
            stderr=fd,
            cwd=cwd,
        )

        try:
            error_code = proc.wait(timeout=1)
            raise ValueError("code-server failed starting, return code {}".format(error_code))
        except subprocess.TimeoutExpired:
            pass

    except Exception as ex:
        print('Failed running vscode server: {}'.format(ex))
        task.set_parameter(name='properties/vscode_port', value=str(-1))
        return

    task.set_parameter(name='properties/vscode_port', value=str(port))
    return proc


def start_jupyter_server(hostname, hostnames, param, task, env, bind_ip="127.0.0.1", port=None):
    if not param.get('jupyterlab', True):
        return

    # execute jupyter notebook
    fd, local_filename = mkstemp()
    cwd = (
        os.path.expandvars(os.path.expanduser(param["user_base_directory"]))
        if param["user_base_directory"]
        else os.getcwd()
    )

    # find a free tcp port
    port = get_free_port(8888, 9000) if not port else int(port)

    # if we are not running as root, make sure the sys executable is in the PATH
    env = dict(**env)
    env['PATH'] = '{}:{}'.format(Path(sys.executable).parent.as_posix(), env.get('PATH', ''))

    try:
        # set default shell to bash if not defined
        if not env.get("SHELL") and shutil.which("bash"):
            env['SHELL'] = shutil.which("bash")
    except Exception as ex:
        print("WARNING: failed finding default shell bash: {}".format(ex))

    # make sure we have the needed cwd
    # noinspection PyBroadException
    try:
        Path(cwd).mkdir(parents=True, exist_ok=True)
    except Exception:
        print("Warning: failed setting user base directory [{}] reverting to ~/".format(cwd))
        cwd = os.path.expanduser("~/")

    # setup jupyter-lab default
    # noinspection PyBroadException
    try:
        settings = Path(os.path.expanduser(
            "~/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/notification.jupyterlab-settings"))
        settings.parent.mkdir(parents=True, exist_ok=True)
        # noinspection PyBroadException
        try:
            with open(settings.as_posix(), 'rt') as f:
                base_json = json.load(f)
        except Exception:
            base_json = {}

        # Notice we are Not using "python.defaultInterpreterPath": sys.executable,
        # because for some reason it breaks the auto python interpreter setup
        base_json.update({
            "checkForUpdates": False,
            "doNotDisturbMode": False,
            "fetchNews": "false"
        })
        with open(settings.as_posix(), 'wt') as f:
            json.dump(base_json, f)
    except Exception as ex:
        print("WARNING: Could not set default jupyter lab settings: {}".format(ex))

    print(
        "Running Jupyter Notebook Server on {} [{}] port {} at {}".format(hostname, hostnames, port, cwd)
    )
    additional_args = [
        "--ServerApp.token='{}'".format(param.get("jupyter_token")) if param.get("jupyter_token") is not None else "",
        "--ServerApp.password=''".format(param.get("jupyter_password")) if param.get("jupyter_password") is not None else "",
        "--ServerApp.allow_origin=*".format(param.get("jupyter_allow_origin")) if param.get("jupyter_allow_origin") is not None else "",
        "--ServerApp.base_url={}".format(param.get("jupyter_base_url")) if param.get("jupyter_base_url") is not None else "",
    ]
    additional_args = [a for a in additional_args if a]

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "jupyter",
            "lab",
            "--no-browser",
            "--allow-root",
            "--ip",
            bind_ip,
            "--port",
            str(port),
        ] + additional_args,
        env=env,
        stdout=fd,
        stderr=fd,
        cwd=cwd,
    )
    return monitor_jupyter_server(fd, local_filename, process, task, port, hostnames, param)


def setup_ssh_server(hostname, hostnames, param, task, env):
    if not param.get("ssh_server"):
        return

    # make sure we do not pass it along to others, work on a copy
    env = deepcopy(env)
    env.pop('LOCAL_PYTHON', None)
    env.pop('PYTHONPATH', None)
    env.pop('DEBIAN_FRONTEND', None)

    print("Installing SSH Server on {} [{}]".format(hostname, hostnames))
    ssh_password = param.get("ssh_password", "training")

    proxy_port = port = None
    ssh_port = None
    if Session.check_min_api_version("2.13"):
        try:
            # noinspection PyProtectedMember
            ssh_port = task._get_runtime_properties().get("internal_tcp_port")
        except Exception as ex:
            print("Failed retrieving internal TCP port for SSH daemon: {}".format(ex))

    # noinspection PyBroadException
    try:
        ssh_port = ssh_port or param.get("ssh_ports") or "10022:15000"
        min_port = int(ssh_port.split(":")[0])
        max_port = max(min_port+32, int(ssh_port.split(":")[-1]))
        port = get_free_port(min_port, max_port)
        if param.get("use_ssh_proxy"):
            proxy_port = port
            port = get_free_port(min_port, max_port)
        else:
            proxy_port = None
        use_dropbear = bool(param.get("force_dropbear", False))

        # if we are root, install open-ssh
        if not use_dropbear and os.geteuid() == 0:
            # noinspection SpellCheckingInspection
            os.system(
                "export PYTHONPATH=\"\" && "
                "([ ! -z $(command -v sshd) ] || "
                "(DEBIAN_FRONTEND=noninteractive apt-get update ; DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server) || "
                "(dnf install -y openssh-server)) && "
                "mkdir -p /var/run/sshd && "
                "echo 'root:{password}' | chpasswd && "
                "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && "
                "sed -i 's|PermitRootLogin prohibit-password|PermitRootLogin yes|g' /etc/ssh/sshd_config && "
                "sed -i 's|session\\s*required\\s*pam_loginuid.so|session optional pam_loginuid.so|g' /etc/pam.d/sshd "
                "&& "  # noqa: W605
                "echo 'ClientAliveInterval 10' >> /etc/ssh/sshd_config && "
                "echo 'ClientAliveCountMax 20' >> /etc/ssh/sshd_config && "
                "echo 'AcceptEnv CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY "
                "CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY' >> /etc/ssh/sshd_config && "
                'echo "export VISIBLE=now" >> /etc/profile && '
                'echo "export PATH=$PATH" >> /etc/profile && '
                'echo "ldconfig" 2>/dev/null >> /etc/profile && '
                'echo "export CLEARML_CONFIG_FILE={clearml_config_file}" >> /etc/profile'.format(
                    password=ssh_password,
                    port=port,
                    clearml_config_file=env.get("CLEARML_CONFIG_FILE") or
                                        os.environ.get("CLEARML_CONFIG_FILE") or os.environ.get("TRAINS_CONFIG_FILE"),
                )
            )
            sshd_path = '/usr/sbin/sshd'
            ssh_config_path = '/etc/ssh/'
            custom_ssh_conf = None
        else:
            # check if sshd exists
            # noinspection PyBroadException
            try:
                os.system(
                    'echo "export PATH=$PATH" >> $HOME/.profile && '
                    'echo "export CLEARML_CONFIG_FILE={clearml_config_file}" >> $HOME/.profile'.format(
                    clearml_config_file=env.get("CLEARML_CONFIG_FILE") or
                                        os.environ.get("CLEARML_CONFIG_FILE") or os.environ.get("TRAINS_CONFIG_FILE"),
                ))
            except Exception:
                print("WARNING: failed setting ~/.profile")

            # check if sshd is preinstalled
            # noinspection PyBroadException
            # try:
            #     # try running SSHd as non-root (currently bypassed, use dropbear instead)
            #     sshd_path = None  ## subprocess.check_output('which sshd', shell=True).decode().strip()
            #     if not sshd_path:
            #         raise ValueError("sshd was not found")
            # except Exception:
            #     print('WARNING: SSHd was not found defaulting to user-space dropbear sshd server')
            #

            # noinspection PyBroadException
            try:
                dropbear_download_link = (os.environ.get("CLEARML_DROPBEAR_EXEC") or
                    'https://github.com/clearml/dropbear/releases/download/DROPBEAR_2025.88/dropbearmulti')

                dropbear = StorageManager.get_local_copy(dropbear_download_link, extract_archive=False)
                try:
                    os.chmod(dropbear, 0o744)
                    if os.system("{} dropbear -V > /dev/null 2>&1".format(dropbear)):
                        raise Exception("dropbear execution failed")
                except Exception:
                    if platform.machine() == "aarch64":
                        dropbear_download_link += "_arm64"
                    else:
                        dropbear_download_link += "_amd64"

                    dropbear = StorageManager.get_local_copy(dropbear_download_link, extract_archive=False)
                    os.chmod(dropbear, 0o744)
                    if os.system("{} dropbear -V > /dev/null 2>&1".format(dropbear)):
                        raise Exception("dropbear execution failed")
                # set to dropbear
                sshd_path = dropbear
                use_dropbear = True
            except Exception:
                print('Error: failed locating SSHd and failed fetching `dropbear`, leaving!')
                return

            # noinspection PyBroadException
            try:
                ssh_config_path = os.path.join(os.getcwd(), '.clearml_session_sshd')
                # noinspection PyBroadException
                try:
                    Path(ssh_config_path).mkdir(parents=True, exist_ok=True)
                except Exception:
                    ssh_config_path = os.path.join(gettempdir(), '.clearml_session_sshd')
                    Path(ssh_config_path).mkdir(parents=True, exist_ok=True)

                custom_ssh_conf = os.path.join(ssh_config_path, 'sshd_config')
                with open(custom_ssh_conf, 'wt') as f:
                    conf = \
                        "PermitRootLogin yes" + "\n"\
                        "ClientAliveInterval 10" + "\n"\
                        "ClientAliveCountMax 20" + "\n"\
                        "AllowTcpForwarding yes" + "\n"\
                        "UsePAM yes" + "\n"\
                        "AuthorizedKeysFile {}".format(os.path.join(ssh_config_path, 'authorized_keys')) + "\n"\
                        "PidFile {}".format(os.path.join(ssh_config_path, 'sshd.pid')) + "\n"\
                        "AcceptEnv CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY "\
                        "CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY"+"\n"
                    for k in default_ssh_fingerprint:
                        filename = os.path.join(ssh_config_path, '{}'.format(k.replace('__pub', '.pub')))
                        conf += "HostKey {}\n".format(filename)

                    f.write(conf)
            except Exception:
                print('Error: Cannot configure sshd, leaving!')
                return

            if not use_dropbear:
                # clear the ssh password, we cannot change it
                ssh_password = None
                task.set_parameter('{}/ssh_password'.format(config_section_name), '')

        # get current user:
        # noinspection PyBroadException
        try:
            current_user = getpass.getuser() or "root"
        except Exception:
            # we failed getting the user, let's assume root
            print("Warning: failed getting active user name, assuming 'root'")
            current_user = "root"

        # create fingerprint files
        Path(ssh_config_path).mkdir(parents=True, exist_ok=True)
        keys_filename = {}
        for k, v in default_ssh_fingerprint.items():
            filename = os.path.join(ssh_config_path, '{}'.format(k.replace('__pub', '.pub')))
            try:
                os.unlink(filename)
            except Exception:  # noqa
                pass
            if v:
                try:
                    with open(filename, 'wt') as f:
                        f.write(v + (' {}@{}'.format(current_user, hostname) if filename.endswith('.pub') else ''))
                    os.chmod(filename, 0o600 if filename.endswith('.pub') else 0o600)
                    keys_filename[k] = filename
                except Exception as ex:
                    print('Warning: failed creating ssh key file {}: {}'.format(filename, ex))

        # run server in foreground so it gets killed with us
        if use_dropbear:
            # convert key files
            dropbear_key_files = []
            for k, ssh_key_file in keys_filename.items():
                # skip over the public keys, there is no need for them
                if not ssh_key_file or ssh_key_file.endswith(".pub"):
                    continue
                drop_key_file = ssh_key_file + ".dropbear"
                try:
                    os.system("{} dropbearconvert openssh dropbear {} {}".format(
                        sshd_path, ssh_key_file, drop_key_file))
                    if Path(drop_key_file).is_file():
                        dropbear_key_files += ["-r", drop_key_file]
                except Exception:
                    pass
            proc_args = [sshd_path, "dropbear", "-e", "-K", "30", "-I", "0", "-F", "-p", str(port)] + dropbear_key_files
            # this is a copy of `env` so there is nothing to worry about
            if ssh_password:
                env["DROPBEAR_CLEARML_FIXED_PASSWORD"] = ssh_password
        else:
            proc_args = [sshd_path, "-D", "-p", str(port)] + (["-f", custom_ssh_conf] if custom_ssh_conf else [])

        proc = subprocess.Popen(args=proc_args, env=env)
        # noinspection PyBroadException
        try:
            result = proc.wait(timeout=1)
        except Exception:
            result = 0

        if result != 0:
            raise ValueError("Failed launching sshd: ", proc_args)

        if proxy_port:
            # noinspection PyBroadException
            try:
                TcpProxy(listen_port=proxy_port, target_port=port, proxy_state={}, verbose=False,  # noqa
                         keep_connection=True, is_connection_server=True)
            except Exception as ex:
                print('Warning: Could not setup stable ssh port, {}'.format(ex))
                proxy_port = None

        if task:
            if proxy_port:
                task.set_parameter(name='properties/internal_stable_ssh_port', value=str(proxy_port))
            task.set_parameter(name='properties/internal_ssh_port', value=str(port))
            # noinspection PyProtectedMember
            task._set_runtime_properties(
                runtime_properties={
                    'internal_ssh_port': str(proxy_port or port),
                    '_ssh_user': current_user,
                }
            )

        print(
            "\n#\n# SSH Server running on {} [{}] port {}\n# LOGIN u:root p:{}\n#\n".format(
                hostname, hostnames, port, ssh_password
            )
        )

    except Exception as ex:
        print("Error: {}\n\n#\n# Error: SSH server could not be launched\n#\n".format(ex))

    return proxy_port or port


def _b64_decode_file(encoded_string):
    # noinspection PyBroadException
    try:
        import gzip
        value = gzip.decompress(base64.decodebytes(encoded_string.encode('ascii'))).decode('utf8')
        return value
    except Exception:
        return None


def setup_user_env(param, task):
    env = setup_os_env(param)

    # create temp config file,
    try:
        fd, local_filename = mkstemp(".clearml.conf")
        os.close(fd)
        from clearml.config import config_obj
        # make sure it's loaded
        config_obj.get("api", None)
        conf_dict = config_obj._config.to_dict()
        conf_dict ={k: v for k, v in conf_dict.items() if k in ("sdk", "api")}
        with open(local_filename, 'wt') as f:
            json.dump(conf_dict, f)
        env["CLEARML_CONFIG_FILE"] = local_filename
    except Exception as ex:
        print("Error [{}]: Failed to store new config file, using original".format(ex))

    # fix casting errors
    if str(param.get("user_key") or "").lower() == "none":
        param["user_key"] = None
    if str(param.get("user_secret") or "").lower() == "none":
        param["user_secret"] = None

    # apply vault if we have it
    vault_environment = {}
    if param.get("user_key") and param.get("user_secret"):
        # noinspection PyBroadException
        try:
            print('Applying vault configuration')
            from clearml.backend_api.session.defs import ENV_ENABLE_ENV_CONFIG_SECTION, ENV_ENABLE_FILES_CONFIG_SECTION
            prev_env, prev_files = ENV_ENABLE_ENV_CONFIG_SECTION.get(), ENV_ENABLE_FILES_CONFIG_SECTION.get()
            ENV_ENABLE_ENV_CONFIG_SECTION.set(True), ENV_ENABLE_FILES_CONFIG_SECTION.set(True)
            prev_envs = deepcopy(os.environ)
            Session(api_key=param.get("user_key"), secret_key=param.get("user_secret"))
            vault_environment = {k: v for k, v in os.environ.items() if prev_envs.get(k) != v}
            if prev_env is None:
                ENV_ENABLE_ENV_CONFIG_SECTION.pop()
            else:
                ENV_ENABLE_ENV_CONFIG_SECTION.set(prev_env)
            if prev_files is None:
                ENV_ENABLE_FILES_CONFIG_SECTION.pop()
            else:
                ENV_ENABLE_FILES_CONFIG_SECTION.set(prev_files)
            if vault_environment:
                print('Vault environment added: {}'.format(list(vault_environment.keys())))
        except Exception as ex:
            print('Applying vault configuration failed: {}'.format(ex))

    # do not change user bash/profile if we are not running inside a container
    if os.geteuid() != 0:
        # check if we are inside a container
        is_container = False
        try:
            with open("/proc/1/sched", "rt") as f:
                lines = f.readlines()
                if lines and lines[0].split()[0] in ("bash", "sh", "zsh"):
                    # this a container
                    is_container = True
        except Exception:  # noqa
            pass

        if not is_container:
            if param.get("user_key") and param.get("user_secret"):
                env['CLEARML_API_ACCESS_KEY'] = param.get("user_key")
                env['CLEARML_API_SECRET_KEY'] = param.get("user_secret")
            return env

    # target source config
    source_conf = '~/.clearmlrc'

    # create symbolic link to the venv
    environment = os.path.expanduser('~/environment')
    # noinspection PyBroadException
    try:
        os.symlink(os.path.abspath(os.path.join(os.path.abspath(sys.executable), '..', '..')), environment)
        print('Virtual environment are available at {}'.format(environment))
    except Exception as e:
        print("Error: Exception while trying to create symlink. The Application will continue...")
        print(e)

    # set default user credentials
    if param.get("user_key") and param.get("user_secret"):
        if param.get("user_key"):
            env['CLEARML_API_ACCESS_KEY'] = param.get("user_key")
            os.system("echo 'export CLEARML_API_ACCESS_KEY=\"{}\"' >> {}".format(
                param.get("user_key").replace('$', '\\$'), source_conf))
        else:
            env.pop('CLEARML_API_ACCESS_KEY', None)
            os.system("echo 'export CLEARML_API_ACCESS_KEY=' >> {}".format(source_conf))

        if param.get("user_secret"):
            env['CLEARML_API_SECRET_KEY'] = param.get("user_secret")
            os.system("echo 'export CLEARML_API_SECRET_KEY=\"{}\"' >> {}".format(
                param.get("user_secret").replace('$', '\\$'), source_conf))
        else:
            env.pop('CLEARML_API_SECRET_KEY', None)
            os.system("echo 'export CLEARML_API_SECRET_KEY=' >> {}".format(source_conf))

    elif os.environ.get("CLEARML_AUTH_TOKEN"):
        env['CLEARML_AUTH_TOKEN'] = os.environ.get("CLEARML_AUTH_TOKEN")
        os.system("echo 'export CLEARML_AUTH_TOKEN=\"{}\"' >> {}".format(
            os.environ.get("CLEARML_AUTH_TOKEN").replace('$', '\\$'), source_conf))

    if param.get("default_docker"):
        os.system("echo 'export CLEARML_DOCKER_IMAGE=\"{}\"' >> {}".format(
            (param.get("default_docker") or "").strip() or (env.get('CLEARML_DOCKER_IMAGE') or ''), source_conf))

    if vault_environment:
        for k, v in vault_environment.items():
            os.system("echo 'export {}={}' >> {}".format(k, "" if v in (None, "") else "\"{}\"".format(v), source_conf))
            env[k] = str(v) if v else ""

    # make sure we activate the venv in the bash
    if Path(os.path.join(environment, 'bin', 'activate')).expanduser().exists():
        os.system("echo 'source {}' >> {}".format(os.path.join(environment, 'bin', 'activate'), source_conf))
    elif Path(os.path.join(environment, 'etc', 'conda', 'activate.d')).expanduser().exists():
        # let conda patch the bashrc
        os.system("conda init")
        # make sure we activate this environment by default
        os.system("echo 'conda activate {}' >> {}".format(environment, source_conf))

    # set default folder for user
    if param.get("user_base_directory"):
        base_dir = param.get("user_base_directory")
        if ' ' in base_dir:
            base_dir = '\"{}\"'.format(base_dir)
        os.system("echo 'cd {}' >> {}".format(base_dir, source_conf))

    # make sure we load the source configuration
    os.system("echo 'source {}' >> ~/.bashrc".format(source_conf))
    os.system("echo '. {}' >> ~/.profile".format(source_conf))

    # check if we need to create .git-credentials

    runtime_property_support = Session.check_min_api_version("2.13")
    if runtime_property_support:
        # noinspection PyProtectedMember
        runtime_prop = dict(task._get_runtime_properties())
        git_credentials = runtime_prop.pop('_git_credentials', None)
        git_config = runtime_prop.pop('_git_config', None)
        # force removing properties
        # noinspection PyProtectedMember
        task._edit(runtime=runtime_prop)
        task.reload()
        if git_credentials is not None:
            git_credentials = _b64_decode_file(git_credentials)
        if git_config is not None:
            git_config = _b64_decode_file(git_config)
    else:
        # noinspection PyProtectedMember
        git_credentials = task._get_configuration_text('git_credentials')
        # noinspection PyProtectedMember
        git_config = task._get_configuration_text('git_config')

    if git_credentials:
        git_cred_file = os.path.expanduser('~/.config/git/credentials')
        # noinspection PyBroadException
        try:
            Path(git_cred_file).parent.mkdir(parents=True, exist_ok=True)
            with open(git_cred_file, 'wt') as f:
                f.write(git_credentials)
        except Exception:
            print('Could not write {} file'.format(git_cred_file))

    if git_config:
        git_config_file = os.path.expanduser('~/.config/git/config')
        # noinspection PyBroadException
        try:
            Path(git_config_file).parent.mkdir(parents=True, exist_ok=True)
            with open(git_config_file, 'wt') as f:
                f.write(git_config)
        except Exception:
            print('Could not write {} file'.format(git_config_file))

    # check if we need to retrieve remote files for the session
    if "session-files" in task.artifacts:
        try:
            target_dir = os.path.expanduser("~/session-files/")
            cached_files_folder = task.artifacts["session-files"].get_local_copy(
                extract_archive=True, force_download=True, raise_on_error=True)
            # noinspection PyBroadException
            try:
                # first try a simple, move, if we fail, copy and delete
                os.replace(cached_files_folder, target_dir)
            except Exception:
                import shutil
                Path(target_dir).mkdir(parents=True, exist_ok=True)
                if Path(cached_files_folder).is_dir():
                    shutil.copytree(
                        src=cached_files_folder,
                        dst=target_dir,
                        symlinks=True,
                        ignore_dangling_symlinks=True,
                        dirs_exist_ok=True)
                    shutil.rmtree(cached_files_folder)
                else:
                    target_file = Path(cached_files_folder).name
                    # we need to remove the taskid prefix from the cache folder
                    target_file = (Path(target_dir) / (".".join(target_file.split(".")[1:]))).as_posix()
                    shutil.copy(cached_files_folder, target_file, follow_symlinks=False)
                    os.unlink(cached_files_folder)
        except Exception as ex:
            print("\nWARNING: Failed downloading remote session files! {}\n".format(ex))

    return env


def get_host_name(task, param):
    # noinspection PyBroadException
    try:
        hostname = socket.gethostname()
        hostnames = socket.gethostbyname(socket.gethostname())
    except Exception:
        def get_ip_addresses(family):
            for interface, snics in psutil.net_if_addrs().items():
                for snic in snics:
                    if snic.family == family:
                        yield snic.address

        hostnames = list(get_ip_addresses(socket.AF_INET))[0]
        hostname = hostnames

    # try to get external address (if possible)
    # noinspection PyBroadException
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # noinspection PyBroadException
        try:
            # doesn't even have to be reachable
            s.connect(('8.255.255.255', 1))
            hostnames = s.getsockname()[0]
        except Exception:
            pass
        finally:
            s.close()
    except Exception:
        pass

    # override if we have host name defines
    if os.environ.get("CLEARML_AGENT_HOST_IP"):
        hostnames = hostname = os.environ.get("CLEARML_AGENT_HOST_IP")

    # update host name
    if (not task.get_parameter(name='properties/external_address') and
            not task.get_parameter(name='properties/k8s-gateway-address')):

        if task._get_runtime_properties().get("external_address"):
            external_addr = task._get_runtime_properties().get("external_address")
        else:
            external_addr = hostnames
            if param.get('public_ip'):
                # noinspection PyBroadException
                try:
                    external_addr = requests.get('https://checkip.amazonaws.com').text.strip()
                except Exception:
                    pass
            # make sure we set it to the runtime properties
            task._set_runtime_properties({"external_address": external_addr})

        # make sure we set it back to the Task user properties
        task.set_parameter(name='properties/external_address', value=str(external_addr))

    return hostname, hostnames


def run_user_init_script(task):
    # run initialization script:
    # noinspection PyProtectedMember
    init_script = task._get_configuration_text(config_object_section_bash_init)
    if not init_script or not str(init_script).strip():
        return
    print("Running user initialization bash script:")
    init_filename = os_json_filename = None
    try:
        fd, init_filename = mkstemp(suffix='.init.sh')
        os.close(fd)
        fd, os_json_filename = mkstemp(suffix='.env.json')
        os.close(fd)
        with open(init_filename, 'wt') as f:
            f.write(init_script +
                    '\n{} -c '
                    '"exec(\\"try:\\n import os\\n import json\\n'
                    ' json.dump(dict(os.environ), open(\\\'{}\\\', \\\'w\\\'))'
                    '\\nexcept: pass\\")"'.format(sys.executable, os_json_filename))
        env = dict(**os.environ)
        # do not pass or update back the PYTHONPATH environment variable
        env.pop('PYTHONPATH', None)
        subprocess.call(['/bin/bash', init_filename], env=env)
        with open(os_json_filename, 'rt') as f:
            environ = json.load(f)
        # do not pass or update back the PYTHONPATH environment variable
        environ.pop('PYTHONPATH', None)
        # update environment variables
        os.environ.update(environ)
    except Exception as ex:
        print('User initialization script failed: {}'.format(ex))
    finally:
        if init_filename:
            try:
                os.unlink(init_filename)
            except:  # noqa
                pass
        if os_json_filename:
            try:
                os.unlink(os_json_filename)
            except:  # noqa
                pass
    os.environ['CLEARML_DOCKER_BASH_SCRIPT'] = str(init_script)


def _sync_workspace_snapshot(task, param, auto_shutdown_task):
    workspace_folder = param.get("store_workspace")
    if not workspace_folder:
        # nothing to do
        return

    print("Syncing workspace {}".format(workspace_folder))

    workspace_folder = Path(os.path.expandvars(workspace_folder)).expanduser()
    if not workspace_folder.is_dir():
        print("WARNING: failed to create workspace snapshot from '{}' - "
              "directory does not exist".format(workspace_folder))
        return

    # build hash of
    files_desc = ""
    for f in workspace_folder.rglob("*"):
        fs = f.stat()
        files_desc += "{}: {}[{}]\n".format(f.absolute(), fs.st_size, fs.st_mtime)
    workspace_hash = hash(str(files_desc))
    if param.get("workspace_hash") == workspace_hash:
        # noinspection PyPackageRequirements
        try:
            time_stamp = datetime.datetime.fromtimestamp(
                param.get(sync_runtime_property)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            time_stamp = param.get(sync_runtime_property)

        print("Skipping workspace snapshot upload, "
              "already uploaded no files changed since last sync {}".format(time_stamp))
        return

    # force running status - so that we can upload the artifact
    prev_status = task.status
    if prev_status not in ("in_progress", ):
        task.mark_started(force=True)

    try:
        print("Compressing workspace: {}".format(workspace_folder))

        # create a tar file of the folder
        # put a consistent file name into a temp folder because the filename is part of
        # the compressed artifact, and we want consistency in hash.
        # After that we rename compressed file to temp file and
        temp_folder = Path(mkdtemp(prefix='workspace_'))
        local_gzip = (temp_folder / "workspace_snapshot").as_posix()
        # notice it will add a ".tar.gz" suffix to the file
        local_gzip = shutil.make_archive(
            base_name=local_gzip, format="gztar", root_dir=workspace_folder.as_posix())
        if not local_gzip:
            print("ERROR: Failed compressing workspace [{}]".format(workspace_folder))
            raise ValueError("Failed compressing workspace")

        # list archived files for preview
        files = list(workspace_folder.rglob("*"))
        archive_preview = 'Archive content {}:\n'.format(workspace_folder)
        for filename in sorted(files):
            if filename.is_file():
                relative_file_name = filename.relative_to(workspace_folder)
                archive_preview += '{} - {:,} B\n'.format(relative_file_name, filename.stat().st_size)

        print("Uploading workspace: {}".format(workspace_folder))

        # upload actual snapshot tgz
        timestamp = datetime.datetime.now(datetime.UTC) \
            if hasattr(datetime, "UTC") and hasattr(datetime.datetime, "now") else datetime.datetime.utcnow()  # noqa
        task.upload_artifact(
            name=artifact_workspace_name,
            artifact_object=Path(local_gzip),
            delete_after_upload=True,
            preview=archive_preview,
            metadata={"timestamp": str(timestamp), sync_workspace_creating_id: task.id},
            wait_on_upload=True,
            retries=3
        )

        try:
            temp_folder.rmdir()
        except Exception as ex:
            print("Warning: Failed removing temp artifact folder: {}".format(ex))

        print("Finalizing workspace sync")

        # change artifact to input artifact
        task.reload()
        # find our artifact and update it
        for a in task.data.execution.artifacts:
            if a.key != artifact_workspace_name:
                # nothing to do
                continue
            elif a.mode == tasks.ArtifactModeEnum.input:
                # the old input entry - we are changing to output artifact
                # the reason is that we want this entry to be deleted with this Task
                # in contrast to Input entries that are Not deleted when deleting the Task
                a.mode = tasks.ArtifactModeEnum.output
                a.key = "old_" + str(a.key)
            else:
                # set the new entry as an input artifact
                a.mode = tasks.ArtifactModeEnum.input

        # noinspection PyProtectedMember
        task._edit(execution=task.data.execution, force=True)
        task.reload()

        # update our timestamp & hash
        param[sync_runtime_property] = time()
        param["workspace_hash"] = workspace_hash
        # noinspection PyProtectedMember
        task._set_runtime_properties(runtime_properties={sync_runtime_property: time()})
        print("[{}] Workspace '{}' snapshot synced".format(timestamp, workspace_folder))
    except Exception as ex:
        print("ERROR: Failed syncing workspace [{}]: {}".format(workspace_folder, ex))
    finally:
        if auto_shutdown_task:
            if prev_status in ("failed", ):
                task.mark_failed(force=True, status_message="workspace shutdown sync completed")
            elif prev_status in ("completed", ):
                task.mark_completed(force=True, status_message="workspace shutdown sync completed")
            else:
                task.mark_stopped(force=True, status_message="workspace shutdown sync completed")


def sync_workspace_snapshot(task, param, auto_shutdown_task=True):
    __poor_lock.append(time())
    if len(__poor_lock) != 1:
        # someone is already in, we should leave
        __poor_lock.pop(-1)

    try:
        return _sync_workspace_snapshot(task, param, auto_shutdown_task=auto_shutdown_task)
    finally:
        __poor_lock.pop(-1)


def restore_workspace(task, param):
    if not param.get("store_workspace"):
        # check if we have something to restore, show warning
        if artifact_workspace_name in task.artifacts:
            print("WARNING: Found workspace snapshot, but ignoring since store_workspace is 'None'")
        return None

    # add sync callback, timeout 5 min
    print("Setting workspace snapshot sync callback on session end")
    task.register_abort_callback(
        partial(sync_workspace_snapshot, task, param),
        callback_execution_timeout=60*5)

    try:
        workspace_folder = Path(os.path.expandvars(param.get("store_workspace"))).expanduser()
        workspace_folder.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        print("ERROR: Could not create workspace folder {}: {}".format(
            param.get("store_workspace"), ex))
        return None

    if artifact_workspace_name not in task.artifacts:
        print("No workspace snapshot was found, a new workspace snapshot [{}] "
              "will be created when session ends".format(workspace_folder))
        return None

    print("Fetching previous workspace snapshot")
    artifact_zip_file = task.artifacts[artifact_workspace_name].get_local_copy(extract_archive=False)
    if not artifact_zip_file:
        print("Error: Fetching previous workspace snapshot Failed! skipping workspace restore")
        return None

    print("Restoring workspace snapshot")
    try:
        shutil.unpack_archive(artifact_zip_file, extract_dir=workspace_folder.as_posix())
    except Exception as ex:
        print("ERROR: restoring workspace snapshot failed: {}".format(ex))
        return None

    # remove the workspace from the cache
    try:
        os.unlink(artifact_zip_file)
    except Exception as ex:
        print("WARNING: temp workspace zip could not be removed: {}".format(ex))

    print("Successfully restored workspace checkpoint to {}".format(workspace_folder))
    # set time stamp
    # noinspection PyProtectedMember
    task._set_runtime_properties(runtime_properties={sync_runtime_property: time()})
    return workspace_folder


def verify_workspace_storage_access(store_workspace, task):
    # notice this function will call EXIT if we do not have access rights to the output storage
    if not store_workspace:
        return True

    # check that we have credentials to upload the artifact,
    try:
        original_output_uri = task.output_uri
        task.output_uri = task.output_uri or True
        task.output_uri = original_output_uri
    except ValueError as ex:
        print(
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "Error!\n"
            "  `store_workspace` requested but target storage is not accessible!\n"
            "  \n"
            "  Storage configuration server error - could not store working session\n"
            "  If you are using GS/Azure/S3 (or compatible) make sure to\n"
            "  1. Verify your credentials in the ClearML Vault\n"
            "  2. Add the relevant python package to the session:\n"
            "      Azure: azure-storage-blob>=12.0.0\n"
            "      GS: google-cloud-storage>=1.13.2\n"
            "      S3: boto3>=1.9\n"
            "Exception:\n"
            f"{ex}\n"
            "*************************************************************************\n"
            "*************************************************************************\n"
        )
        # do not throw the exception itself, because it will confuse readers
        exit(1)


class SyncCallback:
    pipe_file_name_c = "clearml_sync_pipe_c"
    pipe_file_name_r = "clearml_sync_pipe_r"
    magic = "DEFAULT"
    cmd_file = "clearml-sync-workspace"
    _original_stdout_write = None
    _original_stderr_write = None
    ssh_banner = [
        "#!/bin/bash",
        "echo \"\"",
        "echo \"ClearML-Session:\"",
        "echo \" * Workspace at {workspace_dir} will be automatically synced at the end of the session, "
        "or manually by running '{clearml_sync_cmd}' command\"",
        "echo \" * Close session from the web UI or by running 'shutdown' command as root.\"",
        "echo \"\"",
        "",
    ]
    singleton = None

    def __init__(
            self,
            sync_function: callable = None,
            monitor_process: subprocess.Popen = None,
            workspace_dir: str = None
    ):
        self.magic = str(uuid4())
        self._fd = None
        self._sync_func = sync_function
        self._monitor_process = monitor_process
        self._workspace_dir = workspace_dir
        self._path_dir = None
        SyncCallback.singleton = self
        tmp_dir = Path(mkdtemp(prefix='session_'))
        self.pipe_file_name_c = tmp_dir / SyncCallback.pipe_file_name_c
        self.pipe_file_name_r = tmp_dir / SyncCallback.pipe_file_name_r

    def init(self):
        if self._sync_func:
            try:
                self._create_sync_object()
                self._write_sync_cmd_file()
            except Exception as ex:
                print("Failed to create sync object: {}".format(ex))

        try:
            self._create_monitor_process()
            self._shutdown_cmd()
        except Exception as ex:
            print("Failed to create shutdown cmd: {}".format(ex))

        try:
            self._write_ssh_banner()
        except Exception as ex:
            print("Failed to create ssh banner: {}".format(ex))

    def background_sync_thread(self) -> None:
        if not self._sync_func:
            return

        while True:
            try:
                # Open the pipe for reading
                with open(self.pipe_file_name_c, 'rt') as pipe:
                    command = pipe.read().strip()
                    if not command or command.split(":", 1)[0] != self.magic:
                        continue
                    command = command.split(":", 1)[-1]
                    if not command:
                        continue

                    print(f"Received command: {command}")
                    if not os.path.exists(self.pipe_file_name_r):
                        os.mkfifo(self.pipe_file_name_r, 0o644)

                    timestamp = command.split("=", 1)[-1]

                    with open(self.pipe_file_name_r, 'wb') as pipe_out:
                        self._fd = pipe_out
                        # so that we push all our prints
                        self._patch_stdout()

                        try:
                            self._sync_func()
                        except Exception as ex:
                            print("WARNING: sync callback failed [{}]: {}".format(self._sync_func, ex))

                        try:
                            pipe_out.write("\nEOF={}\n".format(timestamp).encode())
                        except Exception as ex:
                            self._restore_stdout()
                            print("Exception occurred while syncing: {}".format(ex))

                        # restore original stdout/stderr
                        self._restore_stdout()

                    self._fd = None

            except Exception as ex:
                self._restore_stdout()
                self._fd = None
                print("Exception occurred while waiting for sync request: {}\nWaiting for 5 seconds...".format(ex))
                sleep(5)

        # maybe we will get here
        os.remove(self.pipe_file_name_r)
        os.remove(self.pipe_file_name_c)

    def wait_on_process(self, run_background_sync_thread=True, call_sync_callback_on_return=True):
        if not self._monitor_process:
            # if we do not have a process to wait just call the sync background
            if run_background_sync_thread:
                self.background_sync_thread()
        else:
            # start background thread
            if run_background_sync_thread:
                Thread(target=self.background_sync_thread, daemon=True).start()
            # wait on process
            self._monitor_process.wait()

        if call_sync_callback_on_return and self._sync_func:
            self._sync_func()

    def _create_sync_object(self) -> object:
        # Create the named pipe if it doesn't exist
        if not os.path.exists(self.pipe_file_name_c):
            os.mkfifo(self.pipe_file_name_c, 0o644)
        if not os.path.exists(self.pipe_file_name_r):
            os.mkfifo(self.pipe_file_name_r, 0o644)

    def _create_monitor_process(self):
        if self._monitor_process:
            return
        sleep_cmd = shutil.which("sleep")
        self._monitor_process = subprocess.Popen([sleep_cmd, "999d"], shell=False)

    def _write_sync_cmd_file(self):
        import inspect
        source_function = inspect.getsource(_sync_cmd_function)
        source_function = "#!{}\n\n".format(sys.executable) + source_function
        source_function = source_function.replace("SyncCallback.pipe_file_name_c",
                                                  "\"{}\"".format(self.pipe_file_name_c))
        source_function = source_function.replace("SyncCallback.pipe_file_name_r",
                                                  "\"{}\"".format(self.pipe_file_name_r))
        source_function = source_function.replace("SyncCallback.magic", "\"{}\"".format(self.magic))
        source_function += "\nif __name__ == \"__main__\":\n    {}()\n".format("_sync_cmd_function")
        # print("source_function:\n```\n{}\n```".format(source_function))

        full_path = None
        path_folders = os.environ.get("PATH", "/usr/bin").split(os.pathsep)
        path_folders += ["/tmp/.clearml.session.cmd/"]
        if self._path_dir:
            path_folders = [self._path_dir] + path_folders
        last_ex = None
        for i, p in enumerate(path_folders):
            # noinspection PyBroadException
            try:
                p = Path(p)
                # create the last temp folder, the one we added
                if i == len(path_folders) - 1:
                    p.mkdir(parents=True, exist_ok=True)

                if not p.is_dir():
                    continue

                full_path = Path(p) / self.cmd_file
                full_path.touch(exist_ok=True)

                with open(full_path, "wt") as f:
                    f.write(source_function)
                os.chmod(full_path, 0o777)

                if p.as_posix() not in path_folders:
                    os.environ["PATH"] = (
                            os.environ.get("PATH").rstrip(os.pathsep) + "{}{}".format(os.pathsep, p))
                break
            except Exception as ex:
                last_ex = ex
                if full_path:
                    # noinspection PyBroadException
                    try:
                        Path(full_path).unlink()
                    except Exception:
                        pass
                    full_path = None

        if not full_path:
            print("ERROR: Failed to create sync execution cmd: {}".format(last_ex))
            return
        self._path_dir = full_path.as_posix()
        print("Creating sync command in: {}".format(full_path))

    def _write_ssh_banner(self):
        banner_file = Path("/etc/update-motd.d/")
        make_exec = False
        if banner_file.is_dir():
            banner_file = banner_file / "99-clearml"
            make_exec = True
        else:
            banner_file = Path("/etc/profile").expanduser()

        # noinspection PyBroadException
        try:
            banner_file.touch(exist_ok=True)
        except Exception:
            banner_file = Path("~/.profile").expanduser()
            # noinspection PyBroadException
            try:
                banner_file.touch(exist_ok=True)
            except Exception:
                print("WARNING: failed creating ssh banner")
                return

        try:
            with open(banner_file, "at") as f:
                ssh_banner = self.ssh_banner

                # skip first `#!/bin/bash` line if this is not an executable, and add a new line instead
                if not make_exec:
                    ssh_banner = [""] + ssh_banner[1:]

                f.write("\n".join(ssh_banner).format(
                    workspace_dir=self._workspace_dir, clearml_sync_cmd=self.cmd_file
                ))

            if make_exec:
                os.chmod(banner_file.as_posix(), 0o755)

        except Exception as ex:
            print("WARNING: Failed to write to banner {}: {}".format(banner_file, ex))

    def _shutdown_cmd(self):
        batch_command = [
            "#!/bin/bash",
            "[ \"$UID\" -ne 0 ] && echo \"shutdown: Permission denied. Try as root.\" && exit 1",
            "[ ! -f /tmp/.clearml.session.pid ] && echo \"shutdown: failed.\" && exit 2",
            "[ ! -z $(command -v {}) ] && echo \"Syncing workspace\" && {}".format(self.cmd_file, self.cmd_file),
            "kill -9 $(cat /tmp/.clearml.session.pid 2>/dev/null) && echo \"system is now spinning down - "
            "it might take a minute if we need to upload the workspace:\""
            " && for ((i=180; i>=0; i--)); do echo -n \" .\"; sleep 1; done",
            ""
        ]

        if not self._monitor_process:
            return

        # if we are not running as root, remove the root check
        if os.getuid() != 0:
            batch_command = [batch_command[0]] + batch_command[2:]

        path_folders = os.environ.get("PATH", "/usr/bin").split(os.pathsep)
        if self._path_dir:
            path_folders = [self._path_dir] + path_folders

        last_ex = None
        shutdown_cmd = None
        for p in path_folders:
            shutdown_cmd_directory = Path(p)
            if not shutdown_cmd_directory.is_dir():
                continue

            # noinspection PyBroadException
            try:
                (Path(p) / "shutdown").unlink()
            except Exception:
                pass

            try:
                shutdown_cmd = shutdown_cmd_directory / "shutdown"
                with open(shutdown_cmd, "wt") as f:
                    f.write("\n".join(batch_command))
                os.chmod(shutdown_cmd.as_posix(), 0o755)
                break
            except Exception as ex:
                last_ex = ex
                shutdown_cmd = None

        if not shutdown_cmd:
            print("WARNING: Failed to write to shutdown cmd: {}".format(last_ex))

        try:
            with open("/tmp/.clearml.session.pid", "wt") as f:
                f.write("{}".format(self._monitor_process.pid))
        except Exception as ex:
            print("WARNING: Failed to write to run pid: {}".format(ex))

    def _stdout__patched__write__(self, is_stderr, *args, **kwargs):
        write_func = self._original_stderr_write if is_stderr else self._original_stdout_write
        ret = write_func(*args, **kwargs)  # noqa

        if self._fd:
            message = args[0] if len(args) > 0 else None
            if message is not None:
                try:
                    message = str(message)
                    if "\n" not in message:
                        message = message + "NEOL\n"
                    self._fd.write(message.encode())
                    self._fd.flush()
                except Exception as ex:
                    self._original_stderr_write(" WARNING: failed sending stdout over pipe: {}\n".format(ex))

        return ret

    def _patch_stdout(self):
        if not self._original_stdout_write:
            self._original_stdout_write = sys.stdout.write
        if not self._original_stderr_write:
            self._original_stderr_write = sys.stderr.write
        sys.stdout.write = partial(self._stdout__patched__write__, False,)
        sys.stderr.write = partial(self._stdout__patched__write__, True,)

    def _restore_stdout(self):
        if self._original_stdout_write:
            sys.stdout.write = self._original_stdout_write
            self._original_stdout_write = None
        if self._original_stderr_write:
            sys.stderr.write = self._original_stderr_write
            self._original_stderr_write = None


def _sync_cmd_function():
    # this is where we put all the imports and the sync call back
    import os
    import sys
    from time import time

    print("Storing workspace to persistent storage")
    try:
        if not os.path.exists(SyncCallback.pipe_file_name_c):
            os.mkfifo(SyncCallback.pipe_file_name_c, 0o644)
    except Exception as ex:
        print("ERROR: Failed creating request pipe {}".format(ex))

    # push the request
    timestamp = str(time())
    try:
        with open(SyncCallback.pipe_file_name_c, 'wt') as pipe:
            cmd = "{}:sync={}".format(SyncCallback.magic, timestamp)
            pipe.write(cmd)
    except Exception as ex:
        print("ERROR: Failed sending sync request {}".format(ex))

    # while we did not get EOF
    try:
        # Read the result from the server
        with open(SyncCallback.pipe_file_name_r, 'rb') as pipe:
            while True:
                result = pipe.readline()
                if not result:
                    break
                result = result.decode()

                if result.endswith("NEOL\n"):
                    result = result[:-5]

                # read from fd
                if "EOF=" in result:
                    stop = False
                    for l in result.split("\n"):
                        if not l.startswith("EOF="):
                            sys.stdout.write(l+"\n")
                        elif l.endswith("={}".format(timestamp)):
                            stop = True

                    if stop:
                        print("Workspace synced successfully")
                        break
                else:
                    sys.stdout.write(result)

    except Exception as ex:
        print("ERROR: Failed reading sync request result {}".format(ex))


def main():
    # noinspection PyBroadException
    try:
        Task.set_resource_monitor_iteration_timeout(
            seconds_from_start=1,
            wait_for_first_iteration_to_start_sec=1,  # noqa
            max_wait_for_first_iteration_to_start_sec=1  # noqa
        )  # noqa
    except Exception:
        pass

    param = {
        "user_base_directory": "~/",
        "ssh_server": True,
        "ssh_password": "training",
        "default_docker": "nvidia/cuda",
        "user_key": None,
        "user_secret": None,
        "vscode_server": True,
        "vscode_version": '',
        "vscode_extensions": '',
        "jupyterlab": True,
        "public_ip": False,
        "ssh_ports": None,
        "force_dropbear": False,
        "store_workspace": None,
        "use_ssh_proxy": False,
        "router_enabled": False,
    }
    task = init_task(param, default_ssh_fingerprint)

    # if router is enabled, do not request a public IP, enforce local IP
    if param.get("router_enabled") and param.get("public_ip"):
        print("External TCP router configured, disabling `public_ip` request")
        param["public_ip"] = False

    run_user_init_script(task)

    # notice this function will call EXIT if we do not have access rights to the output storage
    verify_workspace_storage_access(store_workspace=param.get("store_workspace"), task=task)

    # restore workspace if exists
    # notice, if "store_workspace" is not set we will Not restore the workspace
    try:
        restore_workspace(task, param)
    except Exception as ex:
        print("ERROR: Failed restoring workspace: {}".format(ex))

    # make the new user base folder the workspace directory
    if (param["store_workspace"] or "").strip():
        param["user_base_directory"] = param["store_workspace"]

    hostname, hostnames = get_host_name(task, param)

    env = setup_user_env(param, task)

    ssh_port = setup_ssh_server(hostname, hostnames, param, task, env)

    # make sure we set it to the runtime properties
    if ssh_port:
        ext_ssh_port = 0
        # noinspection PyProtectedMember
        if task._get_runtime_properties().get("_external_host_tcp_port_mapping"):
            # noinspection PyProtectedMember
            ext_port_mapping = task._get_runtime_properties().get("_external_host_tcp_port_mapping")
            for port_map in ext_port_mapping.split(","):
                if port_map.split(":")[-1] == str(ssh_port):
                    ext_ssh_port = port_map.split(":")[0]
                    break

        if not ext_ssh_port:
            ext_ssh_port = ssh_port
        # noinspection PyProtectedMember
        address = task._get_runtime_properties().get("external_address") or hostnames
        print("Requesting TCP route from router ingress to {} port {}".format(address, ssh_port))
        # noinspection PyProtectedMember
        task._set_runtime_properties({
            "external_address": address,
            "external_tcp_port": str(ext_ssh_port),
            "_SERVICE": "EXTERNAL_TCP",
        })

        # ask the router to set routing to us
        if param.get("router_enabled"):
            task.set_system_tags((task.get_system_tags() or []) + ["external_service"])

    start_vscode_server(hostname, hostnames, param, task, env)

    # Notice we can only monitor the jupyter server because the vscode/ssh do not have "quit" interface
    # we add `shutdown` command below
    jupyter_process = start_jupyter_server(hostname, hostnames, param, task, env)

    syncer = SyncCallback(
        sync_function=partial(sync_workspace_snapshot, task, param, False),
        monitor_process=jupyter_process,
        workspace_dir=param.get("store_workspace")
    )
    syncer.init()
    # notice this will end when process is done
    print('Wait until shutdown')
    syncer.wait_on_process(run_background_sync_thread=True, call_sync_callback_on_return=True)

    print('We are done')
    # no need to sync the process, syncer.wait_on_process already did that

    # sync back python packages for next time
    # TODO: sync python environment

    print('Goodbye')


if __name__ == '__main__':
    main()

<div align="center">

<a href="https://app.clear.ml"><img src="https://github.com/clearml/clearml/blob/master/docs/clearml-logo.svg?raw=true" width="250px"></a>

## **`clearml-session` </br> CLI for launching JupyterLab / VSCode / SSH on a remote machine**

## 🔥 NEW in version `0.13` [Workspace Syncing](#-store-and-synchronize-interactive-session-workspace) 🚀 


[![GitHub license](https://img.shields.io/github/license/clearml/clearml-session.svg)](https://img.shields.io/github/license/clearml/clearml-session.svg)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/clearml-session.svg)](https://img.shields.io/pypi/pyversions/clearml-session.svg)
[![PyPI version shields.io](https://img.shields.io/pypi/v/clearml-session.svg)](https://img.shields.io/pypi/v/clearml-session.svg)
[![PyPI status](https://img.shields.io/pypi/status/clearml-session.svg)](https://pypi.python.org/pypi/clearml-session/)
[![Slack Channel](https://img.shields.io/badge/slack-%23clearml--community-blueviolet?logo=slack)](https://joinslack.clear.ml)

`🌟 ClearML is open-source - Leave a star to support the project! 🌟`

</div>

**`clearml-session`** is a utility for launching detachable remote interactive sessions (MacOS, Windows, Linux)

### tl;dr 
**CLI to launch a remote session of Jupyter-Lab / VSCode / SSH, 
inside any docker container on any deployment, Cloud / Kubernetes / Bare-Metal**

### 🔰 What does it do?
Starting a clearml (ob)session from your local machine triggers the following:
- ClearML allocates a remote instance (GPU) from your dedicated pool
- On the allocated instance it will spin **jupyter-lab** + **vscode server** + **SSH** access for
interactive usage (i.e., development)
- ClearML will start monitoring machine performance, allowing DevOps to detect stale instances and spin them down
- NEW 🔥 Kubernetes support, develop directly inside your pods! No kubectl required! 
Read more about `clearml-agent` and interactive sessions [here](https://clear.ml/docs/latest/docs/clearml_agent/#kubernetes)   
- NEW 🎉 Automatically store & sync your [interactive session workspace](#-store-and-synchronize-interactive-session-workspace). 
`clearml-session` will automatically create a snapshot of your entire workspace when shutting it down, 
and later restore into a new session on a different remote machine

> ℹ️ **Remote PyCharm:** You can also work with PyCharm in a remote session over SSH. Use the [PyCharm Plugin](https://github.com/clearml/clearml-pycharm-plugin) to automatically sync local configurations with a remote session.


### Use-cases for remote interactive sessions:
1. Development requires resources not available on the current developer's machines
2. Team resource sharing (e.g. how to dynamically assign GPUs to developers)
3. Spin a copy of a previously executed experiment for remote debugging purposes (:open_mouth:!)
4. Scale-out development to multiple clouds, assign development machines on AWS/GCP/Azure in a seamless way

## Prerequisites:
* **An SSH client installed on your machine** - To verify, open your terminal and execute `ssh`. If you did not receive an error, we are good to go.
* At least one `clearml-agent` running on a remote host. See installation [details](https://github.com/clearml/clearml-agent).

Supported OS: MacOS, Windows, Linux


## 🔒 Secure & Stable
**clearml-session** creates a single, secure, and encrypted connection to the remote machine over SSH.
SSH credentials are automatically generated by the CLI and contain fully random 32 bytes password.

All http connections are tunneled over the SSH connection,
allowing users to add additional services on the remote machine (!)

Furthermore, all tunneled connections have a special stable network layer allowing you to refresh the underlying SSH
connection without breaking any network sockets!  

This means that if the network connection is unstable, you can refresh
the base SSH network tunnel, without breaking JupyterLab/VSCode-server or your own SSH connection
(e.g. debugging over SSH with PyCharm)  

---

## ⚡ How to use: Interactive Session


1. Run `clearml-session`
2. Select the requested queue (resource)
3. Wait until a machine is up and ready
4. Click on the link to the remote JupyterLab/VSCode OR connect with the provided SSH details

**Notice! You can also**: Select a **docker image** to execute in, install required **python packages**, run **bash script**,
pass **git credentials**, etc.
See below for full CLI options.

## 📖 Tutorials

### 👉 Getting started

Requirements `clearml` python package installed and configured (see detailed [instructions](https://clear.ml/docs/latest/docs/getting_started/ds/ds_first_steps))
``` bash
pip install clearml-session
clearml-session --docker nvcr.io/nvidia/pytorch:20.11-py3 --git-credentials
```

Wait for the machine to spin up.
Expected CLI output would look something like:
``` console
Creating new session
New session created [id=3d38e738c5ff458a9ec465e77e19da23]
Waiting for remote machine allocation [id=3d38e738c5ff458a9ec465e77e19da23]
.Status [queued]
....Status [in_progress]
Remote machine allocated
Setting remote environment [Task id=3d38e738c5ff458a9ec465e77e19da23]
Setup process details: https://app.community.clear.ml/projects/64ae77968db24b27abf86a501667c330/experiments/3d38e738c5ff458a9ec465e77e19da23/output/log
Waiting for environment setup to complete [usually about 20-30 seconds]
..............
Remote machine is ready
Setting up connection to remote session
Starting SSH tunnel
Warning: Permanently added '[192.168.0.17]:10022' (ECDSA) to the list of known hosts.
root@192.168.0.17's password: f7bae03235ff2a62b6bfbc6ab9479f9e28640a068b1208b63f60cb097b3a1784


Interactive session is running:
SSH: ssh root@localhost -p 8022 [password: f7bae03235ff2a62b6bfbc6ab9479f9e28640a068b1208b63f60cb097b3a1784]
Jupyter Lab URL: http://localhost:8878/?token=df52806d36ad30738117937507b213ac14ed638b8c336a7e
VSCode server available at http://localhost:8898/

Connection is up and running
Enter "r" (or "reconnect") to reconnect the session (for example after suspend)
`s` (or "shell") to connect to the SSH session
`Ctrl-C` (or "quit") to abort (remote session remains active)
or "Shutdown" to shut down remote interactive session
```

Click on the **Jupyter Lab** link (http://localhost:8878/?token=xyz),
or **VScode** (running inside your remote container) (http://localhost:8898/),
or drop into **SSH** shell by typing `shell`.

Open your terminal, clone your code & start working :)

> ℹ️ **TIP**: You can additional python package to your remote session setup by adding `--packages` to the command line, 
> for example to add `boto3` add `--packages "boto3>1"`

> ℹ️ **TIP**: If you need direct SSH into the remote container from your terminal, 
> you can directly drop into a shell by adding `--shell` to the command line


### 📞 Leaving a session and reconnecting to it

On the `clearml-session` CLI terminal, enter 'quit' or press `Ctrl-C`
It will close the CLI but preserve the remote session (i.e. remote session will remain running)

When you want to reconnect to it, execute:
``` bash
clearml-session
```

Then press "Y" (or enter) to reconnect to the already running session:
``` console
clearml-session - launch interactive session
Checking previous session
Connect to active session id=3d38e738c5ff458a9ec465e77e19da23 [Y]/n?
```

### Shutting down a remote session

On the `clearml-session` CLI terminal, enter 'shutdown' (case-insensitive).
It will shut down the remote session, free the resource and close the CLI:

```console
Enter "r" (or "reconnect") to reconnect the session (for example after suspend)
`s` (or "shell") to connect to the SSH session
`Ctrl-C` (or "quit") to abort (remote session remains active)
or "Shutdown" to shut down remote interactive session

shutdown

Shutting down interactive session
Remote session shutdown
Goodbye
```

You can also use the CLI to shut down a specific clearml interactive session:

```bash
clearml-session shutdown --id <session_id>
```

### 🔗 Connecting to a running interactive session from a different machine

Continue working on an interactive session from **any** machine.
In the `clearml` web UI, go to the DevOps project, and find your interactive session.
Click on the ID button next to the Task name, and copy the unique ID.

```bash
clearml-session --attach <session_id>
```

Click on the JupyterLab/VSCode link, or connect directly to the SSH session.

> ✨ **TIP**: You can work & debug your colleagues code and workspace by sharing the `session id` 
> and connect to the same remote container together with `--attach`


### 📂 Store and synchronize interactive session workspace

Specify the remote workspace root-folder by adding `--store-workspace ~/workspace` to the command line.
In the remote session container, put all your code / data under the `~/workspace` directory.
When your session is shut down, the workspace folder will be automatically packaged and stored on the clearml file server.
In your next `clearml-session` execution, specify again `--store-workspace ~/workspace` and clearml-session
will grab the previous workspace snapshot and restore it into the new remote container in `~/workspace`.

```bash
clearml-session --store-workspace ~/workspace --docker python:3.10-bullseye
```

To continue the last aborted session and restore the workspace:

```bash
clearml-session --store-workspace ~/workspace --docker python:3.10-bullseye
```

```console
clearml-session - CLI for launching JupyterLab / VSCode / SSH on a remote machine
Verifying credentials
Use previous queue (resource) '1xGPU' [Y]/n? 

Interactive session config:
...
Restore workspace from session id=01bf86f038314434878b2413343ba746 'interactive_session' @ 2024-03-02 20:34:03 [Y]/n? 
Restoring workspace from previous session id=01bf86f038314434878b2413343ba746
```

To continue a **specific** session ID and restore its workspace:

```bash
clearml-session --continue-session <session_id> --store-workspace ~/workspace --docker python:3.10-bullseye
```

### 📤 Upload local files to remote session

If you need to upload files from your local machine into the remote session, 
specify the file or directory with `--upload-files /mnt/data/stuff`. 
The entire content of the directory / file will be copied into your remote `clearml-session` 
container under the `~/session-files/` directory. 

Can be used in conjunction with `--store-workspace` to easily move workloads between local development machines
and remote machines with 100% persistent workspace synchronization.

```bash
clearml-session --upload-files /mnt/data/stuff
```


### 🔧 Debug a previously executed experiment

If you have a previously executed experiment (Task) on the clearml platform,
you can create an exact copy of the experiment (Task) and debug it on the remote interactive session.
`clearml-session` will replicate the exact remote environment, add JupyterLab/VSCode/SSH and allow you interactively
execute and debug the experiment, on the interactive remote container.  

In the `clearml` web UI, find the experiment (Task) you wish to debug.
Click on the ID button next to the Task name, and copy the unique ID, then execute:

```bash
clearml-session --debugging-session <experiment_id_here>
```

Click on the JupyterLab/VSCode link, or drop directly into an SSH shell by typing `shell`.


### 👉 Remote session commands
While running inside the remote session, `clearml-session` adds the following commands to your shell:

- `shutdown` - calling the `shutdown` command, as the name suggests, will shut down the interactive SSH session.

- `clearml-sync-workspace` - calling this command will immediately upload your current workspace directory (see `--store-workspace` argument) to the ClearML configured storage (e.g. files server, S3 etc.).
Notice if this command does not exist this means the session does Not sync any local workspace.


## ❓ Frequently Asked Questions

#### How does it work?

The `clearml-session` creates a new interactive `Task` in the system (default project: DevOps).

This `Task` is responsible for setting the SSH and JupyterLab/VSCode on the host machine.

The local `clearml-session` awaits for the interactive Task to finish with the initial setup, then
it connects via SSH to the host machine (see "safe and stable" above), and tunnels
both SSH and JupyterLab over the SSH connection.

The end result is a local link which you can use to access the JupyterLab/VSCode on the remote machine, over a **secure and encrypted** connection!

#### Does `clearml-session` support Kubernetes clusters?

Yes! `clearml-session` utilizes the `clearml-agent` kubernetes glue together with routing capabilities in order to allow
any clearml-session to spin a container (pod) on the kubernetes cluster and securely connect **directly** into the pod.
This feature does not require any kubernetes access from the users, and simplifies code
development on kubernetes clusters as well as job scheduling & launching. 
Read more on how to deploy clearml on kubernetes [here](https://clear.ml/docs/latest/docs/clearml_agent/#kubernetes).

#### How can I use `clearml-session` to scale up / out development resources?

**Clearml** has a [cloud autoscaler](https://clear.ml/docs/latest/docs/cloud_autoscaling/autoscaling_overview), so you can easily and automatically spin machines for development!

There is also a default docker image to use when initiating a task.

This means that using **clearml-session**s
with the autoscaler enabled, allows for turn-key secure development environment inside a docker of your choosing.

Learn more about it [here](https://clear.ml/docs/latest/docs/guides/services/aws_autoscaler) & [here](https://clear.ml/docs/latest/docs/webapp/applications/apps_gpu_compute).

#### Does `clearml-session` fit Work-From-Home setup?
**YES**. Install `clearml-agent` on target machines inside the organization, connect over your company VPN 
and use `clearml-session` to gain access to a dedicated on-prem machine with the docker of your choosing
(with out-of-the-box support for any internal docker artifactory).

Learn more about how to utilize your office workstations and on-prem machines [here](https://clear.ml/docs/latest/docs/clearml_agent).

## ⌨️ CLI options

```bash
clearml-session --help
```

```console
clearml-session - CLI for launching JupyterLab / VSCode / SSH on a remote machine
usage: clearml-session [-h] [--version] [--attach [ATTACH]] [--shutdown [SHUTDOWN]] [--shell] [--debugging-session DEBUGGING_SESSION] [--queue QUEUE] [--router-enabled [true/false]]
                       [--docker DOCKER] [--docker-args DOCKER_ARGS] [--public-ip [true/false]] [--remote-ssh-port REMOTE_SSH_PORT] [--vscode-server [true/false]]
                       [--vscode-version VSCODE_VERSION] [--vscode-extensions VSCODE_EXTENSIONS] [--jupyter-lab [true/false]] [--upload-files UPLOAD_FILES]
                       [--continue-session CONTINUE_SESSION] [--store-workspace STORE_WORKSPACE] [--git-credentials [true/false]] [--user-folder USER_FOLDER] [--packages [PACKAGES ...]]
                       [--requirements REQUIREMENTS] [--init-script [INIT_SCRIPT]] [--config-file CONFIG_FILE] [--remote-gateway [REMOTE_GATEWAY]] [--base-task-id BASE_TASK_ID]
                       [--project PROJECT] [--session-name SESSION_NAME] [--session-tags [SESSION_TAGS ...]] [--disable-session-cleanup [true/false]] [--keepalive [true/false]]
                       [--queue-excluded-tag [QUEUE_EXCLUDED_TAG ...]] [--queue-include-tag [QUEUE_INCLUDE_TAG ...]] [--skip-docker-network [true/false]] [--password PASSWORD]
                       [--randomize [RANDOMIZE ...]] [--username USERNAME] [--force-dropbear [true/false]] [--disable-storage-packages [true/false]] [--disable-store-defaults]
                       [--disable-fingerprint-check] [--verbose] [--yes]
                       {list,info,shutdown} ...

clearml-session - CLI for launching JupyterLab / VSCode / SSH on a remote machine

positional arguments:
  {list,info,shutdown}  ClearML session control commands
    list                List running Sessions
    info                Detailed information on specific session
    shutdown            Shutdown specific session

options:
  -h, --help            show this help message and exit
  --version             Display the clearml-session utility version
  --attach [ATTACH]     Attach to running interactive session (default: previous session)
  --shutdown [SHUTDOWN], -S [SHUTDOWN]
                        Shut down an active session (default: previous session)
  --shell               Open the SSH shell session directly, notice quiting the SSH session will Not shutdown the remote session
  --debugging-session DEBUGGING_SESSION
                        Pass existing Task id (experiment), create a copy of the experiment on a remote machine, and launch jupyter/ssh for interactive access. Example --debugging-session
                        <task_id>
  --queue QUEUE         Select the queue to launch the interactive session on (default: previously used queue)
  --router-enabled [true/false]
                        If we have a clearml Router set, make sure we request direct TCP routing to our container.
  --docker DOCKER       Select the docker image to use in the interactive session on (default: previously used docker image or `nvidia/cuda:11.6.2-runtime-ubuntu20.04`)
  --docker-args DOCKER_ARGS
                        Add additional arguments for the docker image to use in the interactive session on (default: previously used docker-args)
  --public-ip [true/false]
                        If True register the public IP of the remote machine. Set if running on the cloud. Default: false (use for local / on-premises)
  --remote-ssh-port REMOTE_SSH_PORT
                        Set the remote ssh server port, running on the agent`s machine. (default: 10022)
  --vscode-server [true/false]
                        Install vscode server (code-server) on interactive session (default: true)
  --vscode-version VSCODE_VERSION
                        Set vscode server (code-server) version, as well as vscode python extension version <vscode:python-ext> (example: "3.7.4:2020.10.332292344")
  --vscode-extensions VSCODE_EXTENSIONS
                        Install additional vscode extensions, as well as vscode python extension (example: "ms-python.python,ms-python.black-formatter,ms-python.pylint,ms-python.flake8")
  --jupyter-lab [true/false]
                        Install Jupyter-Lab on interactive session (default: true)
  --upload-files UPLOAD_FILES
                        Advanced: Upload local files/folders to the remote session. Example: `/my/local/data/` will upload the local folder and extract it into the container in ~/session-
                        files/
  --continue-session CONTINUE_SESSION
                        Continue previous session (ID provided) restoring your workspace (see --store-workspace)
  --store-workspace STORE_WORKSPACE
                        Upload/Restore remote workspace folder. Example: `~/workspace/` will automatically restore/store the *containers* folder and extract it into next the session. Use
                        with --continue-session to continue your previous work from your exact container state
  --git-credentials [true/false]
                        If true, local .git-credentials file is sent to the interactive session. (default: false)
  --user-folder USER_FOLDER
                        Advanced: Set the remote base folder (default: ~/)
  --packages [PACKAGES ...]
                        Additional packages to add, supports version numbers (default: previously added packages). examples: --packages torch==1.7 tqdm
  --requirements REQUIREMENTS
                        Specify requirements.txt file to install when setting the interactive session. Requirements file is read and stored in `packages` section as default for the next
                        sessions. Can be overridden by calling `--packages`
  --init-script [INIT_SCRIPT]
                        Specify BASH init script file to be executed when setting the interactive session. Script content is read and stored as default script for the next sessions. To
                        clear the init-script do not pass a file
  --config-file CONFIG_FILE
                        Advanced: Change the configuration file used to store the previous state (default: ~/.clearml_session.json)
  --remote-gateway [REMOTE_GATEWAY]
                        Advanced: Specify gateway ip/address:port to be passed to interactive session (for use with k8s ingestion / ELB)
  --base-task-id BASE_TASK_ID
                        Advanced: Set the base task ID for the interactive session. (default: previously used Task). Use `none` for the default interactive session
  --project PROJECT     Advanced: Set the project name for the interactive session Task
  --session-name SESSION_NAME
                        Advanced: Set the name of the interactive session Task
  --session-tags [SESSION_TAGS ...]
                        Advanced: Add tags to the interactive session for increased visibility
  --disable-session-cleanup [true/false]
                        Advanced: If set, previous interactive sessions are not deleted
  --keepalive [true/false]
                        Advanced: If set, enables the transparent proxy always keeping the sockets alive. Default: False, do not use transparent socket for mitigating connection drops.
  --queue-excluded-tag [QUEUE_EXCLUDED_TAG ...]
                        Advanced: Excluded queues with this specific tag from the selection
  --queue-include-tag [QUEUE_INCLUDE_TAG ...]
                        Advanced: Only include queues with this specific tag from the selection
  --skip-docker-network [true/false]
                        Advanced: If set, `--network host` is **not** passed to docker (assumes k8s network ingestion) (default: false)
  --password PASSWORD   Advanced: Select ssh password for the interactive session (default: `randomly-generated` or previously used one)
  --randomize [RANDOMIZE ...]
                        Advanced: Recreate a new random ssh password for the interactive session options: `--randomize` one time recreate random password, --randomize `always` create a
                        new random password for every session
  --username USERNAME   Advanced: Select ssh username for the interactive session (default: `root` or previously used one)
  --force-dropbear [true/false]
                        Force using `dropbear` instead of SSHd
  --disable-storage-packages [true/false]
                        If True automatic boto3/azure-storage-blob/google-cloud-storage python packages will not be added, you can manually add them using --packages
  --disable-store-defaults
                        If set, do not store current setup as new default configuration
  --disable-fingerprint-check
                        Advanced: If set, ignore the remote SSH server fingerprint check
  --verbose             Advanced: If set, print verbose progress information, e.g. the remote machine setup process log
  --yes, -y             Automatic yes to prompts; assume "yes" as answer to all prompts and run non-interactively

Notice! all arguments are stored as new defaults for the next execution

```



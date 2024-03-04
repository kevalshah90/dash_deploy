### Dash_Deploy

Access `mysqldump` DB file here: https://drive.google.com/file/d/1ayrZbjiXV3ytug-xxb8DpdV8dfQ8LQR5/view?usp=share_link 


Launch App using: 

`python -m auth.__init__` 

`gunicorn --reload auth:app --timeout 8000` 

From https://gunicorn.org/

Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX. It's a pre-fork worker model.

Pre-forking basically means a master creates forks which handle each request. A fork is a completely separate *nix process.



If you will start application via gunicorn in the docker it will spawn several processes. Docker manages only one process and if you will tell "docker down" it will kill "init" process which is gunicorn but those "worker" processes will stay alive.

Gunicorn - Python WSGI HTTP Server for UNIX
https://docs.docker.com/config/containers/multi-service_container/ you can read more here

Docker Documentation
Run multiple services in a container
How to run more than one process in a container

 

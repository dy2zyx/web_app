# Movie RecSys for evaluating recommendation explanations

A movie recommendation system web application based on Django and Docker

## Tips for running the application locally

### Prerequisites

The application is containerized and runs in a Docker container. To run the application, Docker engine needs to be installed:

* To install Docker Desktop on Windows - Go to [Docker's download page for Windows](https://docs.docker.com/docker-for-windows/install)

* To install Docker Desktop on MacOS - Go to [Docker's download page for MacOS](https://docs.docker.com/docker-for-mac/install/)

To check if it Docker is successfully installed, open a terminal and run:

- ```docker --version```

### Steps for running the application

1. Copy the app repository to your local machine. You can download the repository or clone it by using Git.

2. Open a terminal and locate to the app's root folder, which is the 'web_app' folder containing sub-folders such as 'recsys_demo', 'requriements' etc. and files such as 'Dockerfile', 'manage.py' etc.

3. Build a Docker image. In the terminal, run:  ```make build ``` This will build a Docker image named 'web_app' and tagged 'latest'. In the built image, all the required dependencies of the application will be installed. To check if the image has been built, run: ```docker images``` in the terminal.

4. Run the application in a Docker container using docker-compose. In the terminal, run: ```make compose-start``` If you want to run the application in daemon mode, run: ```make compose-start options="-d"```. Normally it will create a container for the built image and run the application. To check if the container is built, run in the terminal: ```docker container ls```

5. Open a web navigator and go to ```localhost:8000/login``` If everything goes well, you will get into a login form.

6. To shut down the application, in the terminal, run: ```make compose-stop```

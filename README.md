# fanfiction-to-ebook
fte is a simple tools that creates ebooks from online fanfiction by scraping their webpages. It can run as a standalone cli command, a local webapp, or a docker image. The primary use case for fte is to create content for local self-hosted (i.e., no access from outside home LAN) use.

PLEASE NOTE: the webapp and docker image use Flask's development server to serve content. Do not use it for high volume or insecure traffic. 

Also, you will need to download the latest gecko / chrome web driver and place it in fte's root directory

## Standalone cli command
Attempting to run fte.py without any input will fail and produce a menu explaining how to use it. You can find more details through the help flag: `-h`
```
python fte.py
```
![no flags](https://i.imgur.com/U8EWzfJ.png)
```
python fte.py -h
```
![help flag](https://i.imgur.com/xVernrA.png)

## Local webapp
To run fte in a local webapp, install the python packages in `requirements.txt` and start up Flask. Also, you may change some of the functionality with the appropriate environemntal variables in an .env file:
### cli commands
```
python -m pip install -r requirements.txt

python -m flask --app -e .env application.py run -p <PORT> 
```
### .env file
```
UPLOAD_DIR="./uploads"    # Which directory to upload .epub files to
WORKING_DIR="."           # Which directory to temporarily use for downloading ebooks from your browser
WEB_DRIVER=firefox        # Which web driver to use. You will need the corresponding browser. firefox or chrome
FLASK_DEBUG=False
```

![web app](https://i.imgur.com/KJizwMQ.png)

## Docker image and container
To use docker, execute the following docker run command. The mounted directory will store the files uploaded using the webapp.
```
docker run --name fte-app -p 42005:42005 --mount type=bind,source="$pwd"/uploads,target=/app/uploads --rm -d jcabre04/fte
```

Alternatively, use docker-compose with fte's docker-compose.yaml file:
```
docker-compose up -d
```

## Thanks!
Shoutouts to:
- Nazli Ander and his [article](https://nander.cc/using-selenium-within-a-docker-container) for helping me find a docker image compatible with chrome and how to configure Selenium to use it! 
- Academind's Maximilian Schwarzmüller and his [udemy course](https://www.udemy.com/course/docker-kubernetes-the-practical-guide/) for a lot of Docker clarification!


# Setting up chrome and chrome driver from:
# https://nander.cc/using-selenium-within-a-docker-container

FROM python:3.10-slim

# Add chrome repository, install it, install chrome driver, update base image
RUN apt-get -y update \
    && apt-get -yq install wget gnupg gnupg2 gnupg1 curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \ 
    && apt-get install -y google-chrome-stable \
    && apt-get install -yqq unzip \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/` \
    curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE \
    `/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && apt-get remove -yq unzip

# Set display port as an environment variable. Helps avoid crashing
ENV DISPLAY=:99

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

ENV UPLOAD_DIR=/app/uploads/
ENV WORKING_DIR=/app/
ENV WEB_DRIVER=chrome

EXPOSE 42005

CMD [ "python", "-m", "flask" , "--app", "./application.py", "run", "-p", "42005", "--host", "0.0.0.0" ]

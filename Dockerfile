#Base Image
FROM docker.artifactory01.ghdna.io/python-nodejs:python3.7-nodejs12

#Defining Working Directory
WORKDIR /app
ADD . /app

#Install Dependencies of the Flask App
RUN pip install -r requirements.txt
EXPOSE 5000

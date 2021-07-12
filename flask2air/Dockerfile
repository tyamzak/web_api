#Dockerfile

FROM python

ARG project_dir=/projects/

ADD src/requirements $project_dir

WORKDIR $project_dir

RUN apt-get update  

RUN pip3 install -r requirements

CMD ["python3","app.py"]

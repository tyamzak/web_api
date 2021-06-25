#Dockerfile

FROM python
#FROM opencvcourses/opencv 

ARG project_dir=/projects/

ADD src/requirements $project_dir

WORKDIR $project_dir

RUN apt-get update && apt-get install -y libopencv-dev 

RUN pip3 install -r requirements

CMD ["python","app.py"]

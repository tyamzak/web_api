#Dockerfile

FROM python

ARG project_dir=/projects/

ADD src/requirements $project_dir

WORKDIR $project_dir

RUN apt-get update  

RUN apt-get upgrade -y

#RUN apt-get install -y 	vim sudo apache2 libapache2-mod-wsgi-py3	

RUN pip3 install -r requirements

# default.confを修正
#RUN rm /etc/apache2/sites-available/000-default.conf

#COPY ./apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf

CMD ["python3","app.py"]

# default.confを修正
#COPY ./myapp /home/vagrant/myapp

# Apache起動
EXPOSE 5051

#CMD ["apachectl", "-D", "FOREGROUND"]
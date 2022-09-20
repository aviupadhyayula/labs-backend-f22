FROM python:alpine3.7
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install pipenv 
RUN PIPENV_VENV_IN_PROJECT="true"
RUN pipenv install --deploy --ignore-pipfile
EXPOSE 5001
ENTRYPOINT ['./gunicorn.sh']

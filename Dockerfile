FROM docker.io/library/python:3.9.19-slim-bullseye

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


VOLUME [ "/src" ]
VOLUME [ "/gpx" ]

WORKDIR /src

EXPOSE 5000


CMD [ "python", "-u", "-m", "flask", "--app", "tracedisplay", "run", "--host=0.0.0.0", "--debug"]


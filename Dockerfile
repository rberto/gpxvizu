FROM python:3.9.19-slim-bullseye

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME [ "/gpx" ]

ADD . .

CMD [ "python", "-u", "./tracedisplay.py" ]


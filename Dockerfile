FROM python:3.9-alpine

ARG TOKEN
ENV TOKEN $TOKEN
WORKDIR /app

COPY . /app
RUN python3 -m pip install -r requirements.txt

CMD ["python3", "main.py"]

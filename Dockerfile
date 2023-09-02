FROM python:3.11.5

WORKDIR /app
COPY . /app
COPY .env /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD ["python", "-m", "src.main"]
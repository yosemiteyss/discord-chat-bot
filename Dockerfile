FROM python:3.11.2

WORKDIR /app
COPY . /app
COPY .env /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80

CMD ["python", "-m", "src.main"]
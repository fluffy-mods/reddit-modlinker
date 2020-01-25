FROM python:3.6

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

CMD ["python", "modlinker.py"]
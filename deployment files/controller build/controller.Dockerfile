FROM python:3.12-alpine3.20
RUN pip install pandas requests
WORKDIR /app
COPY controller.py /app/
CMD ["python", "controller.py"]
FROM python:3.8.10
WORKDIR /app
COPY requirements.txt .
RUN apt update
RUN apt install -y libgl1-mesa-glx
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD exec uvicorn --port 8000 --host 0.0.0.0 app2:app
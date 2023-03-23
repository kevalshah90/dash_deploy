FROM python:3.9

WORKDIR /app

# export GOOGLE_APPLICATION_CREDENTIALS=./stroom-data-exploration-ebf3ef8e9bf0.json
RUN pip install --upgrade pip
RUN pip3 install --upgrade --force-reinstall --no-cache-dir numpy
RUN apt-get update && apt-get install -y build-essential
RUN apt-get install -y gdal-bin proj-bin libgdal-dev libproj-dev 
#libblosc-dev

COPY requirements.txt ./

RUN pip3 install --upgrade --force-reinstall --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

#CMD ["python", "-m", "auth.__init__"]

# Production - No Debugger
#CMD ["python", "-m", "auth.wsgi"]

# Production
#CMD ["gunicorn --reload auth:app --timeout 8000"]

CMD gunicorn --reload auth:app --timeout 8000
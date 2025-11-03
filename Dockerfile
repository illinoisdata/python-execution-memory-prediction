FROM kaggle/python
WORKDIR /kaggle
COPY ./src/. /kaggle

RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "app.py"]
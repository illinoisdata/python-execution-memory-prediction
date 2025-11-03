FROM kaggle/python
WORKDIR /workspace
COPY . /workspace

RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "app.py"]
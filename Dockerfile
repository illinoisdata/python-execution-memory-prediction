FROM kaggle/python
WORKDIR /workspace
COPY . /workspace

RUN mkdir -p /workspace/.kaggle /workspace/tmp && chmod -R 777 /workspace
RUN pip install --no-cache-dir -r requirements.txt

ENV KAGGLE_CONFIG_DIR=/workspace/.kaggle
ENV TMPDIR=/workspace/tmp

ENTRYPOINT ["python", "app.py"]
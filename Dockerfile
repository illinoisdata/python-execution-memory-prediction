FROM kaggle/python
WORKDIR /workspace
COPY . /workspace

RUN pip install --no-cache-dir -r requirements.txt

ENV HOST_UID=0
ENV HOST_GID=0

ENTRYPOINT ["/bin/bash", "-c", "trap 'chown -R ${HOST_UID}:${HOST_GID} /workspace || true' EXIT; python app.py \"$@\"", "--"]
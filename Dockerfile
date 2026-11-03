# Native Python wheels for both linux/amd64 and linux/arm64. No shell/controller socket.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GROKARR_STATE=/state
WORKDIR /app
COPY pyproject.toml README.md LICENSE requirements.lock ./
COPY src ./src
RUN pip install --no-cache-dir --require-hashes -r requirements.lock && pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home bridge && mkdir /state && chown bridge:bridge /state
USER 10001:10001
VOLUME ["/state"]
EXPOSE 8765
ENTRYPOINT ["grokarr-bridge"]
CMD ["serve", "--host", "0.0.0.0"]

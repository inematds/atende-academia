# atende-academia — só biblioteca padrão do Python, sem instalar dependência.
FROM python:3-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY atende VERSION ./
COPY src/ ./src/
COPY exemplos/ ./exemplos/
# SVGs dos exercícios (e o MP4, se existir); EXERCICIOS_MP4_DIR pode apontar para o volume.
COPY web/ ./web/
RUN chmod +x ./atende && mkdir -p /dados
VOLUME ["/dados"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/saude', timeout=3).status == 200 else 1)"
CMD ["./atende", "serve", "--host", "0.0.0.0", "--porta", "8080", "--dados", "/dados"]

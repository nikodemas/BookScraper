FROM python:3.11-slim
LABEL authors="nikodemas"

WORKDIR /app

COPY parser_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt grpcio-tools

COPY proto/ proto/
RUN python -m grpc_tools.protoc \
      --proto_path=proto \
      --python_out=. \
      --grpc_python_out=. \
      proto/bookparser.proto

COPY parser_service/ parser_service/

CMD ["python", "-m", "parser_service.server"]
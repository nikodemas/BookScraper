This project scrapes the book data from [books.toscrape.com](https://books.toscrape.com/) and stores it locally according to the specified schema.

### Main components:
* `scraper`:
    * A web scraper that crawls the data from the [books.toscrape.com](https://books.toscrape.com/).
    * Extracts raw fields and sends them to the `parser_service`.
    * Deployed as a Kubernetes `CronJob`.
* `parser_service`:
    * A gRPC-based service that reads the data coming from the `scraper` via the `ParseBook(RawBook)` call.
    * Validates records and appends them to a `JSONL` file (default `books.jsonl`).
    * Deployed as a Kubernetes `Deployment` with a `Service` exposing port `50051`.

### Testing and deployment:
#### Local Python tests and linting:
```
# Install dev dependencies
pip install flake8 yamllint pytest

# Run linters
flake8 --max-line-length=120 parser_service scraper tests
yamllint kubernetes/

# Run unit tests
pytest -q
```
#### Running the scraper locally:
```
# Install dependencies
pip install -r parser_service/requirements.txt -r scraper/requirements.txt

# Generate gRPC stubs from project root
python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=. \
  --grpc_python_out=. \
  proto/bookparser.proto

# Start parser server
python -m parser_service.server
```
```
# Run scraper in a separate shell
python -m scraper.scraper
```
Now you can check the `data/books.jsonl` file for the scraped data.
You can also change the default values by changing the environment variables (e.g. `export OUTPUT_FILE_NAME=other_books.jsonl`).

#### Running the scraper in Kubernetes:
```
kubectl apply -f kubernetes/config.yaml
kubectl apply -f kubernetes/parser-service.yaml
kubectl apply -f kubernetes/scraper.yaml
```
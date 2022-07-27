# FastAPI App for YSI prediction

build with 
`docker build -t ysi .`

run the API locally with
`docker run -e PORT=8889 -p 8889:8889 -ti ysi`

run the test suite locally
`docker run -t ysi:latest ./run_tests.sh`

#! /bin/sh
python -m grpc_tools.protoc \
	-I./proto \
	--python_out=./api \
	--pyi_out=./api \
	--grpc_python_out=./api \
	./proto/api.proto
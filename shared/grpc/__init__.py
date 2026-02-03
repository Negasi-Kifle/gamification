# gRPC proto definitions, generated code, and server
#
# To generate Python code from proto files:
#   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. shared/grpc/protos/bonus.proto
#

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

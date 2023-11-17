# Import server
import sys
from concurrent import futures

# Add import path for the proto files
from pathlib import Path

import grpc

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "grpc_test_files"))
import time

# Import contextmanager
from contextlib import contextmanager

# Import the generated protobuf files
import helloworld_pb2
import helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)


@contextmanager
def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    yield server
    server.stop(1)


if __name__ == "__main__":
    with serve() as server:
        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            exit()

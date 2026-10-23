import asyncio

import grpc

import kvstore_pb2
import kvstore_pb2_grpc
from storage import KVStorage


class KeyValueStoreService(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, storage: KVStorage) -> None:
        self._storage = storage

    async def Put(self, request, context):
        if request.ttl_seconds < 0:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "ttl_seconds cannot be negative")

        await self._storage.put(
            key=request.key,
            value=request.value,
            ttl_seconds=request.ttl_seconds)

        return kvstore_pb2.PutResponse()

    async def Get(self, request, context):
        value = await self._storage.get(request.key)

        if value is None:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                "Key not found")

        return kvstore_pb2.GetResponse(value=value)

    async def Delete(self, request, context):
        await self._storage.delete(request.key)

        return kvstore_pb2.DeleteResponse()

    async def List(self, request, context):
        entries = await self._storage.list(request.prefix)

        items = [
            kvstore_pb2.KeyValue(
                key=key,
                value=entry.value,
            )
            for key, entry in entries
        ]

        return kvstore_pb2.ListResponse(items=items)

async def serve() -> None:
    server = grpc.aio.server()

    storage = KVStorage(max_size=10)

    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(
        KeyValueStoreService(storage),
        server,
    )

    server.add_insecure_port("[::]:8000")

    await server.start()
    print("gRPC server started on port 8000")

    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())

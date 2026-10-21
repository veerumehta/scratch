Available now: japes plato (SDK 2.6.5)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Pin the new plato release (116ac14e, or the next).

1. Knowledge Hub: knowledge-hub-client is client-api 767b3d6c. Your `x_security_context=` calls on get_collection_by_id,
   list_collection_indexes, create_collection_index, delete_collection and update_collection_scope work as written.
   Still missing on the Knowledge Hub server, so not in any client: delete_collection_index, get_collection_by_name,
   update_collection_index, get_clone_status.
2. Kernel administration: `KernelClient` has `.agents`, `.tools`, `.llms`, `.notepads`, `.config` and `.chat`, with SDK
   types in `jazzx_sdk.clients.kernel_admin_types`. Your calls map one to one: docs/KERNEL_ADMIN.md.
   `.llms` is Kernel's registry; calling models is `jazzx_sdk.llm`.
3. Keto `object_`: not changed (generator rename; wire key is "object"). Use `from_dict`/`to_dict` or an alias.

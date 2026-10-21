Reply to the assistant team: Knowledge Hub x_security_context and Keto `object_`

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

1. x_security_context: the SDK pinned an old knowledge-hub-client (client-api 0b14d3d1) with no such parameter. client-api
   767b3d6c has it on 28 collection functions, including the five you named. Pin that revision now, or take the next
   plato release (the SDK moves to it; not pushed yet). Your `x_security_context=` calls then work as written.

   Four routes still lack it because the Knowledge Hub server does not declare the header there: delete_collection_index,
   get_collection_by_name, update_collection_index, get_clone_status. That needs a Knowledge Hub change and a client
   regeneration; tell us which you call and raise it with the Knowledge Hub owners.

2. Keto `object_`: the generator renames `object` (a builtin); the wire key is still "object". We would not rename it in
   the generated client. Use `Relationship.from_dict({"object": ...})` and `to_dict()`, or alias `object_` on your side.

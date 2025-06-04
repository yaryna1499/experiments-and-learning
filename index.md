<!-- MetadataAPI documentation master file, created by
sphinx-quickstart on Wed Jun  4 13:58:03 2025.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->

# MetadataAPI models documentation

app.models.ArdaDbObject (*arda_db_objects*)
: Represents a supplementary object in ArdaDB.
  <br/>
  ### Columns:
  <br/>
  | *name\**           | VARCHAR(256)   | The object’s name in the format schema_name.object_name              |
  |--------------------|----------------|----------------------------------------------------------------------|
  | → schema_name      | VARCHAR(256)   | Refers to the ArdaDbSchema where the object is defined               |
  | object_type        | VARCHAR(10)    | The type of the ArdaDb entity: Dictionary, Function, etc.            |
  | description        | TEXT?          | The description of the object’s purpose and usage examples           |
  | arguments          | ARRAY          | The list of argument names for the function                          |
  | arguments_types    | ARRAY          | The list of argument types for the function                          |
  | return_values      | ARRAY          | The list of return value names for the function                      |
  | return_value_types | ARRAY          | The list of return value types for the function                      |
  | → object_source_id | INTEGER        | Refers to the ArdaDbObjectSource info necessary to create the object |
  | is_public          | BOOLEAN        |                                                                      |
  | → created_by       | INTEGER        |                                                                      |
  | created_at         | DATETIME       |                                                                      |
  | updated_at         | DATETIME       |                                                                      |
  <br/>
  ### Constraints:
  <br/>
  * FOREIGN KEY (arda_db_object_sources.source_id → object_source_id)
  * FOREIGN KEY (arda_db_schemas.name → schema_name)
  * FOREIGN KEY (identities.identity_id → created_by)
  * PRIMARY KEY (name)

# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: communication.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13\x63ommunication.proto\x12\x05greet\"=\n\rClientMessage\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0f\n\x07problem\x18\x03 \x01(\t\" \n\rServerMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\")\n\rReportMessage\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0c\n\x04json\x18\x02 \x01(\t2\xdc\x01\n\rCommunication\x12:\n\x0cSubmitReport\x12\x14.greet.ReportMessage\x1a\x14.greet.ServerMessage\x12\x41\n\x13NagiosCommunication\x12\x14.greet.ClientMessage\x1a\x14.greet.ServerMessage\x12L\n\x1a\x42idirectionalCommunication\x12\x14.greet.ClientMessage\x1a\x14.greet.ServerMessage(\x01\x30\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'communication_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLIENTMESSAGE._serialized_start=30
  _CLIENTMESSAGE._serialized_end=91
  _SERVERMESSAGE._serialized_start=93
  _SERVERMESSAGE._serialized_end=125
  _REPORTMESSAGE._serialized_start=127
  _REPORTMESSAGE._serialized_end=168
  _COMMUNICATION._serialized_start=171
  _COMMUNICATION._serialized_end=391
# @@protoc_insertion_point(module_scope)
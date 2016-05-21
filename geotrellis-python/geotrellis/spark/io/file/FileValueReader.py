from __future__ import absolute_import
from geotrellis.spark.io.index.Index import Index
from geotrellis.spark.io.package_scala import TileNotFoundError
from geotrellis.spark.io.file.FileAttributeStore import FileAttributeStore
from geotrellis.spark.io.file.FileLayerHeader import FileLayerHeader
from geotrellis.python.util.utils import file_exists, find, to_pairs, from_file
from geotrellis.spark.io.file.KeyPathGenerator import generate_key_path_func
from geotrellis.spark.io.avro.AvroEncoder import AvroEncoder
from geotrellis.spark.io.avro.codecs.KeyValueRecordCodec import KeyValueRecordCodec

def file_value_reader(first, second = None):
    def get_params():
        if second is None:
            if isinstance(first, FileAttributeStore):
                return first, first.catalogPath
            elif isinstance(first, str):
                return FileAttributeStore(first), first
            else:
                raise Exception("wrong params ({0}, {1})".format(str(first), str(second)))
        else:
            return first, second
    attribute_store, catalog_path = get_params()
    def reader(key_type, value_type, layer_id):
        header          = attribute_store.readHeader(FileLayerHeader, layer_id)
        key_index       = attribute_store.readKeyIndex(key_type, layer_id)
        writer_schema   = attribute_store.readSchema(layer_id)

        max_width = Index.digits(key_index.toIndex(key_index.keyBounds.maxKey))
        key_path = generate_key_path_func(catalog_path, header.path, key_index, max_width)
        def read_func(key):
            path = key_path(key)
            if not file_exists(path):
                raise TileNotFoundError(key, layer_id)
            with open(path) as f:
                print("flv reading from {path}".format(path=path))
                recs = AvroEncoder.fromBinary(writer_schema, f.read(), codec = KeyValueRecordCodec(key_type, value_type))
            #recs = to_pairs(from_file(writer_schema, path))
            #found = find(recs, lambda pair: pair[0] == key)
            # <debug>
            counter = [0]
            def func(pair):
                counter[0] += 1
                result = (pair[0] == key)
                if result:
                    print("found at index {ind}".format(ind=counter[0]))
                return result
            found = find(recs, func)
            # </debug>
            if found is None:
                raise TileNotFoundError(key, layer_id)
            else:
                # <debug>
                cellType = found[1].cellType
                print("cellType {c}".format(c=cellType))
                # </debug>
                return found[1]
        return Reader(read_func)
    return ReaderGenerator(reader)

class Reader(object):
    def __init__(self, read_func):
        self.read_func = read_func

    def read(self, key):
        return self.read_func(key)

class ReaderGenerator(object):
    def __init__(self, reader_func):
        self.reader_func = reader_func

    def reader(self, key_type, value_type, layer_id):
        return self.reader_func(key_type, value_type, layer_id)


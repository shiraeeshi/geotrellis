package geotrellis.spark.io.file

import geotrellis.spark.io.{ StorageFormat, LayerHeader }
import spray.json._

case class FileLayerHeader(
  keyClass: String,
  valueClass: String,
  path: String
) extends LayerHeader {
  def format = StorageFormat.S3
}

object FileLayerHeader {
  implicit object FileLayerHeaderFormat extends RootJsonFormat[FileLayerHeader] {
    def write(md: FileLayerHeader) =
      JsObject(
        "format" -> JsString(md.format.name),
        "keyClass" -> JsString(md.keyClass),
        "valueClass" -> JsString(md.valueClass),
        "path" -> JsString(md.path)
      )

    def read(value: JsValue): FileLayerHeader =
      value.asJsObject.getFields("keyClass", "valueClass", "path") match {
        case Seq(JsString(keyClass), JsString(valueClass), JsString(path)) =>
          FileLayerHeader(
            keyClass,
            valueClass,
            path
          )

        case _ =>
          throw new DeserializationException(s"FileLayerHeader expected, got: $value")
      }
  }
}

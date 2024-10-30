from flask import url_for
from flask_resources import JSONSerializer as FlaskJSONSerializer
from invenio_records_resources.services import Service


class JSONSerializer(FlaskJSONSerializer):

    def info(self, service:Service) -> dict:
        ret = {'description': "Invenio RDM JSON Serialization",
                'name': "JSON Serialization"
               }

        schema_value = service.config.record_cls.schema.value
        if schema_value:
            ret['schema'] = schema_value
            if schema_value.startswith("local://"):
                schema_value = schema_value.replace("local://", "")
                ret['schema_url'] = url_for(
                    "oarepo_runtime_info.schema",
                    schema= schema_value,
                    _external=True,
                )
            elif schema_value.startwith("http://") or schema_value.startwith("https://"):
                ret['schema_url'] = schema_value


        return ret
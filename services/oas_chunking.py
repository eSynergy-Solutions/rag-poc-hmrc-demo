import hashlib
import json
import datetime
import yaml
from typing import List, Dict, Any
from abstracts.ServiceChunking import BaseChunker


def safe_json_dumps(data, indent=2):
    def default(o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )

    return json.dumps(data, indent=indent, default=default)


def hash_chunk(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class OpenAPIChunker(BaseChunker):
    """
    Concrete implementation of BaseChunker for OpenAPI specs.
    """

    def create_chunk(
        self, chunk_type: str, spec_id: str, name: str, content_data: dict
    ) -> Dict:
        content_json = safe_json_dumps(content_data)
        chunk_id = hash_chunk(content_json)
        return {
            "id": chunk_id,
            "type": chunk_type,
            "spec_id": spec_id,
            "name": name,
            "content": content_json,
        }

    def extract_openapi_version(self, openapi: dict, spec_id: str) -> List[Dict]:
        version = openapi.get("openapi")
        if not version:
            return []
        return [
            self.create_chunk(
                "version", spec_id, "OpenAPI Version", {"openapi": version}
            )
        ]

    def extract_info(self, openapi: dict, spec_id: str) -> List[Dict]:
        info = openapi.get("info", {})
        if not info:
            return []
        return [self.create_chunk("info", spec_id, "API Info", info)]

    def extract_servers(self, openapi: dict, spec_id: str) -> List[Dict]:
        servers = openapi.get("servers", [])
        if not servers:
            return []
        return [self.create_chunk("servers", spec_id, "Server Environments", servers)]

    def extract_paths(self, openapi: dict, spec_id: str) -> List[Dict]:
        chunks = []
        paths = openapi.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                chunks.append(
                    self.create_chunk(
                        "path", spec_id, f"{method.upper()} {path}", details
                    )
                )
        return chunks

    def extract_components(self, openapi: dict, spec_id: str) -> List[Dict]:
        chunks = []
        components = openapi.get("components", {})
        for section, items in components.items():
            for name, content in items.items():
                chunks.append(self.create_chunk(section, spec_id, name, content))
        return chunks

    def extract_global_security(self, openapi: dict, spec_id: str) -> List[Dict]:
        security = openapi.get("security", [])
        if not security:
            return []
        return [
            self.create_chunk(
                "globalSecurity", spec_id, "Global Security Requirements", security
            )
        ]

    def extract_tags(self, openapi: dict, spec_id: str) -> List[Dict]:
        tags = openapi.get("tags", [])
        if not tags:
            return []
        return [self.create_chunk("tags", spec_id, "Global Tags", tags)]

    def chunk(self, oas_yaml_str: str, spec_id: str) -> List[Dict[str, Any]]:
        try:
            openapi = yaml.safe_load(oas_yaml_str)
        except yaml.YAMLError as e:
            print(f"YAML parsing failed for {spec_id}: {e}")
            return []

        if not isinstance(openapi, dict) or "openapi" not in openapi:
            print(f"Skipping {spec_id}: Not an OpenAPI spec.")
            return []

        chunks = []
        chunks += self.extract_openapi_version(openapi, spec_id)
        chunks += self.extract_info(openapi, spec_id)
        chunks += self.extract_servers(openapi, spec_id)
        chunks += self.extract_paths(openapi, spec_id)
        chunks += self.extract_components(openapi, spec_id)
        chunks += self.extract_global_security(openapi, spec_id)
        chunks += self.extract_tags(openapi, spec_id)
        return chunks

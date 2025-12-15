import json
import hashlib
from jsonschema import validate, ValidationError
from pathlib import Path

SCHEMA_PATH = Path(__file__).parents[2] / "brains" / "TSLA_1h" / "brain_schema_v1.json"

class BrainLoadError(Exception):
    pass


def _feature_hash(feature_list):
    s = "|".join(feature_list)
    return hashlib.sha256(s.encode()).hexdigest()


class BrainLoader:
    def __init__(self, path: str):
        self.path = Path(path)
        if not self.path.exists():
            raise BrainLoadError(f"Brain file not found: {path}")
        with open(self.path, "r") as f:
            self.data = json.load(f)
        try:
            validate(instance=self.data, schema=json.loads(SCHEMA_PATH.read_text()))
        except ValidationError as e:
            raise BrainLoadError(f"Schema validation failed: {e}")

    def feature_hash_ok(self, runtime_feature_list):
        expected = self.data.get("feature_hash")
        if not expected:
            return False
        return expected == _feature_hash(runtime_feature_list)

    def get_model(self):
        return self.data.get("model")

    def get_signal_def(self):
        return self.data.get("signal_definition")

    def get_risk_profile(self):
        return self.data.get("risk_profile")

    def get_expected_stats(self):
        return self.data.get("expected_stats")

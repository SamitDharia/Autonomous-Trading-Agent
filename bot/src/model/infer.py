import math

def predict_from_linear_model(model, features: dict):
    """Given a model dict with 'bias' and 'weights', compute z, confidence and direction."""
    bias = float(model.get("bias", 0.0))
    weights = model.get("weights", {})
    z = bias
    for k, w in weights.items():
        z += float(w) * float(features.get(k, 0.0))
    conf = 1.0 / (1.0 + math.exp(-z))
    direction = 1 if z >= 0 else -1
    return direction, conf, z

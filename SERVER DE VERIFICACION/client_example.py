import requests
import json
import time

SERVER = "http://localhost:5000"


def generate_key(duration_days=30, client_name="TestClient"):
    resp = requests.post(f"{SERVER}/generate", json={
        "duration_days": duration_days,
        "client_name": client_name,
    })
    return resp.json()


def validate_key(license_key):
    resp = requests.get(f"{SERVER}/validate", params={"key": license_key})
    return resp.json()


def verify_token(token):
    resp = requests.post(f"{SERVER}/verify-token", json={"token": token})
    return resp.json()


if __name__ == "__main__":
    print("=== Generar una licencia ===")
    lic = generate_key(duration_days=365, client_name="MiCliente")
    print(json.dumps(lic, indent=2))
    key = lic["key"]

    print("\n=== Validar la licencia ===")
    validation = validate_key(key)
    print(json.dumps(validation, indent=2))

    if "token" in validation:
        print("\n=== Verificar token localmente ===")
        verification = verify_token(validation["token"])
        print(json.dumps(verification, indent=2))

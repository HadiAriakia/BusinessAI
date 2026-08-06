
import jsonschema
import pytest

from tests.conftest import REGISTRATION


@pytest.fixture
def spec(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def response_schema(spec, path, method, status):
    """The declared schema for one response, resolvable against components."""
    schema = spec["paths"][path][method]["responses"][status]["content"][
        "application/json"
    ]["schema"]
    # $defs lets jsonschema follow the $ref into components/schemas.
    return {**schema, "$defs": spec["components"]["schemas"]}


def resolve_refs(schema):
    """OpenAPI writes #/components/schemas/X; jsonschema needs #/$defs/X."""
    if isinstance(schema, dict):
        return {
            key: (
                value.replace("#/components/schemas/", "#/$defs/")
                if key == "$ref"
                else resolve_refs(value)
            )
            for key, value in schema.items()
        }
    if isinstance(schema, list):
        return [resolve_refs(item) for item in schema]
    return schema


def assert_conforms(spec, path, method, status, body):
    schema = resolve_refs(response_schema(spec, path, method, status))
    jsonschema.validate(instance=body, schema=schema)


def test_register_response_matches_its_schema(client, spec):
    response = client.post("/auth/register", json=REGISTRATION)

    assert response.status_code == 201
    assert_conforms(spec, "/auth/register", "post", "201", response.json())


def test_login_response_matches_its_schema(client, spec, registered):
    response = client.post(
        "/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )

    assert response.status_code == 200
    assert_conforms(spec, "/auth/login", "post", "200", response.json())


def test_me_response_matches_its_schema(client, spec, auth_header):
    response = client.get("/me", headers=auth_header)

    assert response.status_code == 200
    assert_conforms(spec, "/me", "get", "200", response.json())


def test_validation_error_matches_its_schema(client, spec):
    response = client.post("/auth/register", json={"username": "x"})

    assert response.status_code == 422
    assert_conforms(spec, "/auth/register", "post", "422", response.json())


def test_user_schema_does_not_expose_password_hash(spec):
    properties = spec["components"]["schemas"]["UserResponse"]["properties"]

    assert set(properties) == {"id", "username", "email"}


def test_protected_routes_declare_their_auth_requirement(spec):
    assert spec["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    # /me requires the token; the auth endpoints must not, or a client could
    # never obtain one.
    assert spec["paths"]["/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "security" not in spec["paths"]["/auth/login"]["post"]
    assert "security" not in spec["paths"]["/auth/register"]["post"]


def test_documented_status_codes_are_present(spec):
    assert set(spec["paths"]["/auth/register"]["post"]["responses"]) >= {
        "201",
        "409",
        "422",
    }
    assert set(spec["paths"]["/auth/login"]["post"]["responses"]) >= {
        "200",
        "401",
        "422",
    }
    assert set(spec["paths"]["/me"]["get"]["responses"]) >= {"200", "401"}

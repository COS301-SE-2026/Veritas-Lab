import json
import uuid
import pytest
import pytest_asyncio
from app.auth.auth import COOKIE_NAME

@pytest_asyncio.fixture
async def single_case_context(case_assignment_context):
    ctx = case_assignment_context

    ctx["media_ids"] = []
    ctx["media_type_ids"] = []

    try:
        yield ctx

    finally:
        await ctx["conn"].execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            ctx["investigator_id"]
        )

        for media_id in ctx["media_ids"]:
            await ctx["conn"].execute(
                """
                DELETE FROM "Cases_DB"."Media"
                WHERE mediaid = $1
                """,
                uuid.UUID(media_id)
            )

        for media_type_id in ctx["media_type_ids"]:
            await ctx["conn"].execute(
                """
                DELETE FROM "Cases_DB"."MediaType"
                WHERE mediatypeid = $1
                """,
                uuid.UUID(media_type_id)
            )

async def seed_case(
    ctx,
    creator=None,
    state="OPEN",
    name="Integration test case",
    description="Case used for integration testing"
):
    if creator is None:
        creator = ctx["creator_name"]

    case_id = uuid.uuid4()

    await ctx["conn"].execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        ctx["creator_id"]
    )

    await ctx["conn"].execute(
        """
        INSERT INTO "Cases_DB"."Cases"
        (
            caseid,
            casename,
            casecreator,
            casedescription,
            casestate
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5::case_state_enum
        )
        """,
        case_id,
        name,
        creator,
        description,
        state
    )

    ctx["cases"].append(str(case_id))

    return str(case_id)

async def seed_pnp_model(
    ctx,
    media_id,
    model_name="TestModel",
    classification="AI",
    confidence=0.91,
    file_name="test.onnx"
):
    model_result = {
        "modelName": model_name,
        "fileName": file_name,
        "results": {
            "classification": classification,
            "confidence": confidence
        },
        "config": {},
        "date": "2026-09-26T14:00:00Z"
    }

    row = await ctx["conn"].fetchrow(
        """
        INSERT INTO "Cases_DB"."PNPModels"
            (
                MediaId,
                ModelName,
                ModelResult
            )
        VALUES
            (
                $1,
                $2,
                $3::jsonb
            )
        RETURNING PNPModelId
        """,
        uuid.UUID(media_id),
        model_name,
        json.dumps(model_result)
    )

    return {
        "pnp_model_id": row["pnpmodelid"],
        "model_result": model_result
    }

async def seed_media(ctx):
    media_type_id = uuid.uuid4()
    media_id = uuid.uuid4()

    suffix = uuid.uuid4().hex[:6]

    await ctx["conn"].execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        ctx["investigator_id"]
    )

    await ctx["conn"].execute(
        """
        INSERT INTO "Cases_DB"."MediaType"
        (
            mediatypeid,
            medianame,
            mediabucket,
            mediaextension
        )
        VALUES (
            $1,
            $2,
            $3,
            $4
        )
        """,
        media_type_id,
        f"Test Image {suffix}",
        "test-bucket",
        f".{suffix}"
    )

    await ctx["conn"].execute(
        """
        INSERT INTO "Cases_DB"."Media"
        (
            mediaid,
            mediatype,
            mediahash,
            mediaannotations,
            reportartifacts,
            reportfindings,
            reportcomments,
            reportcertainty,
            reportdatecreation
        )
        VALUES (
            $1,
            $2,
            $3,
            $4::jsonb,
            $5::jsonb,
            $6,
            $7,
            $8,
            CURRENT_TIMESTAMP
        )
        """,
        media_id,
        media_type_id,
        f"hash-{uuid.uuid4()}",
        json.dumps([
            {
                "type": "test",
                "value": "annotation"
            }
        ]),
        json.dumps({
            "artifact": "test-artifact"
        }),
        json.dumps({
            "risk_level": 3,
            "ai_probability": 0.12,
            "classification": "Authentic",
            "findings": "No manipulation detected."
        }),
        "Reviewed by investigator.",
        3
    )

    await ctx["conn"].execute(
        """
        INSERT INTO "Cases_DB"."AutomatedAnnotations"
        (
            MediaId,
            MediaAnnotations
        )
        VALUES (
            $1,
            $2::jsonb
        )
        """,
        media_id,
        json.dumps([
            {
                "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "kind": "shape",
                "source": "AI",
                "points": [
                    {"x": 10.0, "y": 10.0},
                    {"x": 50.0, "y": 10.0},
                    {"x": 50.0, "y": 50.0},
                    {"x": 10.0, "y": 50.0},
                    {"x": 10.0, "y": 10.0}
                ]
            }
        ])
    )

    ctx["media_ids"].append(str(media_id))
    ctx["media_type_ids"].append(str(media_type_id))

    return str(media_id)

async def attach_evidence(
    ctx,
    case_id,
    media_id,
    perspective="Front view"
):
    await ctx["conn"].execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        ctx["creator_id"]
    )

    await ctx["conn"].execute(
        """
        UPDATE "Cases_DB"."Cases"
        SET evidence = ARRAY[
            ROW(
                $2::uuid,
                $3::text
            )::"Cases_DB".evidence_type
        ]
        WHERE caseid = $1
        """,
        uuid.UUID(case_id),
        uuid.UUID(media_id),
        perspective
    )

@pytest.mark.asyncio
async def test_user_can_view_own_open_case(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])
    response = client.get(f"/api/getSingleCase/{case_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["case"]["caseId"] == case_id
    assert body["case"]["caseState"] == "OPEN"

@pytest.mark.asyncio
async def test_user_cannot_view_another_users_case(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    client.cookies.set(COOKIE_NAME,ctx["user_token"])

    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Case not found"
    }

@pytest.mark.asyncio
async def test_investigator_can_view_published_case(client, single_case_context):
    ctx = single_case_context
    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["case"]["caseState"] == "PUBLISHED"

@pytest.mark.asyncio
async def test_investigator_can_view_closed_case(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="CLOSED"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 200, response.text
    assert response.json()["case"]["caseState"] == "CLOSED"

@pytest.mark.asyncio
async def test_investigator_cannot_view_another_users_open_case(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_admin_can_view_published_case(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])

    response = client.get(f"/api/getSingleCase/{case_id}")

    assert response.status_code == 200, response.text
    assert response.json()["case"]["caseState"] == "PUBLISHED"

@pytest.mark.asyncio
async def test_user_open_case_hides_report_data(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="OPEN"
    )

    media_id = await seed_media(ctx)

    await attach_evidence(
        ctx,
        case_id,
        media_id,
        "Front view"
    )

    await seed_pnp_model(
        ctx,
        media_id,
        model_name="HiddenModel"
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.get(f"/api/getSingleCase/{case_id}")

    assert response.status_code == 200, response.text
    evidence = response.json()["evidence"]
    assert len(evidence) == 1
    item = evidence[0]
    assert item["mediaId"] == media_id
    assert item["casePerspective"] == "Front view"
    assert "annotations" not in item
    assert "reportArtifacts" not in item
    assert "reportFindings" not in item
    assert "reportComments" not in item
    assert "reportCertainty" not in item
    assert "reportDateCreation" not in item
    assert "automatedAnnotations" not in item
    assert "plugAndPlay" not in item

@pytest.mark.asyncio
async def test_user_closed_case_can_view_report_data(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="CLOSED"
    )

    media_id = await seed_media(ctx)

    await attach_evidence(
        ctx,
        case_id,
        media_id,
        "Rear view"
    )

    pnp = await seed_pnp_model(
        ctx,
        media_id,
        model_name="ClosedCaseModel",
        classification="AI",
        confidence=0.88
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 200, response.text
    evidence = response.json()["evidence"]
    assert len(evidence) == 1

    item = evidence[0]

    assert "plugAndPlay" in item
    assert len(item["plugAndPlay"]) == 1

    pnp_item = item["plugAndPlay"][0]

    assert pnp_item["PNPModelId"] == pnp["pnp_model_id"]
    assert pnp_item["mediaId"] == media_id
    assert pnp_item["modelName"] == "ClosedCaseModel"

    assert pnp_item["modelResult"]["modelName"] == "ClosedCaseModel"
    assert pnp_item["modelResult"]["results"]["classification"] == "AI"
    assert pnp_item["modelResult"]["results"]["confidence"] == 0.88

    assert pnp_item["uploadDate"] is not None
    assert item["mediaId"] == media_id
    assert item["casePerspective"] == "Rear view"
    assert "annotations" in item
    assert "reportArtifacts" in item

    assert item["reportFindings"] == {
        "risk_level": 3,
        "ai_probability": 0.12,
        "classification": "Authentic",
        "findings": "No manipulation detected."
    }

    assert item["reportComments"] == "Reviewed by investigator."
    assert item["reportCertainty"] == 3
    assert item["reportDateCreation"] is not None

    assert "automatedAnnotations" in item

    assert item["annotations"] == [
        {
            "type": "test",
            "value": "annotation"
        }
    ]

    assert item["automatedAnnotations"] == [
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "kind": "shape",
            "source": "AI",
            "points": [
                {"x": 10.0, "y": 10.0},
                {"x": 50.0, "y": 10.0},
                {"x": 50.0, "y": 50.0},
                {"x": 10.0, "y": 50.0},
                {"x": 10.0, "y": 10.0}
            ]
        }
    ]

@pytest.mark.asyncio
async def test_investigator_can_view_report_data(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    media_id = await seed_media(ctx)

    await attach_evidence(
        ctx,
        case_id,
        media_id,
        "Side view"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    pnp = await seed_pnp_model(
        ctx,
        media_id,
        model_name="InvestigatorModel",
        classification="AUTHENTIC",
        confidence=0.96
    )

    response = client.get(f"/api/getSingleCase/{case_id}")

    assert response.status_code == 200, response.text
    evidence = response.json()["evidence"]
    assert len(evidence) == 1
    item = evidence[0]
    assert item["mediaId"] == media_id
    assert item["casePerspective"] == "Side view"
    assert "annotations" in item
    assert "reportArtifacts" in item
    assert "automatedAnnotations" in item
    assert item["reportFindings"] == {
        "risk_level": 3,
        "ai_probability": 0.12,
        "classification": "Authentic",
        "findings": "No manipulation detected."
    }

    assert item["reportComments"] == "Reviewed by investigator."
    assert item["reportCertainty"] == 3

    assert item["annotations"] == [
        {
            "type": "test",
            "value": "annotation"
        }
    ]

    assert item["automatedAnnotations"] == [
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "kind": "shape",
            "source": "AI",
            "points": [
                {"x": 10.0, "y": 10.0},
                {"x": 50.0, "y": 10.0},
                {"x": 50.0, "y": 50.0},
                {"x": 10.0, "y": 50.0},
                {"x": 10.0, "y": 10.0}
            ]
        }
    ]

    assert "plugAndPlay" in item
    assert len(item["plugAndPlay"]) == 1

    pnp_item = item["plugAndPlay"][0]

    assert pnp_item["PNPModelId"] == pnp["pnp_model_id"]
    assert pnp_item["mediaId"] == media_id
    assert pnp_item["modelName"] == "InvestigatorModel"

    assert pnp_item["modelResult"]["results"]["classification"] == "AUTHENTIC"
    assert pnp_item["modelResult"]["results"]["confidence"] == 0.96
    assert pnp_item["uploadDate"] is not None

@pytest.mark.asyncio
async def test_get_single_case_not_found(client, single_case_context):
    ctx = single_case_context
    missing_case_id = str(uuid.uuid4())
    client.cookies.set(
        COOKIE_NAME,
        ctx["investigator_token"]
    )

    response = client.get(f"/api/getSingleCase/{missing_case_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Case not found"
    }

@pytest.mark.asyncio
async def test_get_single_case_requires_authentication(client, single_case_context):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="OPEN"
    )

    client.cookies.clear()
    response = client.get(f"/api/getSingleCase/{case_id}")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_single_case_returns_multiple_pnp_models_for_same_evidence(
    client,
    single_case_context
):
    ctx = single_case_context

    case_id = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    media_id = await seed_media(ctx)

    await attach_evidence(
        ctx,
        case_id,
        media_id,
        "Front view"
    )

    pnp_one = await seed_pnp_model(
        ctx,
        media_id,
        model_name="ModelA",
        classification="AI",
        confidence=0.91,
        file_name="model-a.onnx"
    )

    pnp_two = await seed_pnp_model(
        ctx,
        media_id,
        model_name="ModelB",
        classification="AUTHENTIC",
        confidence=0.87,
        file_name="model-b.onnx"
    )

    client.cookies.set(
        COOKIE_NAME,
        ctx["investigator_token"]
    )

    response = client.get(
        f"/api/getSingleCase/{case_id}"
    )

    assert response.status_code == 200, response.text

    body = response.json()
    evidence = body["evidence"]

    # The SQL JOIN produces two DB rows,
    # but the API must still return one evidence object.
    assert len(evidence) == 1

    item = evidence[0]

    assert item["mediaId"] == media_id
    assert "plugAndPlay" in item
    assert len(item["plugAndPlay"]) == 2

    pnp_by_name = {
        result["modelName"]: result
        for result in item["plugAndPlay"]
    }

    assert set(pnp_by_name.keys()) == {
        "ModelA",
        "ModelB"
    }

    model_a = pnp_by_name["ModelA"]

    assert model_a["PNPModelId"] == pnp_one["pnp_model_id"]
    assert model_a["mediaId"] == media_id
    assert model_a["modelResult"]["fileName"] == "model-a.onnx"
    assert model_a["modelResult"]["results"]["classification"] == "AI"
    assert model_a["modelResult"]["results"]["confidence"] == 0.91
    assert model_a["uploadDate"] is not None

    model_b = pnp_by_name["ModelB"]

    assert model_b["PNPModelId"] == pnp_two["pnp_model_id"]
    assert model_b["mediaId"] == media_id
    assert model_b["modelResult"]["fileName"] == "model-b.onnx"
    assert model_b["modelResult"]["results"]["classification"] == "AUTHENTIC"
    assert model_b["modelResult"]["results"]["confidence"] == 0.87
    assert model_b["uploadDate"] is not None
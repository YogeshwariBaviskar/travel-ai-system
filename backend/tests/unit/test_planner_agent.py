import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.planner_agent import PlannerAgent


MOCK_PLAN = {
    "title": "5 Days in Paris",
    "summary": "A wonderful trip through the City of Light.",
    "total_days": 5,
    "estimated_total_cost": 2000.0,
    "currency": "USD",
    "days": [
        {
            "day": 1,
            "date": "2026-06-01",
            "location": "Paris",
            "morning": {"name": "Eiffel Tower", "description": "Visit the iconic tower.", "duration_hours": 3.0, "estimated_cost": 30.0},
            "afternoon": {"name": "Louvre Museum", "description": "World-class art.", "duration_hours": 3.0, "estimated_cost": 20.0},
            "evening": {"name": "Dinner in Le Marais", "description": "French cuisine.", "duration_hours": 2.0, "estimated_cost": 60.0},
            "accommodation": {"name": "Hotel de Ville", "area": "Le Marais", "cost_per_night": 150.0},
        }
    ],
    "tips": ["Book Eiffel Tower tickets in advance.", "Get a Navigo travel card."],
}


def _make_mock_response(plan: dict) -> MagicMock:
    tool_call = MagicMock()
    tool_call.function.name = "create_trip_plan"
    tool_call.function.arguments = json.dumps(plan)

    message = MagicMock()
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def agent():
    return PlannerAgent()


@pytest.fixture
def sample_request():
    return {
        "destination": "Paris, France",
        "start_date": "2026-06-01",
        "end_date": "2026-06-06",
        "budget": 2500,
        "interests": ["Art", "Food"],
        "num_travelers": 1,
    }


@pytest.mark.asyncio
async def test_plan_returns_dict(agent, sample_request):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(agent.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await agent.plan(sample_request)

    assert isinstance(result, dict)
    assert result["title"] == "5 Days in Paris"
    assert len(result["days"]) == 1


@pytest.mark.asyncio
async def test_plan_contains_required_keys(agent, sample_request):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(agent.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await agent.plan(sample_request)

    for key in ("title", "summary", "total_days", "estimated_total_cost", "currency", "days", "tips"):
        assert key in result, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_plan_day_has_all_slots(agent, sample_request):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(agent.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await agent.plan(sample_request)

    day = result["days"][0]
    for slot in ("morning", "afternoon", "evening", "accommodation"):
        assert slot in day


@pytest.mark.asyncio
async def test_plan_raises_when_no_tool_use(agent, sample_request):
    choice = MagicMock()
    choice.message.tool_calls = None
    response = MagicMock()
    response.choices = [choice]
    with patch.object(agent.client.chat.completions, "create", new=AsyncMock(return_value=response)):
        with pytest.raises(ValueError, match="no trip plan returned"):
            await agent.plan(sample_request)


@pytest.mark.asyncio
async def test_run_delegates_to_plan(agent, sample_request):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(agent.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await agent.run(sample_request)

    assert result["title"] == MOCK_PLAN["title"]

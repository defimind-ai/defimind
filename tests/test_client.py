"""Client unit tests — construction + payload parsing. No live call needed."""

from defimind.client import DefiMindClient, extract_payload


class _Block:
    def __init__(self, text):
        self.text = text


class _Result:
    def __init__(self, content=None, structured=None):
        self.content = content or []
        self.structuredContent = structured


# A captured-shape CheckPoolHealth payload as the live server delivers it:
# JSON *text* in a content block, structuredContent absent.
CHECKPOOLHEALTH_TEXT = '{"version": "V3", "token0_name": "USDC", "has_activity": false}'


def test_client_constructs():
    c = DefiMindClient("https://mcp.defimind.ai/mcp")
    assert c._endpoint == "https://mcp.defimind.ai/mcp"
    assert c._session is None


def test_extract_payload_parses_json_text():
    # The branch the live DeFiMind endpoint actually uses.
    res = _Result(content=[_Block(CHECKPOOLHEALTH_TEXT)], structured=None)
    payload = extract_payload(res)
    assert payload["version"] == "V3"
    assert payload["has_activity"] is False


def test_extract_payload_prefers_structured():
    res = _Result(content=[_Block('{"x": 1}')], structured={"y": 2})
    assert extract_payload(res) == {"y": 2}


def test_extract_payload_non_json_text_passthrough():
    res = _Result(content=[_Block("not json")], structured=None)
    assert extract_payload(res) == "not json"


def test_extract_payload_empty_result():
    out = extract_payload(_Result(content=[], structured=None))
    assert out["_note"] == "empty result"

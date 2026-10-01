from nlp.extractor import extract_entities


def test_upi_and_shortener():
    e = extract_entities("Pay to rahul@okaxis via bit.ly/abc")
    assert e["upi_ids"][0]["value"] == "rahul@okaxis"
    assert "shortened" in e["urls"][0]["reasons"][0]
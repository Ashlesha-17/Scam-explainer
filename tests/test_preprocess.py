from nlp.preprocess import preprocess


def test_hinglish_normalization():
    assert "karo" in preprocess("KYC update kro")


def test_url_replaced():
    assert "urltoken" in preprocess("click http://bad.xyz now")
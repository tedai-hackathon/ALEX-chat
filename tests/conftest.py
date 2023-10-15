import pytest


@pytest.fixture(scope="session")
def urls():
    return [
        "https://www.irs.gov/forms-pubs/about-form-ss-4",
        "https://sos.wyo.gov/Forms/Publications/ChoiceIsYours.pdf",
        "",
    ]

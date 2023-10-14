import collections
import enum
import typing

import pypdf
import requests


class FieldKind(enum.Enum):
    """Types of fields supported by PDFs."""

    TEXT = "/Tx"
    BUTTON = "/Btn"
    CHOICE = "/Ch"
    SIGNATURE = "/Sig"


# Serves as an interface to get information from the user about what to put in a field
# in the PDF form.
InputInterface = collections.abc.Callable[
    [str, FieldKind], typing.Union[bool, str, None]
]


def fill_pdf(
    reader: pypdf.PdfReader,
    writer: pypdf.PdfWriter,
    input_getter: InputInterface,
):
    """Fill a PDF with a provided reader and writer and user-interface."""
    writer.append(reader)

    for page_num, page in enumerate(reader.pages):
        fields = reader.get_fields(page)
        if fields is None:
            continue

        updates: typing.Dict[str, typing.Union[bool, str]] = {}
        for name, field in fields.items():
            if field.value is not None:
                print(field, field.value)

            value = input_getter(name, FieldKind(field.field_type))

            # Note: Some fields may be empty because not applicable, so it's best not
            # to throw an error.
            if value is not None:
                if isinstance(value, bool):
                    value = "/On" if value else "/Off"
                updates[name] = value

        writer.update_page_form_field_values(
            writer.get_page(page_num), updates, auto_regenerate=False
        )


def process_form(url: str, path: str, input_getter: InputInterface):
    """Download the PDF form at the given URL, process the PDF and fill out the fields,
    and save the processed pdf to the given file-path.
    """
    response = requests.get(url)
    reader = pypdf.PdfReader(response)
    writer = pypdf.PdfWriter()

    fill_pdf(reader, writer, input_getter)
    with open(path, "wb") as f:
        writer.write(f)

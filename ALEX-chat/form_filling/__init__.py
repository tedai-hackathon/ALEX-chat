import collections
import enum
import typing

import pypdf


class FieldKind(enum.Enum):
    TEXT = "/Tx"
    BUTTON = "/Btn"
    CHOICE = "/Ch"
    SIGNATURE = "/Sig"


def fill_pdf(
    reader: pypdf.PdfReader,
    writer: pypdf.PdfWriter,
    retriever: collections.abc.Callable[
        [str, FieldKind], typing.Union[bool, str, None]
    ],
):
    """Fills a PDF with a provided reader and writer, as well as a "retriever" function
    that gets information from the user.
    """
    writer.append(reader)

    for page_num, page in enumerate(reader.pages):
        fields = reader.get_fields(page)
        if fields is None:
            continue

        updates: typing.Dict[str, typing.Union[bool, str]] = {}
        for name, field in fields.items():
            if field.value is not None:
                print(field, field.value)

            value = retriever(name, FieldKind(field.field_type))

            # Note: Some fields may be empty because not applicable, so it's best not
            # to throw an error.
            if value is not None:
                if isinstance(value, bool):
                    value = "/On" if value else "/Off"
                updates[name] = value

        writer.update_page_form_field_values(
            writer.get_page(page_num), updates, auto_regenerate=False
        )

from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminDocumentChooser


class BaseDocumentChooserPanel(BaseChooserPanel):
    object_type_name = "document"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminDocumentChooser}


class DocumentChooserPanel:
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_DocumentChooserPanel'), (BaseDocumentChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
        })

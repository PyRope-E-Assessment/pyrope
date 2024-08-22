

class Message:

    def __init__(self, sender):
        self.sender = sender


class ChangeWidgetAttribute(Message):

    def __init__(self, sender, widget_id, attribute_name, attribute_value):
        Message.__init__(self, sender)
        self.widget_id = widget_id
        self.attribute_name = attribute_name
        self.attribute_value = attribute_value

    def __str__(self):
        value = self.attribute_value
        if isinstance(self.attribute_value, str):
            value = f"'{self.attribute_value}'"
        return (
            f"{self.sender}: '{self.attribute_name}' set to "
            f"{value}."
        )


class CreateWidget(Message):

    def __init__(self, sender, widget_id, widget_type):
        Message.__init__(self, sender)
        self.widget_id = widget_id
        self.widget_type = widget_type

    def __str__(self):
        return (
            f'{self.sender}: Create {self.widget_type} widget with ID '
            f'{self.widget_id}.'
        )


class ExerciseAttribute(Message):

    def __init__(self, sender, attribute_name, attribute_value):
        Message.__init__(self, sender)
        self.attribute_name = attribute_name
        self.attribute_value = attribute_value

    def __str__(self):
        return (
            f'{self.sender}: {self.attribute_name} set to '
            f'{self.attribute_value}.'
        )


class RenderTemplate(Message):

    def __init__(self, sender, template_type, template):
        Message.__init__(self, sender)
        self.template_type = template_type
        self.template = template

    def __str__(self):
        return f'{self.sender}: Render {self.template_type}.'


class Submit(Message):

    def __str__(self):
        return f'{self.sender}: Exercise submitted.'


class WaitingForSubmission(Message):

    def __str__(self):
        return f'{self.sender}: Wait for submission.'


class WidgetValidationError(Message):

    def __init__(self, sender, error, widget_id):
        Message.__init__(self, sender)
        self.error = error
        self.widget_id = widget_id

    def __str__(self):
        return f'{self.sender}: {self.error}'

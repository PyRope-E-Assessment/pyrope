
import re


class TemplateFormatter:

    @classmethod
    def format(cls, template, **kwargs):
        template = '\n'.join([line.strip() for line in template.split('\n')])
        result = []
        for literal_text, field_name, format_spec in cls.parse(template):

            if literal_text:
                result.append(literal_text)

            if field_name is not None:
                obj = cls.get_field(field_name, format_spec, kwargs)
                result.append(cls.format_field(obj, format_spec))

        return ''.join(result).replace(r'\<\<', '<<').replace(r'\>\>', '>>')

    @staticmethod
    def parse(s):
        text_start = 0
        for match in re.finditer(r'<<[^>]*>>', s):
            field_start, field_end = match.span()
            field = s[field_start + 2:field_end - 2]
            field_name, *format_spec = field.split(':', maxsplit=1)
            format_spec = format_spec[0] if format_spec else None
            literal_text = s[text_start:field_start]
            text_start = field_end
            yield literal_text, field_name, format_spec
        yield s[text_start:], None, None

    @staticmethod
    def get_field(field_name, format_spec, kwargs):
        if format_spec is None:
            field_template = f'<<{field_name}>>'
        else:
            field_template = f'<<{field_name}:{format_spec}>>'
        obj = kwargs.get(field_name, field_template)
        return str(obj)

    @staticmethod
    def format_field(obj, format_spec):
        if format_spec is None:
            return obj
        elif format_spec == 'latex':
            return obj.strip(' $')
        else:
            raise ValueError(f'Unknown format specifier "{format_spec}".')

from django.utils.encoding import force_text
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, list):
            error_msg = force_text(response.data[0])
        elif isinstance(response.data, dict):
            error_list = [(key, force_text(value[0]) if isinstance(value, list) else force_text(value)) for key, value
                          in response.data.items()]
            error = error_list[0]
            error_msg = '%s：%s' % error if error[0] not in ['detail', '__all__', 'non_field_errors'] else error[1]
        else:
            error_msg = force_text(response.data)
        del response.data
        response.data = dict()
        response.data['msg'] = error_msg
        response.data['code'] = response.status_code
        response.status_code = 200    # in order to display the error msg
    return response

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, list):
            error_msg = response.data[0]
        else:
            error_list = [(key, value[0] if isinstance(value, list) else repr(value)) for key, value in
                          response.data.items()]
            error_msg = '%s参数有误：%s' % error_list[0]

        del response.data
        response.data = dict()
        response.data['msg'] = error_msg
        response.data['code'] = response.status_code
        response.status_code = 200    # in order to display the error msg
    return response

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        error_msg_list = []
        for key, value in response.data.items():
            if isinstance(value, list):
                error_msg_list.append('%s参数有误：%s' % (key, ' '.join(value)))
            else:
                error_msg_list.append(str(value))
            del response.data[key]
        response.data['msg'] = '\n'.join(error_msg_list)
        response.data['code'] = response.status_code
        response.status_code = 200    # in order to display the error msg
    return response

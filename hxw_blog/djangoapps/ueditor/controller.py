import codecs
import json
import os
import random
from datetime import *

from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

ROOT = settings.ENV_ROOT


# 本地上传图片时构造json返回值
class JsonResult(object):
    def __init__(self, state="未知错误", url="", title="", original="", error="null"):
        super(JsonResult, self).__init__()
        self.state = state
        self.url = url
        self.title = title
        self.original = original
        self.error = error


# 构造返回json
def build_json_result(result):
    json_data = {
        "state": result.state,
        "url": result.url,
        "title": result.title,
        "original": result.original,
        "error": result.error
    }
    return json_data


def build_file_name(filename):
    dt = datetime.now()
    name, ext = os.path.splitext(filename)
    return dt.strftime("%Y%m%d%M%H%S{0}{1}".format(random.randint(1, 999999), ext))


# 读取json文件
def get_config_content():
    json_file = os.path.join(ROOT, "ueconfig.json")
    with open(json_file, 'r') as load_f:
        content = json.load(load_f)
    return content


# 上传配置类
class UploadConfig(object):
    def __init__(self, PathFormat, UploadFieldName, SizeLimit, AllowExtensions, SavePath, Base64, Base64Filename):
        super(UploadConfig, self).__init__()
        self.PathFormat = PathFormat
        self.UploadFieldName = UploadFieldName
        self.SizeLimit = SizeLimit
        self.AllowExtensions = AllowExtensions
        self.SavePath = SavePath
        self.Base64 = Base64
        self.Base64Filename = Base64Filename


# 获取json配置中的某属性值
def get_config_value(key):
    config = get_config_content()
    return config[key]


# 检查文件扩展名是否在允许的扩展名内
def check_file_type(filename, AllowExtensions):
    exts = list(AllowExtensions)
    name, ext = os.path.splitext(filename)
    return ext in exts


def check_file_size(filesize, SizeLimit):
    return filesize < SizeLimit


# 处理上传图片、文件、视频文件
@csrf_exempt
def upload_file_view(request, config):
    result = JsonResult()
    if config.Base64:
        pass
    else:
        buf = request.FILES.get(config.UploadFieldName)
        filename = buf.name
        if not check_file_type(filename,config.AllowExtensions):
            result.error = "不允许的文件格式"
            return JsonResponse(build_json_result(result))

        if not check_file_size(buf.size,config.SizeLimit):
            result.error = "文件大小超出服务器限制"
            return JsonResponse(build_json_result(result))

        try:
            truelyName = build_file_name(filename)
            webUrl = config.SavePath + truelyName
            savePath = ROOT + webUrl
            f = codecs.open(savePath, "wb")
            for chunk in buf.chunks():
                f.write(chunk)
            f.flush()
            f.close()
            result.state = "SUCCESS"
            result.url = truelyName
            result.title = truelyName
            result.original = truelyName
            response = JsonResponse(build_json_result(result))
            response["Content-Type"] = "text/plain"
            return response
        except Exception as e:
            result.error = "网络错误"
            return JsonResponse(build_json_result(result))


# 处理在线图片与在线文件
# 返回的数据格式：{"state":"SUCCESS","list":[{"url":"upload/image/20140627/6353948647502438222009315.png"},{"url":"upload/image/20140627/6353948659383617789875352.png"},{"url":"upload/image/20140701/6353980733328090063690725.png"},{"url":"upload/image/20140701/6353980745691597223366891.png"},{"url":"upload/image/20140701/6353980747586705613811538.png"},{"url":"upload/image/20140701/6353980823509548151892908.png"}],"start":0,"size":20,"total":6}
def list_file_manage(request, imageManagerListPath, imageManagerAllowFiles, listsize):
    pstart = request.GET.get("start")
    start = pstart is None and int(pstart) or 0
    psize = request.GET.get("size")
    size = psize is None and int(get_config_value(listsize)) or int(psize)
    localPath = ROOT + imageManagerListPath
    filelist = []
    exts = list(imageManagerAllowFiles)
    index = start
    for imagename in os.listdir(localPath):
        name, ext = os.path.splitext(imagename)
        if ext in exts:
            filelist.append(dict(url=imagename))
            index += 1
            if index - start >= size:
                break
    json_data = {
        "state": "SUCCESS",
        "list": filelist,
        "start": start,
        "size": size,
        "total": index
    }
    return JsonResponse(json_data)


# 返回配置信息
def config_handler(request):
    content = get_config_content()
    callback = request.GET.get("callback")
    if callback:
        return HttpResponse("{0}{1}".format(callback, json.dumps(content)))
    return JsonResponse(content)


# 图片上传控制
@csrf_exempt
def upload_image_handler(request):
    AllowExtensions = get_config_value("imageAllowFiles")
    PathFormat = get_config_value("imagePathFormat")
    SizeLimit = get_config_value("imageMaxSize")
    UploadFieldName = get_config_value("imageFieldName")
    SavePath = get_config_value("imageUrlPrefix")
    upconfig = UploadConfig(PathFormat, UploadFieldName, SizeLimit, AllowExtensions, SavePath, False, '')
    return upload_file_view(request, upconfig)


def upload_video_handler(request):
    AllowExtensions = get_config_value("videoAllowFiles")
    PathFormat = get_config_value("videoPathFormat")
    SizeLimit = get_config_value("videoMaxSize")
    UploadFieldName = get_config_value("videoFieldName")
    SavePath = get_config_value("videoUrlPrefix")
    upconfig = UploadConfig(PathFormat, UploadFieldName, SizeLimit, AllowExtensions, SavePath, False, '')
    return upload_file_view(request, upconfig)


def upload_file_handler(request):
    AllowExtensions = get_config_value("fileAllowFiles")
    PathFormat = get_config_value("filePathFormat")
    SizeLimit = get_config_value("fileMaxSize")
    UploadFieldName = get_config_value("fileFieldName")
    SavePath = get_config_value("fileUrlPrefix")
    upconfig = UploadConfig(PathFormat, UploadFieldName, SizeLimit, AllowExtensions, SavePath, False, '')
    return upload_file_view(request,upconfig)


# 在线图片
def list_image_handler(request):
    imageManagerListPath = get_config_value("imageManagerListPath")
    imageManagerAllowFiles = get_config_value("imageManagerAllowFiles")
    imagelistsize = get_config_value("imageManagerListSize")
    return list_file_manage(request, imageManagerListPath, imageManagerAllowFiles, imagelistsize)


# 在线文件
def list_file_manager_handler(request):
    fileManagerListPath = get_config_value("fileManagerListPath")
    fileManagerAllowFiles = get_config_value("fileManagerAllowFiles")
    filelistsize = get_config_value("fileManagerListSize")
    return list_file_manage(request, fileManagerListPath, fileManagerAllowFiles, filelistsize)


actions = {
    "config": config_handler,
    "uploadimage": upload_image_handler,
    "uploadvideo": upload_video_handler,
    "uploadfile": upload_file_handler,
    "listimage": list_image_handler,
    "listfile": list_file_manager_handler
}


@csrf_exempt
def handler(request):
    action = request.GET.get("action")
    return actions.get(action)(request)

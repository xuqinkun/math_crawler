import base64
from config import *
from mongo_client import load_img_src, update_img_info
from utils import get_PNG_img


# local images need encoding
def image_encoder(image_path):
    with open(image_path, 'rb')as f:
        byte_data = base64.b64encode(f.read())
        str_data = bytes.decode(byte_data, encoding='utf-8')
    return str_data


# tencent api, both of two types provide 1000 times.
def tencent_image2str(image_path, types="characters", src="url"):
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.ocr.v20181119 import ocr_client, models
    try:
        cred = credential.Credential(Tencent_API_KEY, Tencent_SECRET_KEY)
        http_profile = HttpProfile()
        http_profile.endpoint = "ocr.ap-chengdu.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        client = ocr_client.OcrClient(cred, "ap-beijing", client_profile)  # create a connection
        req = None
        if types == "questions":
            req = models.EduPaperOCRRequest()  # questions model
        elif types == "characters":
            req = models.GeneralBasicOCRRequest()  # characters model
        params = {}
        if src == "local":
            params = '{"ImageBase64":"ImageEncoder"}'.replace("ImageEncoder", image_encoder(image_path))
        elif src == "url":
            params = '{\"ImageUrl\":\"url\"}'.replace("url", image_path)
        req.from_json_string(params)
        ret = ''
        if types == "questions":
            resp = client.EduPaperOCR(req)
            for questionsblock in resp.QuestionBlockInfos:
                for textblock in questionsblock.QuestionArr:
                    ret = ret + textblock.QuestionText + '\n'
        elif types == "characters":
            resp = client.GeneralBasicOCR(req)
            for textblock in resp.TextDetections:
                if textblock.Confidence >= 85:
                    ret = ret + textblock.DetectedText + '\n'
        return ret

    except TencentCloudSDKException as err:
        print(err)
        return test_dict


# baidu api, characters edition provide 50000 times per day
def baidu_image2str_url(uuid_url_dict = {}, types="characters"):
    from aip import AipOcr
    client = AipOcr(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY)  # create a connection
    options = {}
    options["probability"] = "true"
    uuid_text_dict = {}
    for uuid, url in uuid_url_dict.items():
        ret = ""
        resp = client.basicGeneralUrl(url, options)  # url
        print(resp)
        if "error_msg" in resp:
            print("recognition failed!  url: " + url)
            print(resp)
            if resp["error_msg"] == "url response invalid" or resp["error_msg"] == "image size error":
                #request for the image of url, convert to valid format
                image_path = get_PNG_img()
                uuid_text_dict[uuid] = baidu_image2str_local(image_path)
            else:
                uuid_text_dict[uuid] = ""
        else:
            for tex in resp["words_result"]:
                if tex["probability"]["average"] > 0.85:
                    ret = ret + tex["words"]
            uuid_text_dict[uuid] = ret
    return uuid_text_dict

def baidu_image2str_local(image_path, types="characters"):
    from aip import AipOcr
    client = AipOcr(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY)  # create a connection
    ret = ""
    options = {}
    options["probability"] = "true"
    resp = client.basicGeneral(open(image_path, "rb").read(), options)  # local
    if types == "characters":
        if "error_msg" in resp:
            print("local recognition failed!  image_path: " + image_path)
            print(resp)
            return ret
        for tex in resp["words_result"]:
            if tex["probability"]["average"] > 0.85:
                ret = ret + tex["words"]
    elif types == "questions":
        pass
    return ret

if __name__ == '__main__':
    # test_dict = {}
    # test_dict["1a4eb610-1bde-11ea-9556-91b0e0aedcea"] = "https://img.51jiaoxi.com/questions/1a4eb610-1bde-11ea-9556-91b0e0aedcea.png"
    # print(baidu_image2str_url(test_dict, "characters"))
    print(tencent_image2str("https://img.51jiaoxi.com/questions/1a4eb610-1bde-11ea-9556-91b0e0aedcea.png","questions","url"))
    print("hello")
    # imgs = load_img_src()
    # imgs_text_dict = baidu_image2str_url(imgs)
    # print(update_img_info(imgs_text_dict))
    
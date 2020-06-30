import base64
from config import *
# from mongo_client import load_img_src, update_img_info
from mongo_client import MongoDriver
from utils import image_transform,url_img_download
import argparse


# local images need encoding
def image_encoder(image_path):
    with open(image_path, 'rb')as f:
        byte_data = base64.b64encode(f.read())
        str_data = bytes.decode(byte_data, encoding='utf-8')
    return str_data


# tencent api, both of two types provide 1000 times.
def tencent_image2str_url(uuid_url_dict, types="characters"):
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.ocr.v20181119 import ocr_client, models
    uuid_text_dict = {}
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
        for uuid, url in uuid_url_dict.items():
            params = {}
            params = '{\"ImageUrl\":\"url\"}'.replace("url", url)
            print("OCR resolving %s" %url)
            req.from_json_string(params)
            ret = ''
            try:
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
                uuid_text_dict[uuid] = ret
            except TencentCloudSDKException as err:
                print(err)
                print("OCR failed! URL:%s, set text empty"%url)
                uuid_text_dict[uuid] = ''
        return uuid_text_dict

    except TencentCloudSDKException as err:
        print(err)
        return uuid_text_dict


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
            print("url recognition failed! Using local model.  url: " + url)
            print(resp)
            if resp["error_msg"] == "url response invalid" or resp["error_msg"] == "image size error":
                #request for the image of url, convert to valid format
                image_path = image_transform(url_img_download(url))
                print(image_path)
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
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip',
                        dest='ip',
                        type=str,
                        required=True,
                        help='the ip of host')
    parser.add_argument('-p', '--port',
                        dest='port',
                        type=int,
                        required=True,
                        help='the port of db')
    parser.add_argument('-t','--type',
                        dest='type',
                        type=int,
                        required=True,
                        choices=[0, 1, 2],
                        help='the type of api.\n[QUESTION_TYPE]\n0: baidu_characters\n1: tencent_characters\n2: tencent_questions')
    return parser.parse_args()

if __name__ == '__main__':
    '''
    0 : baidu characters model
    1 : tencent characters model
    2 : tencent questions model
    '''
    # test_dict = {}
    # test_dict["c92c5200-1c3e-11ea-b1ec-11621d417c16"] = "https://img.51jiaoxi.com/questions/c92c5200-1c3e-11ea-b1ec-11621d417c16.png"
    # print(baidu_image2str_url(test_dict, "characters"))
    # print(tencent_image2str(test_dict, "question"))
    args = parse_args()
    mongo_client = MongoDriver(args.ip, args.port)    

    imgs = mongo_client.load_img_src(OCR_BATCH_SIZE)
    print(len(imgs))

    #use baidu characters api
    if args.type == 0:
        imgs_text_dict = baidu_image2str_url(imgs)
    #use tencent characters api
    elif args.type == 1:
        imgs_text_dict = tencent_image2str_url(imgs)
    #use tencent questions api
    elif args.type == 2:
        imgs_text_dict = tencent_image2str_url(imgs,'questions')
    print("solved %d images"%len(imgs_text_dict))
    print(imgs_text_dict)
    print(mongo_client.update_img_info(imgs_text_dict))

    
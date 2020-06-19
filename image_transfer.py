import base64
from constant import *
# from mongo_client import load_unresolved_imgs,insert_one,update_datas

# local images need encoding
def ImageEncoder(image_path):
    with open(image_path, 'rb')as f:
        byte_data = base64.b64encode(f.read())
        str_data =bytes.decode(byte_data, encoding='utf-8')
    return str_data

#tencent api, both of two types provide 1000 times.
def tencent_image2str(image_path,types = "characters", src = "url"):
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
    from tencentcloud.ocr.v20181119 import ocr_client, models 
    try:
        cred = credential.Credential(Tencent_API_KEY, Tencent_SECRET_KEY) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.ap-chengdu.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        client = ocr_client.OcrClient(cred, "ap-beijing", clientProfile) #create a connection
        if types == "questions":
            req = models.EduPaperOCRRequest() #questions model
        elif types == "characters":
            req = models.GeneralBasicOCRRequest() #characters model
        params = {}
        if src == "local":
            params ='{"ImageBase64":"ImageEncoder"}'.replace("ImageEncoder",ImageEncoder(image_path))
        elif src == "url":
            params = '{\"ImageUrl\":\"url\"}'.replace("url",image_path)
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

#baidu api, characters edition provide 50000 times per day
def baidu_image2str(image_path, types = "characters", src = "url"):
    from aip import AipOcr

    client = AipOcr(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY) #create a connection
    ret = ""
    if src == "local":
        resp=client.basicGeneral(open(image_path,"rb").read()) #local
    elif src == "url":
        resp=client.basicGeneralUrl(image_path) #url 
    if types == "characters":
        for tex in resp["words_result"]:
            ret = ret + tex["words"]
    elif types == "questions":
        pass
    return ret

print(baidu_image2str("./test.png","characters","local"))
print(baidu_image2str("http://img.51jiaoxi.com/answer-images/9082d2c8-f08e-4588-9049-aab48f29fb24.png","characters","url"))
print(tencent_image2str("http://img.51jiaoxi.com/answer-images/9082d2c8-f08e-4588-9049-aab48f29fb24.png","questions","url"))





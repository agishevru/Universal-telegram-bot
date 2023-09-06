""" Общий модуль для работы с распознаванием фото через clarifai.com Содержит все функции.
 Для использования нужно зарегистрироваться на сайте и получить свой ключ
 доступа PAT (Personal Access Token)"""

from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
import os
from config import PAT_CLARIFAI


def image_to_tags(path_file: str) -> [[str, str], ...]:
    """ Принимает на вход адрес изображения, анализирует его, и создает для него тэги (концепты).
        Возвращает список со списками:
        :return: [['концепт1', 'значение'], ['концепт2', 'значение'] ] """

    # Your PAT (Personal Access Token) can be found in the portal under Authentification
    PAT = PAT_CLARIFAI
    USER_ID = 'clarifai'
    APP_ID = 'main'
    # Change these to whatever model and image URL you want to use
    # MODEL_ID = 'general-image-recognition'
    # MODEL_VERSION_ID = 'aa7f35c01e0642fda5cf400f543e7c40'
    MODEL_ID = 'general-image-recognition-vit'
    MODEL_VERSION_ID = '1bf8b41a7c154eaca6203643ff6a75b6'
    file = open(path_file, 'rb').read()
    # IMAGE_URL = 'https://samples.clarifai.com/metro-north.jpg'

    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)
    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            # The userDataObject is created in the overview and is required when using a PAT
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
            inputs=[resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file)))]),
        metadata=metadata)
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

    output = post_model_outputs_response.outputs[0]
    concepts_respons = []  # concept: value
    for concept in output.data.concepts:
        concepts_respons.append([concept.name, str(round(concept.value, 4))])
        # print("%s: %.2f" % (concept.name, concept.value))
    return concepts_respons


def image_to_text(path_file: str) -> str:
    """ Принимает на вход адрес изображения, анализирует его, и создает текстовое описание.
        Возвращает описание в str."""

    # Your PAT (Personal Access Token) can be found in the portal under Authentification
    PAT = PAT_CLARIFAI
    USER_ID = 'salesforce'
    APP_ID = 'blip'
    MODEL_ID = 'general-english-image-caption-blip'
    MODEL_VERSION_ID = 'cdb690f13e62470ea6723642044f95e4'
    file = open(path_file, 'rb').read()
    # IMAGE_URL = 'https://samples.clarifai.com/metro-north.jpg'

    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)
    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            # The userDataObject is created in the overview and is required when using a PAT
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
            inputs=[resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file)))]),
        metadata=metadata)
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

    output = post_model_outputs_response.outputs[0]
    text_from_image = output.data.text.raw
    return text_from_image


def translate_ensglish_to_russian(text: str) -> str:
    """ Перевод теста. Принимает на вход английский текст и переводит на русский язык. Возвращает str. """

    PAT = PAT_CLARIFAI
    USER_ID = 'facebook'
    APP_ID = 'translation'
    MODEL_ID = 'translation-english-to-russian-text'
    MODEL_VERSION_ID = 'e56b09a88a3545b08e69e626e76c46d1'
    TEXT_FILE_URL = 'https://samples.clarifai.com/negative_sentence_12.txt'

    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)
    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            # The userDataObject is created in the overview and is required when using a PAT
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
            inputs=[
                resources_pb2.Input(data=resources_pb2.Data(text=resources_pb2.Text(raw=text)))]),
        metadata=metadata)
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

    # Since we have one input, one output will exist here
    output = post_model_outputs_response.outputs[0]
    russian_text = output.data.text.raw
    return russian_text


def image_to_text_translate_rus(path_file: str) -> str:
    """ Объединяющая функция. Анализирует изображение, создает подпись и сразу переводит на русский язык.
        Возвращает строку.
        """
    text = image_to_text(path_file)
    discription = translate_ensglish_to_russian(text)
    return discription


if __name__ == '__main__':

    def check_function(file_name: str):
        """ проверка вывода функций image_to_tags и перевода с помощью translate_ensglish_to_russian.
         ввести имя файла в формате 'file_name.jpg', который расположен в общей папке проэкта /dowloads.
         """

        parrent = os.path.dirname(os.getcwd())
        file = os.path.join(parrent, file_name)
        concepts_photo = image_to_tags(file)
        print(concepts_photo)

        tags=''
        for n, tag in enumerate(concepts_photo):
            tags += tag[0] + ',' if n < (len(concepts_photo) - 1) else tag[0]
        print(tags)

        rus = translate_ensglish_to_russian(tags)
        tags_rus = rus.split(',')

        for n, t_r in enumerate(tags_rus):
            concepts_photo[n][0] = t_r

        print(concepts_photo)



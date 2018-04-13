"""
iflytek TTS　Developer by lidicn
"""
import voluptuous as vol
from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG,ATTR_OPTIONS
import homeassistant.helpers.config_validation as cv
import os
import requests
import logging
import json
import urllib
import urllib.parse


_Log=logging.getLogger(__name__)

# 默认语言
DEFAULT_LANG = 'zh'

# 支持的语言
SUPPORT_LANGUAGES = [
    'zh',
]
CONF_PERSON = 'person'
TOKEN_INTERFACE  = 'http://www.peiyinge.com/make/getSynthSign'
TEXT2AUDIO_INTERFACE = 'http://proxy.peiyinge.com:17063/synth?ts='

PERSON_TYPE = {
    '坤叔':'64010',#舌尖上的中国
    '小英':'65040',
    '飞飞':'65310',#飞碟说
    '小薛':'65320',
    '小俊':'65070',
    '程程':'65080',
    '小华':'62010',
    '小宇':'15675',#央视新闻康主播
    '小南':'65340',
    '彬哥':'65090',
    '小芳':'62020',#儿童读物
    '瑶瑶':'65360',
    '小光':'65110',
    '百合仙子':'62060',#有声播报、专题
    '韦香主':'62070',
    '小媛':'60100',
    '楠楠':'60130',#童声
    '大灰狼':'65250',
    '小洋':'65010',
    '老马':'60150',
    '原野':'65270',

    '萌小新':'60170',#蜡笔小新
    '颖儿':'67100',#赵丽颖
    '葛二爷':'67230',#葛优
    '小桃丸':'60120',#樱桃小丸子

    'John':'69010',#英语
    '凯瑟琳':'69020',#英语
    'Steve':'69030',#乔布斯、英语
    '奥巴马':'69055',#英语、普通话

    '小梅':'10003',#粤语
    '玉儿':'68120',#台湾
    '小强':'68010',#湖南
    '小坤':'68030',#河南
    '晓倩':'68040',#东北
    '小蓉':'68060',#四川
    '小莹':'68080',#陕西
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_PERSON, default='小英'): cv.string,
})

def get_engine(hass, config):
    lang = config.get(CONF_LANG)
    try:
        person = config.get(CONF_PERSON)
    except:
        person = '小英'
    tts_path = hass.config.path('tts')
    return iflytekTTS(lang, person, tts_path )

class iflytekTTS (Provider):

    def __init__(self, lang, person, tts_path):
        self._lang = lang
        self._person = person
        self._tts_path = tts_path
        self._speed = 0
        self._volume= 0



    @property
    def default_language(self):
        """Default language."""
        return self._lang

    @property
    def supported_languages(self):
        """List of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_options(self):
        """Return list of supported options like voice, emotionen."""
        return ['person','filename','speed','volume']

    def message_to_tts(self,message,person_id,speed,volume):
        data = {
            'content': message.encode('utf8')
        }
        result_info = requests.post(TOKEN_INTERFACE, data=data).json()
        content = urllib.parse.quote(message.encode('utf8'))
        ts = result_info['ts']
        sign = result_info['sign']
        voice_url = TEXT2AUDIO_INTERFACE + ts + '&sign=' + sign + \
            '&vid=' + str(person_id) + '&volume=' + str(volume) + '&speed=' + str(speed) + \
            '&content=' + content
        r = requests.get(voice_url)
        data=r.content
        return data

    def get_tts_audio(self, message, language, options=None):
        if options == None:
            get_person = PERSON_TYPE[self._person]
            get_speed = self._speed
            get_volume = self._volume
            get_filename = "nofilename"
        else:
            if "person" in options:
                get_person = PERSON_TYPE[options.get("person",'小俊')]
            else:
                get_person = PERSON_TYPE[self._person]
            if "speed" in options:
                get_speed = options.get("speed",0)
            else:
                get_speed = self._speed
            if "volume" in options:
                get_volume = options.get("volume",0)
            else:
                get_volume = self._volume
            if "filename" in options:
                get_filename = options.get("filename","demo.mp3")
            else:
                get_filename = "nofilename"
        if '#' in message:
            message_list = message.split('*#')
            data_list = []
            for message_ls in message_list:
                if message_ls != '':
                    message_character = message_ls.split('#')
                    character = message_character[1]
                    if character in PERSON_TYPE:
                        get_person = PERSON_TYPE[character]
                    else:
                        get_person = PERSON_TYPE[self._person]
                    data_list.append(self.message_to_tts(message = message_character[0],
                                    person_id= get_person,speed=get_speed,volume=get_volume))
            data = b"".join(data_list)
        else:
            data = self.message_to_tts(message=message,person_id=get_person,speed=get_speed,volume=get_volume)


        if get_filename == "nofilename":
            return ('mp3',data)
        else:
            filename = get_filename

        path_name =  os.path.join(self._tts_path , filename)
        if os.path.isfile(path_name ):
            os.remove(path_name)
        try:
            with open(path_name, 'wb') as voice:
                voice.write(data)
        except OSError:
            _Log.error("os error iflytek tts write file False")
            return (None, None)
        return ('mp3',data)

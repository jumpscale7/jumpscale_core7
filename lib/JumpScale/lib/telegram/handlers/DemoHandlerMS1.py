from datetime import datetime

import json
from JumpScale import j

class DemoHandlerMS1:

    def __init__(self):
        pass

    def on_text(self, tg, message):

        from IPython import embed
        print "DEBUG NOW kkk"
        embed()
        
            
        # markup={}
        # markup["force_reply"]=True

        # tg.send_message(message.chat.id, "this is me",reply_to_message_id=None,reply_markup=json.dumps(markup))               

        markup={}
        markup["keyboard"]=[["yes"],["no"],["1","2","3"],["stop"]]
        markup["resize_keyboard"]=True
        markup["one_time_keyboard"]=True

        if not message.text=="stop":

            tg.send_message(message.chat.id, "Please fill in",reply_to_message_id=None,reply_markup=json.dumps(markup))                    


        
#!/usr/bin/python
# -*- coding:utf-8 -*- 

import time
import re
import itchat
import os
from itchat.content import TEXT, PICTURE, FRIENDS, NOTE, CARD, SHARING

# 全局存储发送的信息
# todo 待优化,信息发送两分钟后无法撤回,所以要定期清除2分钟的信息,防止内存溢出
msg_information = {}

# 监听信息
@itchat.msg_register([
	TEXT,
	PICTURE,
	FRIENDS,
	CARD,
	SHARING
], isFriendChat=True, isGroupChat=True, isMpChat=True)
def handle_receive_msg(msg):
	# 如果是发送给文件传输助手的就取消的
	if msg['User']['UserName'] == 'filehelper':
		return None
	
	# 记录收到消息的时间
	msg_receive_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	# 记录信息来源
	msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
	# 信息发送时间
	msg_time = msg['CreateTime']
	# 信息的唯一id
	msg_id = msg['MsgId']
	# 信息内容
	msg_content = None
	# 信息url 比如分享的文章和音乐
	msg_share_url = None
	
	if msg['Type'] == 'Text' or msg['Type'] == 'Friends':
		msg_content = msg['Text']
	#如果发送的消息是附件、视屏、图片、语音
	elif msg['Type'] == 'Picture':
		msg_content = msg['FileName']
		# 下载文件
		msg['Text'](str(msg_content))
	# 如果是推荐名片
	elif msg['Type'] == 'Card':
		msg_content = msg['RecommendInfo']['NickName'] + '的名片'
		if msg['RecommendInfo']['Sex'] == 1:
			msg_content += '性别为男'
		else:
			msg_content += '性别为女'
	elif msg['Type'] == 'Sharing':
		msg_content = msg['Text']
		msg_share_url = msg['Url']
	else:
		# 其他信息就不要了
		return None
		
	print(msg_content)
		
	# 存储信息
	msg_information.update(
		{
			msg_id: {
				"msg_from": msg_from,
				"msg_time": msg_time,
				"msg_receive_time": msg_receive_time,
				"msg_content": msg_content,
				"msg_share_url": msg_share_url,
				"msg_type": msg['Type'],
				
			}
		}
	)

# 监听信息是否撤回
@itchat.msg_register(NOTE, isFriendChat=True, isGroupChat=True, isMpChat=True)
def information(msg):
	if '撤回了一条消息' in msg['Content']:
		# 在返回的content查找撤回的消息的id
		old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
		# 得到消息
		old_msg = msg_information.get(old_msg_id)
		if not old_msg:
			return None
		
		if len(old_msg_id) < 11:
			#表情包
			print('表情包')
		else:
			msg_body = '告诉你一个秘密~' + '\n' \
			+ old_msg.get('msg_from') + ' 撤回了 ' + old_msg.get('msg_type') + ' 消息 ' \
			+ '\n' + old_msg.get('msg_receive_time') + '\n' \
			+ '撤回消息: ' + '\n' \
			+ r'' + old_msg.get('msg_content')
			
		if old_msg['msg_type'] == 'Sharing':
			msg_body += '\n就是这个链接 ' + old_msg.get('msg_share_url')
			
		# 将撤回消息发送到文件助手
		itchat.send_msg(msg_body, toUserName='filehelper')
		
		# 如果是图片
		if old_msg['msg_type'] == 'Picture':
			file = '@fil@%s' % (old_msg['msg_content'])
			itchat.send(msg=file, toUserName='filehelper')
			os.remove(old_msg['msg_content'])
		
		# 删除字典旧消息
		msg_information.pop(old_msg_id)


itchat.auto_login(hotReload=True)

itchat.send('你已经登录，将开启监撤回消息的功能', toUserName='filehelper')

itchat.run()
#-------------------------------------------------------------
# 
#------------------------------------------------------------

__author__ = 'Gary D. Smith <https://github.com/sparkwarden>'
__version__ = '1.0'
__date__ = '2024/03/17'

"""
Description: wp_xml_extract extracts data from Wordpress.com
export files, generates a report and excel file containing
information for each post.

Tested with Python 3.10
Operating System: iPadOS 17.4
iOS Python apps: Pythonista, a-Shell

Required modules:
 xmltodict - convert xml file to nested dict.
 openpyxl - generate excel report file.
"""

#-------------------------------------------------------------
# 
#------------------------------------------------------------

import xmltodict
import pathlib
import datetime
import io
import sys
import openpyxl
#from collections import OrderedDict
from operator import attrgetter
import copy
import re

LF = '\n'

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def get_output_path_with_dt(extention='.log',\
	timefmt='%Y%m%d_%H%m%S%f'):
	return str(pathlib.Path(__file__).stem + '_' + \
			datetime.datetime.now().strftime(timefmt) + extention)
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

C_CHR_None = '<None>'
C_NUM_None = -1

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

# lightweight logging class 

class clsLogger:
	"""
	lightweight alternative for logging module 
	"""
	
	logger_list = []
	
	PRN_SCREEN_AND_FILE = 1
	PRN_SCREEN_ONLY = 2
	PRN_FILE_ONLY = 3
	PRN_FLUSH_LOG_THRESHOLD = 100
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self, name, prn_flag=1):
		
		self.is_active = False
		self.name = name
		self.prn_flag = prn_flag
		self.log_cnt = 0
			
		self.logfilepath = get_output_path_with_dt('.log')
			
		self.logbuf = io.StringIO()
			
		if self not in clsLogger.logger_list:
			clsLogger.logger_list.append(self)
			msg = f'\nLogger {self.name} starting. . .'
			with open(self.logfilepath,'w',encoding='utf-8') as f:
				f.write('')
				self.writelog(msg)
		else:
			raise Exception ('Logger already established')
			
		self.is_active = True
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_logger_by_name(cls, name):
		
		node_list = [nd for nd in cls.logger_list if nd.name == name]
		retnode = None
		if len(node_list) > 0:
			retnode = node_list[0]
		return retnode
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def writelogarg(self, arg):
		"""
		Write arg string to log buffer.  If log threshold reached,
		flush buffer to log file.
		"""
		if self.log_cnt >= clsLogger.PRN_FLUSH_LOG_THRESHOLD:
			self.flushlog()
		
		arg_str = str(arg)
		if self.prn_flag == clsLogger.PRN_SCREEN_AND_FILE:
			self.logbuf.write(arg_str)
			sys.stdout.write(arg_str)
		elif self.prn_flag == clsLogger.PRN_SCREEN_ONLY:
			sys.stdout.write(arg_str)
		else:
			self.logbuf.write(arg_str)
		self.log_cnt+=1
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def writelog(self, *args):
		for arg in args:
			arg_str = str(arg)
			self.writelogarg(arg_str)
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def flushlog(self):
		with open(self.logfilepath,'a',encoding='utf-8') as f:
			f.write(self.logbuf.getvalue())
		self.log_cnt = 0
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def closelog(self):
		self.writelog(f'\nLogger {self.name} closing. . .')
		self.flushlog()
		self.logbuf.close()
		self.is_active = False
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	@classmethod
	def writelog_by_name(cls, *args, name='root'):
		logr = cls.get_logger_by_name(name)
		logr.writelog(*args)
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def setup(cls):
		cls.logger_list.clear()
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def shutdown(cls):
		for lg in cls.logger_list:
			if lg.is_active:
				lg.closelog()
	
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def list_to_xlsx(xls_list,xls_path):
	"""
	Write list to excel .xlsx file
	"""
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	for row in xls_list:
		ws.append(row)

	wb.save(xls_path)
		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def build_file_list(startdir:str=None, ptrnstr='*.*'):
	"""
	Return a list of files recursively, starting with
	[startdir] directory, matching [ptrnstr] search pattern.
	"""
	_file_list = []
	
	if startdir is None:
		_startdir = str(pathlib.Path().cwd())
	else:
		_startdir = startdir
	
	p = pathlib.Path(_startdir)
	
	glob_list = p.rglob(ptrnstr)
	
	for path in glob_list:
		_path = str(path)
		p = pathlib.Path(_path)
		
		if p.is_file(): 
			_file_list.append(_path)
	
	return _file_list

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def to_str(s, str_len_max=10):

	if s:
		retstr = str(s).strip()
	else:
		retstr = '<None>'
		
	if str_len_max > 0:
		if len(retstr) > str_len_max:
			retstr = retstr[0:str_len_max]
			
	return retstr

#------------------------------------------------------------
# 
#------------------------------------------------------------


def wp_clean_text_tags(intext):
	_tag_list = [
		'<!-- wp:paragraph -->',
		'<!-- /wp:paragraph -->',
		'<p>',
		'</p>',
		'<br>',
		"&nbsp;",
		"&lt;"
		]
	_text = str(intext)
	_text = re.sub(r'\[.*?\]', " ", _text)   # square brackets
	_text = re.sub(r'\<.*?\>', " ", _text)   # tag start end 
	for _tag in _tag_list:
		_text = str(_text).replace(_tag,' ')
	return _text

#------------------------------------------------------------
# 
#------------------------------------------------------------

class WP_Export:
	"""
	Wordpress export class.  Extracts data from each blog post,
	outputs to report log and excel file for subsequent analysis.
	"""
	
	node_list = []
	srt_node_list = []
	none_str =  '<none>'
	
	def __init__(self, postno:int, xml_path:str):
		
		_none = WP_Export.none_str
		self.postno = postno
		self.status = _none
		self.link = _none
		self.post_type = _none
		self.content = _none
		self.post_parent = 0
		self.post_name = _none
		self.creator = _none
		self.title = _none
		self.pub_date = _none
		self.pub_date_time = None
		self.post_id = 0
		self.sort_key = _none
		self.categories = []
		self.tags = []
		self.attachments = []
		self.parameters = {}
		self.xml_path = xml_path
		if self not in WP_Export.node_list:
			WP_Export.node_list.append(self)
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def set_data(self, item):
		_none = WP_Export.none_str
		self.item = item
		self.status = item.get('wp:status',_none)
		self.link = item.get('link',_none)
		self.post_type = item.get('wp:post_type',_none)
		_content = item.get('content:encoded',_none)
		self.content = wp_clean_text_tags(_content)
		
		self.post_name = item.get('wp:post_name',_none)
		self.creator = item.get('dc:creator',_none)
		self.title = item.get('title',_none)
		_pub_date = item.get('pubDate',_none)
		self.pub_date, _pub_date_time = WP_Export.to_pubdate(_pub_date)
		self.pub_date_time = _pub_date_time
		_post_id = item.get('wp:post_id','0')
		self.post_id = int(_post_id)
		
		_post_parent = item.get('wp:post_parent',0)
		self.post_parent = int(_post_parent)
		
		self.attachment_url = item.get('wp:attachment_url','<none>')
		_out_date, _ = WP_Export.to_pubdate(_pub_date,"%Y%m%d%H%M%S")
		self.sort_key = _out_date
		_cats_tags = item.get('category',[])
		
		for x in _cats_tags:
			_k = x['@domain']
			_v = x['@nicename']
			if _k == 'category':
				self.categories.append(_v)
			else:
				self.tags.append(_v)
				
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def as_dict(self):
		d = {}
		d['postno']=self.postno
		d['post_id'] = self.post_id
		d['status']=self.status
		d['link']=self.link
		d['post_type']=self.post_type
		d['content']=self.content
		d['post_parent']=self.post_parent
		d['post_name']=self.post_name
		
		d['creator'] = self.creator
		d['title'] = self.title
		d['pub_date'] = self.pub_date
		d['pub_datetime'] = self.pub_date_time
		
		d['attachment_url'] = self.attachment_url
		d['categories'] = self.categories
		d['tags'] = self.tags
		d['sort_key'] = self.sort_key
		return d
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@staticmethod
	def to_pubdate(indate, outfmt="%Y%m%d"):
		retdt = None
		retdtstr = ''
		try:
			retdt = datetime.datetime.strptime(indate,'%a, %d %b %Y %H:%M:%S +0000')
			retdtstr = retdt.strftime(outfmt)
			
		except ValueError as ex:
			clsLogger.WriteLogArgsByName(ex)
		return retdtstr, retdt
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def setup(cls):
		cls.node_list.clear()
		cls.srt_node_list.clear()
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def set_srt_node_list(cls):
		_deep_node_list = copy.deepcopy(cls.node_list)
		srt_node_list = \
			sorted(_deep_node_list, key=attrgetter('sort_key'),reverse=True)
		cls.srt_node_list = srt_node_list
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_post_by_postno(cls,postno):
		post_list = [nd for nd in cls.node_list if nd.postno == postno]
		retnode = None
		if post_list:
			if len(post_list) > 0:
				retnode = post_list[0]
		return retnode
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	@classmethod
	def get_post_by_postid(cls,post_id):
		post_list = [nd for nd in cls.node_list if nd.post_id == post_id]
		retnode = None
		if post_list:
			if len(post_list) == 1:
				retnode = post_list[0]
		return retnode
		
	
	#---------------------------------------------------------------------
	#
	#---------------------------------------------------------------------
					
	@classmethod
	def attach_images_to_parents(cls):
		_attach_list = [a for a in cls.srt_node_list if a.status == 'inherit']
		_publish_list = [p for p in cls.srt_node_list if p.status == 'publish']
		for p in _publish_list:
			_img_list = [a for a in _attach_list if a.post_parent == p.post_id]
			p.attachments = _img_list
		
	#---------------------------------------------------------------------
	#
	#---------------------------------------------------------------------
	
	def field_str(self, fld_key, LF=''):
		_nonestr = WP_Export.none_str
		d = self.as_dict()
		_value = d.get(fld_key,_nonestr)
		return f'{LF} {fld_key}: {_value} '
		
	#---------------------------------------------------------------------
	#
	#--------------------------------------------------------------------
	
	def as_str(self) -> str:
		
		retstr = f'{LF}<{self.__class__.__name__}> ' + \
		self.field_str('postno') + self.field_str('post_id') + \
		self.field_str('status',LF) + self.field_str('post_type') + \
		self.field_str('pub_date',LF) + self.field_str('sort_key') + \
		self.field_str('title',LF) + \
		self.field_str('post_name',LF) + \
		self.field_str('content',LF)
		
		_cats = f'{LF} categories: '
		_tags = f'{LF} tags: '
		
		for c in self.categories:
			_cats += str(c) + ', '
		
		for t in self.tags:
			_tags += str(t) + ', '
			
		retstr += _cats[:-2]
		retstr += _tags[:-2]
		
		retstr += f'{LF} {len(self.attachments)} image(s) attached.'
		
		return retstr
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def as_xlsx_row(self):
		_cats = ''
		_tags = ''
		for c in self.categories:
			_cats += str(c) + ', '
		
		for t in self.tags:
			_tags += str(t) + ', '
			
		_cats = _cats[:-2]
		_tags = _tags[:-2]
		
		_num_images = len(self.attachments)
		return [self.postno,self.post_id,self.status,self.post_type,\
		self.pub_date,self.sort_key,self.title,self.post_name,_cats,\
		_tags,_num_images]
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
		
	@staticmethod
	def as_xlsx_hdr():
		return ['post no','post id','status','post type','pubdate','sort key','title','name','categories','tags','#images']
		
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
		
	@staticmethod
	def current_dir() -> str:
		return str(pathlib.Path().cwd())
		
	#---------------------------------------------------------------------
	#
	#---------------------------------------------------------------------
		
	def __repr__(self) -> str:
		return self.as_str()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	
	@classmethod
	def report_and_xlsx(cls):
		
		cls.set_srt_node_list()
	
		cls.attach_images_to_parents()
		
		publish_list = [p for p in cls.srt_node_list if p.status == 'publish']
		
		topnode = publish_list[0]
		_path = str(topnode.xml_path)
		
		clsLogger.writelog_by_name(f'{LF} Report for WP xml path: {_path}')
		
		for p in publish_list:
			clsLogger.writelog_by_name(f'{LF} {p.as_str()}')
			
		#------------------------------------------------------------
		# 
		#------------------------------------------------------------
			
		xlsx_list = [cls.as_xlsx_hdr()]
		
		for p in publish_list:
			xlsx_list.append(p.as_xlsx_row())
		
		list_to_xlsx(xlsx_list,_path.rstrip('.xml')+'.xlsx')
			
		
#-------------------------------------------------------------
# 
#------------------------------------------------------------

def wp_clean(instr:str,replace_list):
	_instr = str(instr)
	for r in replace_list:
		_instr.replace(r,' ')
	return _instr
	
#-------------------------------------------------------------
# 
#------------------------------------------------------------

def wp_pprint(item):
	import pprint
	
	with open('pprint.log', 'a', encoding='utf-8') as out:
		pprint.pprint(item, stream=out)
	
#------------------------------------------------------------
# 
#------------------------------------------------------------

def process_xml_file(path):
	WP_Export.setup()
	
	item_list = []

	with open(path,"r",encoding="utf-8") as fd:
		doc = xmltodict.parse(fd.read())
		
		wp_pprint(doc)
		
		item_list = doc['rss']['channel']['item']
	
	for item_no, item in enumerate(item_list,start=1):
		
		_post_type = item.get('wp:post_type','')
		if _post_type in ['post', 'attachment']:
		
			WP_Export(item_no, path)
			nd = WP_Export.get_post_by_postno(item_no)
			nd.set_data(item)
			
	WP_Export.report_and_xlsx()

#-------------------------------------------------------------
# 
#-------------------------------------------------------------
		
def main():
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	curdir = WP_Export.current_dir()
	
	xml_file_list = build_file_list(curdir, '*.xml')
	
	for xml_path in xml_file_list:
		process_xml_file(xml_path)
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	
#-------------------------------------------------------------
# 
#------------------------------------------------------------

if __name__ == "__main__":
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	clsLogger.setup()
	
	logr = clsLogger('root')
	
	logr.writelog(f'{LF}program {__file__} started. {LF}')
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	main()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	logr.writelog(LF)
	logr.writelog(f'{LF}program {__file__} completed. {LF}')
	
	logr.closelog()
	
	clsLogger.shutdown()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------


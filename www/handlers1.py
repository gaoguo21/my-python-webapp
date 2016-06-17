#/usr/bin/env python3
#-*-coding: utf-8-*

import re,time,json,logging,hashlib,base64,asyncio
from coroweb import get,post
from models import User,Comment,Blog,next_id
from apis import APIValueError,APIError,APIResourceNotFoundError,APIPermissionError,Page
from config import configs
from aiohttp import web

def check_admin(request):
	if request.__user__ is None or not request.__user__.admin:
		raise APIPermissionError()
		
@get('/index')
def indexx(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
		'users':users
            }

'''@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Teste Blog', summary=summary, created_at=time.time()-1),
        Blog(id='2', name='Somethinge New', summary=summary, created_at=time.time()-30),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-17200),
		Blog(id='4', name='Teste Blogdfd', summary=summary, created_at=time.time()-1),
        Blog(id='5', name='Somethinge Newdfd', summary=summary, created_at=time.time()-30),
        Blog(id='6', name='Learn Swiftdfds', summary=summary, created_at=time.time()-17200),
		Blog(id='7', name='Teste Blogdfsd', summary=summary, created_at=time.time()-1),
        Blog(id='8', name='Somethinge Nedfdfw', summary=summary, created_at=time.time()-30),
        Blog(id='9', name='Learn Swiftdfsd', summary=summary, created_at=time.time()-17200),
		Blog(id='10', name='Teste dfdBlog', summary=summary, created_at=time.time()-1),
        Blog(id='11', name='Somdfdethinge New', summary=summary, created_at=time.time()-30),
        Blog(id='12', name='Learn Swidfft', summary=summary, created_at=time.time()-17200),
		Blog(id='1', name='Teste Blog', summary=summary, created_at=time.time()-1),
        Blog(id='2', name='Somethinge New', summary=summary, created_at=time.time()-30),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-17200),
		Blog(id='4', name='Teste Blogdfd', summary=summary, created_at=time.time()-1),
        Blog(id='5', name='Somethinge Newdfd', summary=summary, created_at=time.time()-30),
        Blog(id='6', name='Learn Swiftdfds', summary=summary, created_at=time.time()-17200),
		Blog(id='7', name='Teste Blogdfsd', summary=summary, created_at=time.time()-1),
        Blog(id='8', name='Somethinge Nedfdfw', summary=summary, created_at=time.time()-30),
        Blog(id='9', name='Learn Swiftdfsd', summary=summary, created_at=time.time()-17200),
		Blog(id='10', name='Teste dfdBlog', summary=summary, created_at=time.time()-1),
        Blog(id='11', name='Somdfdethinge New', summary=summary, created_at=time.time()-30),
        Blog(id='12', name='Learn Swidfft', summary=summary, created_at=time.time()-17200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }'''

	
@get('/')
def index(*,page='1'):
	page_index=get_page_index(page)
	num=yield from Blog.findNumber('count(id)')
	page=Page(num,page_index)
	if num==0:
		blogs=[]
	else:
		blogs=yield from Blog.findAll(orderBy='created_at desc',limit=(page.offset,page.limit))
	return{
		'__template__':'blogs.html',
			'page':page,
			'blogs':blogs}
			
			
@get('/register')
def register():
	return{
	'__template__':'register.html'
	}
	
@get('/signin')
def signin():
	return{
		'__template__':'signin.html'
		}
	
COOKIE_NAME='awesession'
_COOKIE_KEY=configs.session.secret
	
_RE_EMAIL=re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1=re.compile(r'^[0-9a-f]{40}$')

def get_page_index(page_str):
	p=1
	try:
		p=int(page_str)
	except ValueError as e:
		pass
	if p<1:
		p=1
	return p
	

	
@post('/api/users')
@asyncio.coroutine
def api_register_user(*,email,name,passwd):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not passwd or not _RE_SHA1.match(passwd):
		raise APIValueError('passwd')
	users=yield from User.findAll('email=?',[email])
	if len(users)>0:
		raise APIError('registered:failed','email','Email is already in user.')
	uid=next_id()
	sha1_passwd='%s:%s'%(uid,passwd)
	
	admin=False
	if email=='dd@me.com':
		admin=True
		
	user=User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
	image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest(), admin=admin)
	logging.info('found user')
	yield from user.save()
	logging.info('user saved')
	r=web.Response()
	r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
	user.passwd=('******')
	r.content_type='application/json'
	r.body=json.dumps(user,ensure_ascii=False).encode('utf-8')
	return r

@post('/api/authenticate')
def authenticate(*,email,passwd):
	if not email:
		raise APIValueError('email','Invalid email.')
	if not passwd:
		raise APIValueError('passwd','Invalid password.')
	users=yield from User.findAll('email=?',[email])
	if len(users)==0:
		raise APIValueError('email','Email not exist')
	user=users[0]
	#check passwd
	sha1=hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':')
	sha1.update(passwd.encode('utf-8'))
	if user.passwd!=sha1.hexdigest():
		raise APIValueError('passwd','Invalid password')
		
	r=web.Response()
	r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
	user.passwd='******'
	r.content_type='application/json'
	r.body=json.dumps(user,ensure_ascii=False).encode('utf-8')
	return r
	
@post('/api/blogs/{id}/comments')
def api_create_comment(id,request,*,content):
	user=request.__user__
	if user is None:
		raise APIPermissionError('Please signin first.')
	if not content or not content.strip():
		raise APIValueError('content')
	blog=yield from Blog.find(id)
	if blog is None:
		raise APIResourceNotFoundError('Blog')
	comment=Comment(blog_id=blog.id,user_id=user.id,user_name=user.name,user_image=user.image,content=content.strip())
	yield from comment.save()
	return comment
	
@get('/manage/blogs/edit')
@asyncio.coroutine
def manage_create_blog():
	return{
		'__template__':'manage_blog_edit.html',
		'id':'',
		'action':'/api/blogs'
		}
		
		
@get('/manage/users')
@asyncio.coroutine
def manage_users(*, page='1'):
    # 查看所有用户
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }		
		
@get('/api/blogs/{id}')
@asyncio.coroutine
def api_get_blog(*,id):
	blog=yield from Blog.find(id)
	return blog
	

@get('/blog/{id}')
def get_blog(id):
		blog=yield from Blog.find(id)
		comments=yield from Comment.findAll('blog_id=?',[id],orderBy='created_at desc')
		return{
		'__template__':'blog.html',
		'blog':blog,
		'comments':comments
		}
		
@post('/api/blogs')
def api_create_blog(request,*,name,summary,content):
	check_admin(request)
	if not name or not name.strip():
		raise APIValueError('name','name can not be empty')
	if not summary or not summary.strip():
		raise APIValueError('summary','summary cannot be empty')
	if not content or not content.strip():
		raise APIValueError('content','content cannot be empty')
	blog=Blog(user_id=request.__user__.id, user_name=request.__user__.name,user_image=request.__user__.image,name=name.strip(),summary=summary.strip(),content=content.strip())
	yield from blog.save()
	return blog
	
@get('/api/comments')
def api_comments(*,page='1'):
		page_index=get_page_index(page)
		num=yield from Comment.findNumber('count(id)')
		p=Page(num,page_index)
		if num==0:
			return dict(page=p,comments=())
		comments=yield from Comment.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
		return dict(page=p,comments=comments)
		
@get('/api/blogs')
def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)
	
		
@post('/api/comments/{id}/delete')
def api_delete_comments(id,request):
		check_admin(request)
		c=yield from Comment.find(id)
		if c is None:
			raise APIResourceNOtFoundError('Comment')
		yield from c.remove()
		return dict(id=id)
			
			
@get('/api/blogs')
def api_blogs(*,page='1'):
		page_index=get_page_index(page)
		blog_count=yield from Blog.findNumber('count(id)')
		p=Page(blog_count,page_index)
		if blog_count==0:
			return dict(page=p,blogs=())
		blogs=yield from Blog.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
		return dict(pages=p, blogs=blogs)

@get('/api/users')
def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = yield from User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)
		
@get('/signout')
def signout(request):
	referer=request.headers.get('Referer')
	r=web.HTTPFound(referer or '/')
	r.set_cookie(COOKIE_NAME,'-deleted-',max_age=0,httponly=True)
	logging.info('user signed out')
	return r
	
@get('/manage/blogs')
def manage_blogs(*,page='1'):
	return{
	'__template__':'manage_blogs.html',
	'page_index':get_page_index(page)
	}
	
@post('/api/blogs/{id}/delete')
def api_delete_blog(request,*,id):
	check_admin(request)
	blog=yield from Blog.find(id)
	yield from blog.remove()
	return dict(id=id)
		
def user2cookie(user,max_age):
	expires=str(int(time.time()+max_age))
	s='%s-%s-%s-%s'%(user.id,user.passwd,expires,_COOKIE_KEY)
	L=[user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)

@get('/manage/comments')
def	mange_comments(*,page='1'):
	return{
		'__template__':'manage_comments.html',
		'page_index':get_page_index(page)
		}
		
@asyncio.coroutine
def cookie2user(cookie_str):
	if not cookie_str:
		return None
	try:
		L=cookie_str.split('-')
		if len(L)!=3:
			return None
		uid,expires,sha1=L
		if int(expires)<time.time():
			return None
		user=yield from User.find(uid)
		if user is None:
			return None
		s='%s-%s-%s-%s'%(uid,user.passwd,expires,_COOKIE_KEY)
		if sha1!=hashlib.sha1(s.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.passwd='******'
		return user
	except Exception as e:
		logging.exception(e)
		return None
	

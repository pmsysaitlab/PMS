from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden ,JsonResponse
import requests
import json
from django.views.decorators.csrf import csrf_exempt

import web.WSQL  as WSQL
import linechatbot.LSQL  as LSQL

sessionkeys=[]
session_userid={}

NGROK_INFO=settings.NGROK_INFO
LINE_CHANNEL_SECRET = settings.LINE_LOGIN_CHANNEL_SECRET
LINE_CLIENT_ID = settings.LINE_LOGIN_CHANNEL_ID
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def CheckSession(request):
    """
    Session 檢查(登入用)
    """
    if request.COOKIES.get('sessionid') not in sessionkeys:
        # print("###request.COOKIES.get('sessionid') ###",request.COOKIES.get('sessionid') )
        # print("###sessionkeys###",sessionkeys)
        print(bcolors.FAIL +"cannot get sessionid, log out"+ bcolors.ENDC)
        return -1
    if request.session['ip'] == None:
        print(bcolors.FAIL +"cannot get ip address, log out"+ bcolors.ENDC)
        return -1
    print(bcolors.OKGREEN +"user successfully access from "+ request.session['ip'] + bcolors.ENDC)
    return 1

def index(request):
    """   
    首頁
    """
    #####安全性前綴，請複製該區間貼到每一個def中#####
    code = CheckSession(request)
    if code == -1:
        user="教師端"          #please modi here
        failip=str(request.COOKIES.get('userip'))
        modipage="index.html"  #please modi here
        content="Login Failed" #please modi here
        identity="-1"
        WSQL.T_add_nouserid_log(failip,user,modipage,content,identity)
        return render(request,'login.html',{'LINE_CHANNEL_SECRET_web':LINE_CHANNEL_SECRET,'LINE_CLIENT_ID_web':LINE_CLIENT_ID,'NGROK_INFO_web':NGROK_INFO})
    name=WSQL.T_select_name(session_userid[request.COOKIES.get('sessionid')])
    ip=request.session['ip']
    userid = session_userid[request.COOKIES.get('sessionid')]
    modipage ="index.html" #please modi here
    content="login"        #please modi here
    identity=WSQL.T_select_identity(userid)
    WSQL.T_add_log(ip,userid,modipage,content,identity) 
    #####安全性前綴，請複製該區間貼到每一個def中#####
    return render(request,'index.html',{'name':name,'ONLINEJUDGE_HREF':ONLINEJUDGE_HREF})
@csrf_exempt
def login(request):
    """   
    登入頁
    """
    LINE_CHANNEL_SECRET_web = LINE_CHANNEL_SECRET
    LINE_CLIENT_ID_web = LINE_CLIENT_ID
    NGROK_INFO_web =NGROK_INFO
    user="教師端"  
    failip=str(request.COOKIES.get('userip'))
    modipage="index.html"  #please modi here
    content="Login Failed" #please modi here
    identity="-1"
    WSQL.T_add_nouserid_log(failip,user,modipage,content,identity)
    return render(request,'login.html',locals())
@csrf_exempt
def loginapi(request):
    """
    帳號密碼]登入校驗 API
    """    
    ac = request.POST.get('ac', '')
    pw = request.POST.get('pw', '')
    ip = request.POST.get('ip', '')
    loginstatus=WSQL.T_select_login(ac,pw)
    userid = loginstatus["userid"]
    identity = loginstatus["identity"]
    if userid <0:
        return  JsonResponse({'res':0})
    else:
        request.session.create()
        request.session['ip'] = ip
        sessionkeys.append(request.session.session_key)
        request.session.set_expiry(0)  
        response=HttpResponse()
        session_userid.setdefault(request.session.session_key,userid)
        bind_status = WSQL.T_select_bind(userid)
        # print(sessionkeys)
        # print(session_userid)
        return  JsonResponse({'res':1,'name':list(bind_status["select_name"])})
def linecode(request):
    """
    line登入頁面後的API
    可參考LINE官方文檔查找格式。
    """    
    code = request.GET.get('code',default='noxxx')
    state = request.GET.get('state',default='noxxx')
    ip = request.COOKIES.get('userip')
    headers={'Content-Type':'application/x-www-form-urlencoded'}
    data ={
        'grant_type':'authorization_code',
        'code': code,
        'redirect_uri':'{}Teacher/linecode'.format(settings.NGROK_INFO),
        'client_id': LINE_CLIENT_ID,
        'client_secret': LINE_CHANNEL_SECRET,          
    }
    response=requests.post('https://api.line.me/oauth2/v2.1/token',data=data,headers=headers)
    responseapi = json.loads(response.text)
    try:
        id_token=responseapi['id_token']
        access_token=responseapi['access_token'] 
        data ={
            'id_token':id_token,
            'client_id':LINE_CLIENT_ID,
        }
        idtokenapi=requests.post('https://api.line.me/oauth2/v2.1/verify',data=data)   
        idtoken_data = json.loads(idtokenapi.text)       
        headers={'Authorization':'Bearer {}'.format(access_token)}
        userinfo=requests.get('https://api.line.me/oauth2/v2.1/userinfo',headers=headers)
        userinfo_data = json.loads(userinfo.text)
        lineid = userinfo_data['sub']
        userid = WSQL.T_add_account(lineid)
        bind_status = WSQL.T_select_bind(userid)
        request.session.create()
        request.session['ip'] = ip
        sessionkeys.append(request.session.session_key)
        request.session.set_expiry(0)
        session_userid.setdefault(request.session.session_key,userid)
        print(sessionkeys)
        print(session_userid)
        if bind_status["ORM_Count"] == 0:
            return render(request,'signup.html',{'lineid':lineid })
        else:
            return render(request,'index.html',{'lineid':lineid,'name':bind_status["select_name"]})
    except KeyError:
        return render(request,'index.html',{'lineid':'error'})
def signupapi(request):
    """
    綁定與跳轉
    """
    #####安全性前綴，請複製該區間貼到每一個def中#####
    code = CheckSession(request)
    if code == -1:
        user="教師端"              #please modi here
        failip=str(request.COOKIES.get('userip'))
        modipage="signupapi"     #please modi here
        content="Login Failed"    #please modi here
        identity="-1"
        WSQL.T_add_nouserid_log(failip,user,modipage,content,identity)
        return render(request,'login.html',{'LINE_CHANNEL_SECRET_web':LINE_CHANNEL_SECRET,'LINE_CLIENT_ID_web':LINE_CLIENT_ID,'NGROK_INFO_web':NGROK_INFO})
    #####安全性前綴，請複製該區間貼到每一個def中#####
    lineid = request.POST.get('lineid', '')
    ac = request.POST.get('account', '')
    pw = request.POST.get('md5password', '')
    mail = request.POST.get('mail', '')
    name= request.POST.get('username','')
    userid = WSQL.T_select_userid(lineid)
    WSQL.T_modi_account(userid,ac,pw,0)
    WSQL.T_modi_LineProfile(userid,name,mail)
    # response.set_cookie('name',name) 
    ##### LOG 新增後綴#####
    ip=request.session['ip']
    userid = session_userid[request.COOKIES.get('sessionid')]
    modipage ="signupapi"          #please modi here
    content="新增教師資料並綁定，更新人:"+str(userid)      #please modi here
    identity=WSQL.T_select_identity(userid)
    WSQL.T_add_log(ip,userid,modipage,content,identity)
    ##### LOG 新增後綴#####
    return render(request,'index.html',{'name':name})
def modiprofile(request):
    """
    修改個人資料
    """
    #####安全性前綴，請複製該區間貼到每一個def中#####
    code = CheckSession(request)
    if code == -1:
        user="教師端"              #please modi here
        failip=str(request.COOKIES.get('userip'))
        modipage="signup.html"     #please modi here
        content="Login Failed"    #please modi here
        identity="-1"
        WSQL.T_add_nouserid_log(failip,user,modipage,content,identity)
        return render(request,'login.html',{'LINE_CHANNEL_SECRET_web':LINE_CHANNEL_SECRET,'LINE_CLIENT_ID_web':LINE_CLIENT_ID,'NGROK_INFO_web':NGROK_INFO})
    #####安全性前綴，請複製該區間貼到每一個def中#####
    userid = session_userid[request.COOKIES.get('sessionid')]
    lineid = WSQL.T_select_lineid(userid)
    name   = WSQL.T_select_profile(userid)["name"]
    ac     = WSQL.T_select_profile(userid)["ac"]
    mail   = WSQL.T_select_profile(userid)["mail"]
    ##### LOG 新增後綴#####
    ip=request.session['ip']
    userid = session_userid[request.COOKIES.get('sessionid')]
    modipage ="signup.html"          #please modi here
    content="更新教師資料，更新人:"+str(userid)      #please modi here
    identity=WSQL.T_select_identity(userid)
    WSQL.T_add_log(ip,userid,modipage,content,identity)
    ##### LOG 新增後綴#####
    return render(request,'signup.html',locals())
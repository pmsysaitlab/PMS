from django.db import models
from datetime import datetime

# Create your models here.
class LineBindList(models.Model):
    """
    Line端登入帳號密碼
    userid   = user流水號(PK)
    lineid   = line頒發id，唯一
    ac       = 帳號
    pw       = 密碼
    identity = 身分別(預設0，顯示輸出) 0=測試群(顯示資料測試)，1=非測試群(隱藏教師與助教)
    moditime = 更新時間
    """
    userid = models.AutoField(primary_key=True,null=False)
    lineid = models.CharField(max_length=35,unique=True,null=False)
    ac     = models.CharField(max_length=20,null=True)
    pw     = models.CharField(max_length=32,null=True)
    identity= models.IntegerField(null=True,default=0)
    moditime = models.DateTimeField(default=datetime.now())
    def __str__ (self):                
        return '%s,%s,%s,%s'%(self.userid,self.lineid,self.ac,self.pw) #自定義輸出，方便DEBUG用
    
class LineProfile(models.Model):
    """
    Line端登入以及綁定資料
    userid = user流水號(FK)
    name = 姓名
    mail = 信箱
    moditime = 更新時間
    """
    userid = models.ForeignKey('LineBindList',on_delete=models.CASCADE)
    name    = models.CharField(max_length=50)    
    mail    = models.EmailField()
    moditime = models.DateTimeField(auto_now_add=True)
    def __str__ (self):                
        return '%s,%s,%s'%(self.userid,self.name,self.mail) 
    
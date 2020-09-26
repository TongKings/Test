## 工具

1. linux系统（windows也可用）
2. crontab的使用
3. chromedriver的使用（需要下载和浏览器相同版本的，同期也行但不保证可以用）[网址](http://npm.taobao.org/mirrors/chromedriver/)
4. python(可去官网安装最新)[网址](https://www.python.org/downloads/)
5. selenium的使用(pip install selenium或者pip3 install selnium)，具体使用可查看文档

## 代码(以下代码举例)

```python
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
import time
import random
if __name__ == '__main__':
    #可以使用字典来写，我用的是列表
    #user_name_pwd = {'XXXXXXX':'YYYYY'}
    #学号
    user_name = ['XXXXXX','YYYYY']
    #密码
    password = ['XXXXXX','VVVVV']
    #姓名（不是必须）
    name = ['XXX']
    #循环计数
    i=0
    while(i<len(user_name)):
        #以下两句是保证不会打开浏览器
        option = webdriver.ChromeOptions()
        option.add_argument('headless')
        #google驱动位置
        browser = webdriver.Chrome(executable_path="/home/tong/下载/Util/google/chromedri浏览器ver",options=option)
        #需要填报的网址
        browser.get("http://xgb.ahstu.edu.cn/SPCP/Sys/Web/UserLogin.aspx")
        #帐号（如下图）
        browser.find_element_by_id("StudentId").send_keys(user_name[i])
        #密码（如下图）
        browser.find_element_by_id("Name").send_keys(password[i])
        
        #验证码                   
        browser.find_element_by_id("codeInput")
       .send_keys(browser.find_element_by_id('code-box').text)
        #登录
        login_button = browser.find_element_by_id("Submit")
        #点击登录
        ActionChains(browser).move_to_element(login_button).click(login_button).perform()
        #刷新页面（也可以直接输入跳转的网址）
        browser.get("http://xgb.ahstu.edu.cn/SPCP/Sys/Web/UserLogin.aspx")
        #定位
        zc = browser.find_element_by_css_selector("#platfrom1 img")
        #点击进入
        ActionChains(browser).move_to_element(zc).click(zc).perform()
        #刷新跳转的页面
        browser.get("http://xgb.ahstu.edu.cn/SPCP/Web/Temperature/StuTemperatureInfo")
               
        #Te_one = browser.find_element_by_id("Temper1")
        
        #Te_two = browser.find_element_by_id("Temper2")
        #检查是否重复填写
        try:
            #填写温度范围
            browser.find_element_by_id("Temper1").send_keys(random.randint(36,37))
            browser.find_element_by_id("Temper2").send_keys(random.randint(0,5))
            
            print(name[i],"的温度填写成功")
     
        except:
        
            print(name[i],"的温度在该时间段已经填写过，不能重复填写")
            
            i=i+1
            
            continue
            
            browser.quit()
        #提交填写
        browser.find_element_by_css_selector("[type=button][class=save_form]").click()
        
        #以下是健康信息填报

        #zc_two = browser.find_element_by_css_selector("#platfrom2 img")

        #ActionChains(browser).move_to_element(zc_two).click(zc_two).perform()
        
        #browser.get("http://xgb.ahstu.edu.cn/SPCP/Web/Report/Index")
        
        #browser.find_element_by_name("County").send_keys('龙子湖区')       
    
        #hidden_submenu = browser.find_element_by_css_selector("input[id=ckCLS]")
    
        #browser.execute_script("arguments[0].click();",hidden_submenu)

        #time.sleep(2)
        #menu_s = browser.find_element_by_css_selector("#SaveBtnDiv")
        
        #hidden_submenu_s = browser.find_element_by_css_selector("#SaveBtnDiv .save_form")
        
        #ActionChains(browser).move_to_element(menu_s).click(hidden_submenu_s).perform()
        
        i=i+1
    #延迟两秒
    time.sleep(2)
    #退出浏览器
    browser.quit()
```

![image-20200926193011670](/home/tong/.config/Typora/typora-user-images/image-20200926193011670.png)

    crond计时自动填报
    
  40 7,12,17 * * * python3 /home/tong/文档/tdz.py >> /home/tong/文档/tdz.py.log 2>&1

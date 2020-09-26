from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
import time
import random
if __name__ == '__main__':
    #user_name_pwd = {'2704170211':'19823x','2704170216':'103423','2704170307':'091819'}
    user_name = ['2704170211','2704170216','2704170307','2704170226','2704170223']
    password = ['19823x','103423','091819','031247','090056']
    name = ['童大洲','王天天','何俊','张柯','杨石超']
    i=0
    while(i<len(user_name)):
        
        option = webdriver.ChromeOptions()
    
        option.add_argument('headless')
    
        browser = webdriver.Chrome(executable_path="/home/tong/下载/Util/google/chromedriver",options=option)

        browser.get("http://xgb.ahstu.edu.cn/SPCP/Sys/Web/UserLogin.aspx")
        
        browser.find_element_by_id("StudentId").send_keys(user_name[i])
        
        browser.find_element_by_id("Name").send_keys(password[i])
        
        browser.find_element_by_id("codeInput").send_keys(browser.find_element_by_id('code-box').text)
        
        login_button = browser.find_element_by_id("Submit")
        
        ActionChains(browser).move_to_element(login_button).click(login_button).perform()
        
        browser.get("http://xgb.ahstu.edu.cn/SPCP/Sys/Web/UserLogin.aspx")
        
        zc = browser.find_element_by_css_selector("#platfrom1 img")
        
        ActionChains(browser).move_to_element(zc).click(zc).perform()
        
        browser.get("http://xgb.ahstu.edu.cn/SPCP/Web/Temperature/StuTemperatureInfo")
               
        #Te_one = browser.find_element_by_id("Temper1")
        
        #Te_two = browser.find_element_by_id("Temper2")
        try:
            browser.find_element_by_id("Temper1").send_keys(random.randint(36,37))
            
            browser.find_element_by_id("Temper2").send_keys(random.randint(0,9))
            
            print(name[i],"的温度填写成功")
     
        except:
        
            print(name[i],"的温度在该时间段已经填写过，不能重复填写")
            
            i=i+1
            
            continue
            
            browser.quit()
    
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
    
    time.sleep(2)
    
    browser.quit()

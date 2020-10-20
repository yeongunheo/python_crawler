from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime

import pandas as pd
import requests
import time
import random
import os
import openpyxl
import xlsxwriter
import xlrd

# 크롬창 열기
path = "C:\chromedriver"
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("no-sandbox")
options.add_argument("disable-gpu")
options.add_argument("lang=ko_KR")
options.add_argument( 'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

driver = webdriver.Chrome(executable_path=path, options=options)
driver.implicitly_wait(5)

driver.get('about:blank')
driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
driver.execute_script("const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")

df = pd.DataFrame(columns=['매장명', '분류', '전화번호', '도로명주소', '지번주소', '블로그_리뷰', '예약자_리뷰', '영업시간', 'N예약혜택', '메뉴'])

# 현재 파일의 절대경로
BASE_DIR = os.getcwd()

def error_page_check(param, menu, num):
    if os.path.isfile(BASE_DIR + "/error_page.txt"): #파일이 존재할 경우
        fileWriter = open(BASE_DIR + "/error_page.txt", 'a', encoding="UTF-8")
        fileWriter.write('\n' + param + ' 키워드의 ' + str(menu) + ' : ' + str(num) + '에 문제가 발생했습니다.')
        fileWriter.close()
    else: #파일이 존재하지 않을 경우
        fileWriter = open(BASE_DIR + "/error_page.txt", 'w', encoding="UTF-8")
        fileWriter.write('\n' + param + ' 키워드의 ' + str(menu) + ' : ' + str(num) + '에 문제가 발생했습니다.')
        fileWriter.close()

def main():
    xlsx = pd.read_excel('./input.xlsx')
    for keword in range(xlsx.shape[0]):
        param = xlsx.values[keword][0]
        startmenu = '1'

        # 엑셀파일형식
        # 크롤링데이터_키워드_이름_200819
        fname = '크롤링데이터_' + param + '_' + '홍길동_' + datetime.today().strftime("%y%m%d")

        # url 검색
        url = 'https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=' + param
        driver.get(url)
        driver.implicitly_wait(3)
        time.sleep(random.uniform(8, 10))

        # url 검색
        url = 'https://store.naver.com/restaurants/list?filterId=r11260539&page=1&query=' + param
        driver.get(url)
        driver.implicitly_wait(3)
        time.sleep(random.uniform(3, 5))

        # 다음페이지 버튼 클릭
        driver.find_element_by_css_selector('#container > div.filter_area > div:nth-child(1) > div > a').click()

        pageString = driver.page_source  # 셀레니움 페이지 내에서 html 추출
        soup = BeautifulSoup(pageString, 'html.parser')

        lastmenu = len(soup.find_all("ul", class_="list_filter")[0])

        #request 헤더
        headers = {'User-Agent': 'Chrome/81.0.4044.92'}

        try:
            for menu in range(int(startmenu), lastmenu):
                page_last_check = False  # 마지막페이지 체크

                for num in range(1, 16, 5):
                    if page_last_check:
                        break

                    # url 검색
                    time.sleep(random.uniform(3, 5))  # 3~5초동안 정지
                    url = 'https://store.naver.com/restaurants/list?filterId=r11260539&menu=' + str(menu) + '&page=' + str(num) + '&query=' + param
                    driver.get(url)
                    driver.implicitly_wait(3)
                    time.sleep(random.uniform(1, 3))  # 1~3초동안 정지

                    pageString = driver.page_source  # 셀레니움 페이지 내에서 html 추출
                    soup = BeautifulSoup(pageString, 'html.parser')
                    page_dummy = soup.find_all('div', class_="pagination_inner")
                    # ----------------------------------------------------------------------------------------------------------------
                    # 접속시 일시적 오류로 인해 페이지가 로딩되지 않을 경우
                    # ----------------------------------------------------------------------------------------------------------------
                    title_text = soup.title.text[:3]
                    if title_text == '네이버':
                        time.sleep(random.uniform(60, 180)) # 1~3분동안 정지
                        # url 재검색
                        url = 'https://store.naver.com/restaurants/list?filterId=r11260539&menu=' + str(menu) + '&page=' + str(num) + '&query=' + param
                        driver.get(url)
                        driver.implicitly_wait(3)
                        time.sleep(random.uniform(3, 5))  # 3~5초동안 정지

                        pageString = driver.page_source  # 셀레니움 페이지 내에서 html 추출
                        soup = BeautifulSoup(pageString, 'html.parser')
                        page_dummy = soup.find_all('div', class_="pagination_inner")

                        # 여전히 페이지 오류일 경우
                        if title_text == '네이버':
                            error_page_check(param, menu, num)

                    # ----------------------------------------------------------------------------------------------------------------
                    # 해당 메뉴에 1page밖에 없을 경우
                    # ----------------------------------------------------------------------------------------------------------------
                    if not page_dummy:
                        try:
                            restaurant_list = soup.find_all('li', class_="list_item type_restaurant")
                            if not restaurant_list:
                                break

                            # 단일페이지 df에 담기
                            onePageToDf(restaurant_list, menu, num, fname)

                        except:
                            break
                        break

                    if not page_dummy:
                        break

                    # ----------------------------------------------------------------------------------------------------------------
                    # 페이지 리스트 파싱
                    # ----------------------------------------------------------------------------------------------------------------
                    page_list = page_dummy[0].get_text()

                    # 더이상 불러올 페이지가 없는 경우 종료
                    if not page_list:
                        break

                    restaurant_list = soup.find_all('li', class_="list_item type_restaurant")
                    if not restaurant_list:
                        break

                    current_page = pageToCurrentPage(page_list)

                    # ----------------------------------------------------------------------------------------------------------------
                    # 출력
                    # ----------------------------------------------------------------------------------------------------------------

                    for page in current_page:
                        url = 'https://store.naver.com/restaurants/list?filterId=r11260539&menu=' + str(menu) + '&page=' + str(page) + '&query=' + param
                        driver.get(url)
                        time.sleep(random.uniform(3, 5))  # 3~5초동안 정지

                        pageString = driver.page_source  # 셀레니움 페이지 내에서 html 추출
                        soup = BeautifulSoup(pageString, 'html.parser')

                        # ----------------------------------------------------------------------------------------------------------------
                        # 접속시 일시적 오류로 인해 페이지가 로딩되지 않을 경우
                        # ----------------------------------------------------------------------------------------------------------------
                        title_text = soup.title.text[:3]
                        if title_text == '네이버':
                            time.sleep(random.uniform(60, 180))  # 1~3분동안 정지
                            # url 재검색
                            url = 'https://store.naver.com/restaurants/list?filterId=r11260539&menu=' + str(
                                menu) + '&page=' + str(num) + '&query=' + param
                            driver.get(url)
                            driver.implicitly_wait(3)
                            time.sleep(random.uniform(3, 5))  # 3~5초동안 정지

                            pageString = driver.page_source  # 셀레니움 페이지 내에서 html 추출
                            soup = BeautifulSoup(pageString, 'html.parser')
                            page_dummy = soup.find_all('div', class_="pagination_inner")

                            # 여전히 페이지 오류일 경우
                            if title_text == '네이버':
                                error_page_check(param, menu, page)

                        restaurant_list = soup.find_all('li', class_="list_item type_restaurant")  # 해당 페이지 내 음식점 리스트

                        # 단일페이지 df에 담기
                        onePageToDf(restaurant_list, menu, page, fname)

                    if page_last_check:
                        break
        finally:
            driver.close()

# 페이지 리스트 파싱
def pageToCurrentPage(page_list):
    global page_last_check
    page_length = len(page_list)

    current_page = [] #빈 리스트 생성
    if page_length == 1:  # 1 또는 6
        current_page.append(int(page_list[0]))
        page_last_check = True
    elif page_length == 2 and page_list[:2] == str(11):  # 11
        current_page.append(11)
        page_last_check = True
    elif page_length == 2 and page_list[:2] == str(16):  # 16
        current_page.append(16)
        page_last_check = True
    elif page_length == 2 and page_list[:2] == str(21):  # 21
        current_page.append(21)
        page_last_check = True
    elif page_length == 2 and page_list[:2] == str(26):  # 26
        current_page.append(26)
        page_last_check = True
    elif page_length == 2 and page_list[:2] == str(31):  # 31
        current_page.append(31)
        page_last_check = True
    elif page_length > 1 and page_list[0] == str(1) and page_list[1] == str(2):  # 12345
        if page_length != 5:
            page_last_check = True
        for k in range(1, page_length + 1):
            current_page.append(k)
    elif page_length > 1 and page_list[0] == str(6) and page_list[1] == str(7) and page_length < 6:  # 6789
        page_last_check = True
        for k in range(6, page_length + 1):
            current_page.append(k)
    elif page_length > 1 and page_list[0] == str(6) and page_list[1] == str(7) and page_length == 6:  # 678910
        for k in range(6, 11):
            current_page.append(k)
    else:
        start = int(page_list[:2])
        last = int(page_list[-2:])
        for k in range(start, last + 1):
            current_page.append(k)
        if page_length != 10:
            page_last_check = True

    return current_page

# 단일페이지 df에 담기
def onePageToDf(restaurant_list, menu, page, fname):
    global df
    excel_file_path = f'{BASE_DIR}/{fname}' + '.xlsx'
    headers = {'User-Agent': 'Chrome/81.0.4044.92'}

    # ------------------------------------------------------------------------------------------------------------
    # 이미 엑셀 파일이 존재할 경우
    # ------------------------------------------------------------------------------------------------------------
    if os.path.isfile(excel_file_path):
        # 엑셀파일 읽기
        df = pd.read_excel(fname + '.xlsx')
    else:
        df = pd.DataFrame(columns=['매장명', '분류', '전화번호', '도로명주소', '지번주소', '블로그_리뷰', '예약자_리뷰', '영업시간', 'N예약혜택', '메뉴'])

    cnt = len(df)
    for i in range(0, 20):
        # 한 페이지 내에 20개의 음식점 리스트가 존재하지 않을 경우 break
        try:
            restaurant_url = restaurant_list[i].a['href']
        except IndexError:
            break

        response = requests.get(restaurant_url, headers=headers)
        time.sleep(random.uniform(3, 5))  # 3~5초동안 정지
        # ---------------------------------------------------------------
        # 에러페이지 검출시 재시도
        # ---------------------------------------------------------------
        try:
            response.raise_for_status()
        except:
            error_page_check(fname, menu, page)
            time.sleep(random.uniform(60, 120))  # 1~2분동안 정지
            response = requests.get(restaurant_url, headers=headers)  # 재시도

        time.sleep(random.uniform(1, 3))  # 1~3초동안 정지
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')

        content = soup.find(id="content")
        name = " "
        try:
            name = content.find(class_="name").text  # 매장명
        except:
            name = " "

        category = " "
        try:
            category = content.find(class_="category").text  # 분류
        except:
            category = " "

        phone = " "
        try:
            phone = content.find("div", class_="txt").text  # 전화번호
            if phone[0] != '0':
                phone = " "
        except:
            phone = " "

        roadAddr = " "
        try:
            roadAddr = content.find(class_="addr").text  # 도로명주소
        except:
            roadAddr = " "

        commonAddr = " "
        try:
            commonAddr = content.find_all(class_="addr")[1].text  # 지번주소
        except:
            commonAddr = " "

        blogReviewCount = " "
        bookingReviewCount = " "
        try:
            review = content.find(class_="info_inner").text.split(' ')
            review_count = len(content.find(class_="info_inner").find_all("a", limit=2))
            if review_count == 1:
                blogReviewCount = content.find(class_="info_inner").find("a").text.split(' ')[2]  # 블로그리뷰
            elif review_count == 2:
                bookingReviewCount = \
                    content.find(class_="info_inner").find_all("a", limit=2)[0].text.split(' ')[
                        2]  # 예약자리뷰
                blogReviewCount = \
                    content.find(class_="info_inner").find_all("a", limit=2)[1].text.split(' ')[
                        2]  # 블로그리뷰
        except:
            blogReviewCount = " "
            bookingReviewCount = " "

        biztime = " "
        try:
            biztime = content.find(class_="biztime").text  # 영업시간
        except:
            biztime = " "

        nreserve_benefit = " "
        try:
            nreserve_benefit = content.find(class_="nreserve_benefit").text  # N예약혜택
        except:
            nreserve_benefit = " "

        menu_list = " "
        try:
            menu_list = content.find(class_="list_menu").text  # 메뉴
        except:
            menu_list = " "

        new_dict = {}
        new_dict["매장명"] = name
        new_dict["분류"] = category
        new_dict["전화번호"] = phone
        new_dict["도로명주소"] = roadAddr
        new_dict["지번주소"] = commonAddr
        new_dict["블로그_리뷰"] = blogReviewCount
        new_dict["예약자_리뷰"] = bookingReviewCount
        new_dict["영업시간"] = biztime
        new_dict["N예약혜택"] = nreserve_benefit
        new_dict["메뉴"] = menu_list

        df.loc[cnt] = new_dict

        cnt = cnt + 1

        #중복제거
        df = df.drop_duplicates()

        #엑셀 출력
        df.to_excel(fname + '.xlsx', index=False)

if __name__ == "__main__":
    main()
    print('프로그램이 종료되었습니다.')
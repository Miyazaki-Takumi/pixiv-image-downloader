import os
import time
import re
import shutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import streamlit as st

# おまじない
os.chdir(os.path.dirname(os.path.abspath(__file__)))




# selenium 部分------------------------------------------------------------------------------------------------------------------------------------


# ----------pixiv login-------------
def login(PIXIV_ID,PIXIV_PAS):
    driver.get(f'https://accounts.pixiv.net/login')
    time.sleep(2)

    # ID & PASの入力
    elements = driver.find_elements(By.CSS_SELECTOR, '.sc-bn9ph6-6.kwyvbO')
    elements[0].send_keys(PIXIV_ID)
    elements[1].send_keys(PIXIV_PAS)

    # loginボタンのクリック
    element = driver.find_element(By.CSS_SELECTOR, '.sc-bdnxRM.jvCTkj.sc-dlnjwi.klNrDe.sc-2o1uwj-6.NmyKg.sc-2o1uwj-6.NmyKg')
    driver.execute_script("arguments[0].click();", element)
    time.sleep(1)

    # reCAPTCHA認証を判定
    try_reCAPTCHA()

    time.sleep(3) # ログインを正しく行う為に必須
# ----------------------------------


# -----------reCAPTCHA認証判定-------
def try_reCAPTCHA():

    try:
        # iframe操作に移動
        reCAPTCHA_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
        driver.switch_to.frame(reCAPTCHA_iframe)
        
        # reCAPTCHAが認証されるまで待機
        reCAPTCHA_FLAG = driver.find_element(By.XPATH, '//*[@id="recaptcha-anchor"]').get_attribute("aria-checked")

        st.warning('Please perform "reCAPTCHA" authentication', icon="⚠️") # エラー表示
        # st.error('Please perform "reCAPTCHA" authentication', icon="🚨")

        while reCAPTCHA_FLAG == "false":
            time.sleep(1)
            # reCAPTCHA_FLAGの更新
            reCAPTCHA_FLAG = driver.find_element(By.XPATH, '//*[@id="recaptcha-anchor"]').get_attribute("aria-checked")

        st.success(' THANKS!! success "reCAPTCHA"!', icon="✅")
        # iframe操作から戻る
        driver.switch_to.default_content()
        # loginボタンのクリック
        element = driver.find_element(By.CSS_SELECTOR, '.sc-bdnxRM.jvCTkj.sc-dlnjwi.klNrDe.sc-2o1uwj-6.NmyKg.sc-2o1uwj-6.NmyKg')
        driver.execute_script("arguments[0].click();", element)
        print("done reCAPTCHA")

    except:
        print("no reCAPTCHA")
# ----------------------------------


# -----------画像の取得--------------
def get_imgs(SEARCH_URL,TIME_RANGE):

    page_flag = True
    TIME_RANGE_flag = True
    
    driver.get(f'{SEARCH_URL}')
    time.sleep(3)

    while page_flag: #pageがある限り繰り返す

        # ページ内にある全画像のelements
        elements = driver.find_elements(By.CSS_SELECTOR, '.sc-rp5asc-0.fxGVAF')

        for element in elements:
            # 画像URLを取得
            img_page_url = element.find_element(By.CSS_SELECTOR, '.sc-d98f2c-0.sc-rp5asc-16.iUsZyY.sc-cKRKFl.ejjglN').get_attribute('href')

            # 単画像の別ダブを開きoriginal_img_urlを取得
            driver.execute_script("window.open()")
            driver.switch_to.window(driver.window_handles[1]) # 操作ページを移動
            driver.get(f'{img_page_url}')
            time.sleep(1)

            if int(get_img_title()[:8]) < int(TIME_RANGE):
                TIME_RANGE_flag = False
                break

            # 画像を取得
            img_url = get_img_url()
            img_title = get_img_title()
            download_img(img_page_url,img_url,img_title)

            # ページを戻る
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        
        # TIME_RANGE未満なら続行
        if TIME_RANGE_flag:
            # page_flagの更新
            page_flag = page_transition()
        else:
            break

    driver.quit()
# ----------------------------------


# -----------タイトル抽出------------
def get_img_title():

    data_time = driver.find_element(By.CSS_SELECTOR, '.sc-5981ly-0.AaIsB').text
    t = data_time[-6:]
    a = re.split('[年月日]',data_time[:-7])
    a = ["0" + i if len(i) == 1 else i for i in a]
    a = ''.join(a)
    data_time = a+t

    try:
        img_title = f"{data_time}_{driver.find_element(By.CSS_SELECTOR, '.sc-1u8nu73-3.huVRfc').text}"
    except:
        img_title = f"{data_time}_無題"

    # 禁止文字を置換
    img_title = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', img_title)

    return img_title
# ----------------------------------

# -----------img_pageへ移動する------
def get_img_url():

    # 複数の画像がある場合(「すべて見る」がある場合)
    try:
        img_url = driver.find_element(By.CSS_SELECTOR, '.sc-1qpw8k9-3.eFhoug.gtm-expand-full-size-illust').get_attribute("href")
        imgs_url = [img_url]
    except:
        driver.find_element(By.CSS_SELECTOR, '.sc-emr523-0.guczbC').click()
        imgs_url = driver.find_elements(By.CSS_SELECTOR, '.sc-1qpw8k9-3.eFhoug.gtm-expand-full-size-illust')
        imgs_url = [img_url.get_attribute("href") for img_url in imgs_url]

    return imgs_url

# ----------------------------------

# -----------画像保存--------------
def download_img(img_page_url,imgs_url,file_name):
        
    """ ~注意点~
    「referer」にpixivのサイトを登録しないとアクセスできなかった。
    pixivが画像を保存している「i.pximg.net」は盗連保護の為、referer値が空値または Pixiv のドメイン以外の場合、403 が返されます。

    seleniumで同様のことを行うならば以下のような手段がある
    ----
    driver.execute_script("window.location.href='http://hoge.hoge'") 
    ----
    [参考URL:https://qiita.com/uneyamauneko/items/5e00b0f4027563a0d14f]

    """
    for i,img_url in enumerate(imgs_url):
        response = requests.get(img_url, headers={'referer': img_page_url})
        image = response.content
        time.sleep(1)

        with open(f"./img_folder/{file_name}-{i}.png", "wb") as f:
            f.write(image)
# ----------------------------------


# -----------ページ移動--------------
def page_transition():
    old_url = driver.current_url
    next_url = driver.find_elements(By.CSS_SELECTOR, '.sc-d98f2c-0.sc-xhhh7v-2.cCkJiq.sc-xhhh7v-1-filterProps-Styled-Component.kKBslM')[1].get_attribute("href")
    driver.get(f'{next_url}')

    # ページ移動確認
    if old_url == driver.current_url:
        # 最終ページに到達した
        print("this is last page.")
        return False
    else:
        print("move to next page.")
        return True
# ----------------------------------


# ------------------------------------------------------------------------------------------------------------------------------------------------










# WEBアプリ部分------------------------------------------------------------------------------------------------------------------------------------


# --------変数----------------
dct = {
    "SEARCH_URL":"",
    "TIME_RANGE":"",
    "PIXIV_ID":"",
    "PIXIV_PAS":"",
}
download_flag = False
# -----------------------------


# --------説明テキスト-----------
st.title("Pixiv Image Downloader")
st.header('How to Use?')
st.markdown(
    '''
    【Pixiv Image Downloader】はpixivの画像をseleniumとrequestsを用いて収集します。

    * SEARCH_URLに入力されたURLに存在する画像を収集します。(ページ移動も自動で行います)
    * 収集された画像の投稿日がTIME_RANGEを下回ると停止します。
    * 「Decision」ボタンを押すとWindowが立ち上がり収集が始まります。
    * 終了したら「Download ZIP」ボタンを押してイラストを保存してください。
    ------------------------------------------------------------------------------
    EX : SEARCH_URL
    > https://www.pixiv.net/users/------\n
    > https://www.pixiv.net/users/------/illustrations\n
    > https://www.pixiv.net/users/------/manga\n
    > https://www.pixiv.net/users/------/オリジナル\n   
    ------------------------------------------------------------------------------

    ※Pixivのログイン画面で"reCAPTCHA認証"を求められた場合は認証を行い、放置してください。\n
    ※現在のverはユーザーページにのみ対応しています。\n
    (https://www.pixiv.net/tags/~~~~/artworks などでも動きますが完全ではありません)
    '''
            )

st.subheader("DATA INPUT")

# -----------------------------


# --------入力フォーム----------
with st.form(key="BASE_VALUE"):

    # 入力部分
    dct["SEARCH_URL"] = st.text_input("Search URL", "https://www.pixiv.net/users/420928")
    dct["TIME_RANGE"] = str(st.date_input("What is the collection period? (lower limit)")).replace("-","")
    dct["PIXIV_ID"] = st.text_input("PIXIV's ID", "clione442@gmail.com")
    dct["PIXIV_PAS"] = st.text_input("PIXIV's PAS", "pixivtaku")

    # button設定
    decision_btn = st.form_submit_button("Decision")
    
    # 未入力判定+警告出力
    for key, value in dct.items():
        if value == "":
            st.warning(f'Enter {key}', icon="⚠️")

# -----------------------------



# --------収集部分(「decision_btn」が押されたら開始)----------
if decision_btn and not "" in dct.values():
    
    with st.spinner('Wait for it...'):
        #----------seleniumの準備-----------
        options = Options()
        # options.add_argument('--headless')
        driver = webdriver.Chrome("./chromedriver.exe" ,options=options)
        # ----------------------------------

        login(dct["PIXIV_ID"],dct["PIXIV_PAS"])
        get_imgs(dct["SEARCH_URL"],dct["TIME_RANGE"])
    
    st.success('Done!')
    
    # zipファイルの作成
    shutil.make_archive('zip_imgs', 'zip', root_dir='./img_folder')

    # downloadボタン
    with open("./zip_imgs.zip", "rb") as fp:
        btn = st.download_button(
                label="Download ZIP",
                data=fp,
                file_name="zip_imgs.zip",
                mime="application/zip"
            )
        download_flag = True
# -----------------------------



# --------ファイル消去部分(「zip_imgs.zip」がダウンロードされたら開始)----------
if download_flag:
    # os.remove("./zip_test.zip")
    dir = "./img_folder"
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
 # -----------------------------   

# ------------------------------------------------------------------------------------------------------------------------------------------------

# TODO
"""
reCAPTCHAの動作が確認できていない。確認しろ

main_app.pyの整形(コメントアウトを消して整えろ)

zipの出力名を変えたので一回出力して検証しろ(zip_test.zip → zip_imgs.zip)

gitにプッシュしろ(動画を見つつ)

公式サイトからプログラムを公開しろ
"""
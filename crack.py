import paddlex as pdx
import pyautogui
import random
import cv2 as cv
import numpy as np
import time

model = pdx.load_model('model')

# 计算两点距离
def dist(a, b):
    return pow(pow(b[0] - a[0], 2) + pow(b[1] - a[1], 2), 0.5)


# 鼠标连线
def drag(a, b, ratio=2):
    distance = dist(a, b)

    # 经验计算拖拽时间
    if distance > 250:
        sec = distance / 600
    else:
        sec = distance / 400

    pyautogui.moveTo(a[0] / ratio, a[1] / ratio)

    # 扰动
    pyautogui.move(random.randrange(-5, 5, 1), random.randrange(-5, 5, 1), 0.2)
    pyautogui.mouseDown()
    # 扰动
    pyautogui.move(random.randrange(-3, 3, 1), random.randrange(-3, 3, 1), 0.1, pyautogui.easeInOutQuad)

    # pyautogui.easeInQuad     # start slow, end fast
    # pyautogui.easeOutQuad    # start fast, end slow
    # pyautogui.easeInOutQuad  # start and end fast, slow in middle
    # pyautogui.easeInBounce   # bounce at the end
    # pyautogui.easeInElastic  # rubber band at the end linear
    # pyautogui.linear

    pyautogui.moveTo(b[0] / ratio + random.randrange(-5, 5, 1), b[1] / ratio + random.randrange(-5, 5, 1), sec, pyautogui.easeInOutQuad)
    # 扰动
    pyautogui.move(random.randrange(-5, 5, 1), random.randrange(-5, 5, 1), 0.1, pyautogui.easeInOutQuad)
    pyautogui.mouseUp()


# 破解过程
def crack():
    screenshot = pyautogui.screenshot()
    screenshot.save('images/tmp/screenshot.png')
    print('screen size: ', screenshot.size)

    imageCV = cv.imread('images/tmp/screenshot.png', 1)

    # 根据短语定位
    descLocates = []
    for descPath in ['images/desc/1.png', 'images/desc/2.png']:
        descTemplate = cv.imread(descPath, 1)
        descHeight, descWidth, _ = descTemplate.shape
        res = cv.matchTemplate(imageCV, descTemplate, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)
        descLocates = list(zip(*loc[::-1]))
        if len(descLocates) > 0:
            break

    if len(descLocates) < 1:
        raise Exception('Desc Not Found.')

    descLocate = descLocates[0]
    cv.rectangle(imageCV, descLocate, (descLocate[0] + descWidth, descLocate[1] + descHeight), (0, 0, 255), 3)

    # 识别颜色文字的图片
    predictImg = screenshot.crop(
        (descLocate[0] + descWidth, descLocate[1] - 1, descLocate[0] + descWidth + 100, descLocate[1] + 65));
    predictImg.save('images/tmp/predict.png')

    result = model.predict('images/tmp/predict.png')
    print("predict result: ", result)

    # 定位圆形位置
    btnTemplate = cv.imread('images/buttons/' + result[0]['category'] + '.png', 1)
    btnHeight, btnWeight, _ = btnTemplate.shape

    for threshold in [0.98, 0.96, 0.94, 0.92, 0.9]:
        res = cv.matchTemplate(imageCV, btnTemplate, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        results = list(zip(*loc[::-1]))

        if len(results) < 2:
            print('points retry, threshold:', threshold)
            continue

        # 计算距离最远的两个点作为起始点
        points = {'from': results[0], 'to': results[1]}
        for pt in results:
            if dist(points['from'], points['to']) < dist(points['from'], pt):
                points['to'] = pt

        #如果只找到一个点，则降低阈值重试
        if dist(points['from'], points['to']) < 50:
            print('points retry, threshold:', threshold)
        else:
            break

    if len(results) < 2:
        raise Exception('Button Not Found.')

    # 标记
    cv.rectangle(imageCV, points['from'], (points['from'][0] + btnWeight, points['from'][1] + btnHeight), (0, 0, 255),
                 3)
    cv.rectangle(imageCV, points['to'], (points['to'][0] + btnWeight, points['to'][1] + btnHeight), (0, 0, 255), 3)

    cv.imwrite('images/tmp/rectangle.png', imageCV)

    points = {
        'from': (points['from'][0] + btnWeight * random.randrange(1, 10, 1) / 10, points['from'][1] + btnHeight * random.randrange(1, 10, 1) / 10),
        'to': (points['to'][0] + btnWeight * random.randrange(1, 10, 1) / 10, points['to'][1] + btnHeight * random.randrange(1, 10, 1) / 10),
    }
    print('points:', points)

    ratio = screenshot.size[0] / pyautogui.size().width

    #聚焦
    pyautogui.moveTo(descLocate[0] / ratio, descLocate[1] / ratio)
    pyautogui.click()

    # 鼠标连线
    print('drag distance:', dist(points['from'], points['to']))
    drag(points['from'], points['to'], ratio)
    print('done')

while True:
    try:
        crack()
    except:
        _=''
    finally:
        time.sleep(10)
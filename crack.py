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

def get_line(x,y):
    a = (x[1] - y[1]) / (x[0] - y[0])
    b = (x[0] * y[1] - x[1] * y[0]) / (x[0] - y[0])
    return (a, b)

def _get_line_points(x, y, sr):
    dy = 1 if x[1]<y[1] else -1
    (a, b) = get_line(x, y)
    points = [x]
    if pow(x[0]-y[0], 2) > pow(x[1]-y[1], 2):
        # 以横向采样
        # 方向d
        d = 1 if x[0] < y[0] else -1
        cursor = x[0]
        while abs(cursor)<abs(y[0]):
            cursor = x[0]+sr*d
            points.append((cursor, cursor*a+b))
    else:
        # 以纵向采样
        # 方向d
        d = 1 if x[1]<y[1] else -1
        cursor = x[1]
        while abs(cursor)<abs(y[1]):
            cursor = x[1]+sr*d
            points.append(((cursor-b)/a, cursor))
    points.append(y)
    return points

def get_points(p1, p2, step):
    x1, y1 = p1
    x2, y2 = p2
    nol = True
    if abs(x2 - x1) < abs(y2 - y1):
        y1, x1 = p1
        y2, x2 = p2
        nol = False

    X = np.arange(x1, x2, (1 if x1 < x2 else -1) * step)

    #X = X + X/20
    Y = (X - x2) * (y1 - y2) / (x1 - x2) + y2

    #S = 1.1 * X
    Y = Y + np.random.normal(3, 0.7, Y.shape[0])

    #X = X + S

    if not nol:
        Y, X = X, Y

    # plt.scatter(X, Y)

    return list(zip(X, Y))


# 鼠标连线
def drag(x, y, ratio=2):
    distance = dist(x, y)

    # 经验计算拖拽时间
    # if distance / ratio > 100:
    #     sec = distance/ ratio / 200
    # else:
    #     sec = distance/ ratio / 100

    points = get_points(x, y, 15 if distance > 120 else 10)

    print('points:',points)
    pyautogui.moveTo(x[0] / ratio, x[1] / ratio, 0.5, pyautogui.easeOutQuad)

    #pyautogui.move(random.randrange(-5, 5, 1), random.randrange(-5, 5, 1), 0.2)

    pyautogui.mouseDown()

    for point in points:
        pyautogui.moveTo(point[0] / ratio, point[1] / ratio, 0.1, pyautogui.linear)

    #pyautogui.moveTo(y[0]/ratio, y[1]/ratio, 0.2, pyautogui.linear)
    time.sleep(0.4)
    pyautogui.mouseUp()

    # pyautogui.easeInQuad     # start slow, end fast
    # pyautogui.easeOutQuad    # start fast, end slow
    # pyautogui.easeInOutQuad  # start and end fast, slow in middle
    # pyautogui.easeInBounce   # bounce at the end
    # pyautogui.easeInElastic  # rubber band at the end linear
    # pyautogui.linear

    # pyautogui.moveTo(x[0] / ratio, x[1] / ratio, 0.5, pyautogui.easeOutQuad)
    #
    # # 扰动
    # pyautogui.move(random.randrange(-5, 5, 1), random.randrange(-5, 5, 1), 0.2)
    # pyautogui.mouseDown()
    # # 扰动
    # pyautogui.move(random.randrange(-5, 5, 1), random.randrange(-5, 5, 1), 0.2, pyautogui.linear)
    #
    # pyautogui.moveTo(y[0] / ratio, y[1] / ratio, sec, pyautogui.easeOutQuad)
    # # 扰动
    # pyautogui.move(random.randrange(-10, 10, 1), random.randrange(-10, 10, 1), 0.2, pyautogui.linear)
    # pyautogui.mouseUp()


# 破解过程
def crack():
    screenshot = pyautogui.screenshot()
    screenshot.save('images/tmp/screenshot.png')
    print('screen size: ', screenshot.size)

    ratio = screenshot.size[0] / pyautogui.size().width

    imageCV = cv.imread('images/tmp/screenshot.png', 1)

    # 根据短语定位
    descLocates = []
    for descPath in ['images/desc/1.png', 'images/desc/2.png', 'images/desc/3.png']:
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
        (descLocate[0] + descWidth, descLocate[1] - 1, descLocate[0] + descWidth + 58, descLocate[1] + 38))
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
        'from': (points['from'][0] + btnWeight * random.randrange(4, 8, 1) / 10, points['from'][1] + btnHeight * random.randrange(4, 8, 1) / 10),
        'to': (points['to'][0] + btnWeight * random.randrange(4, 8, 1) / 10, points['to'][1] + btnHeight * random.randrange(4, 8, 1) / 10),
    }
    print('points:', points)

    #聚焦
    pyautogui.moveTo(descLocate[0] / ratio, descLocate[1] / ratio)
    pyautogui.click()
    pyautogui.moveTo(points['from'][0] / ratio+random.randrange(-50, 50, 1), points['from'][1] / ratio+random.randrange(-50, 50, 1))
    pyautogui.click()
    time.sleep(3)

    # 鼠标连线
    print('drag distance:', dist(points['from'], points['to']))
    drag(points['from'], points['to'], ratio)
    print('done')

#crack()
while True:
    try:
        crack()
    except:
        _=''
    finally:
        time.sleep(10)
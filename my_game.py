import pygame
import random
import time
import copy

###################****************** AI 生成 *******************###################
# 初始化 Pygame
pygame.init()

# 定义常量
FPS = 120
BLOCK_SIZE = 80
ROWS, COLS = 6, 7

# 字体设置  
font = pygame.font.Font(None, 48)  
  
# 倒计时设置  
game_time = 60  # 倒计时总时间，单位：秒  

# 定义卡片列表
card_stack = []
selected_cards = []

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 屏幕尺寸
SCREEN_WIDTH, SCREEN_HEIGHT = COLS * (BLOCK_SIZE * 5 // 4) + BLOCK_SIZE // 4, ROWS * (BLOCK_SIZE *5 // 4) + BLOCK_SIZE // 4 + 3 * BLOCK_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('羊了个羊 - 消除游戏')

# 加载主页背景图片
back_pattern = pygame.image.load(f"image/back1_cut2.png")
back_pattern = pygame.transform.scale(back_pattern, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 加载图案图片
patterns = [pygame.image.load(f"image/{i}.png") for i in range(0, 9)]
patterns = [pygame.transform.scale(p, (BLOCK_SIZE, BLOCK_SIZE)) for p in patterns]

# 加载选项栏背景图片
block_pattern = pygame.image.load(f"image/block2_cut.png")
block_pattern = pygame.transform.scale(block_pattern, (SCREEN_WIDTH, 3 * BLOCK_SIZE))

# 加载游戏成功界面图片
successful_pattern = pygame.image.load(f"image/successful.png")
successful_pattern = pygame.transform.scale(successful_pattern, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 加载游戏失败界面图片
over_pattern = pygame.image.load(f"image/over.png")
over_pattern = pygame.transform.scale(over_pattern, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 加载游戏失败界面图片
time_out_pattern = pygame.image.load(f"image/time_out.png")
time_out_pattern = pygame.transform.scale(time_out_pattern, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 随机生成游戏板(初代，不会保证卡片可以完全消除)
def generate_cards():
    cards = []
    for _ in range(ROWS):
        card_row = []
        for _ in range(COLS):
            card_row.append(random.choice(patterns))
        cards.append(card_row)
    return cards

###################****************** AI 生成 *******************###################

# 随机生成游戏板(并保证卡片可以完全消除)
num_list = [[3, 3, 6, 3, 3, 6, 6, 6, 6],
            [3, 6, 3, 6, 3, 6, 3, 6, 6],
            [3, 3, 6, 3, 6, 6, 3, 6, 6],
            [3, 3, 3, 6, 6, 3, 6, 6, 6],
            [3, 6, 6, 6, 6, 3, 6, 3, 3],
            [3, 6, 6, 6, 6, 6, 3, 3, 3],
            [3, 6, 6, 3, 6, 6, 6, 3, 3],
            [6, 3, 6, 3, 3, 6, 6, 6, 3],
            [6, 6, 3, 0, 6, 6, 6, 6, 3],
            [6, 3, 6, 6, 6, 6, 3, 0, 6],
            [6, 6, 9, 3, 3, 6, 3, 0, 6],
            [3, 3, 9, 3, 6, 9, 3, 0, 6]]

def generate_random_patterns(patterns, num_list, state):  
    """  
        根据num_list生成包含随机图案的列表。
        num_list的每个子列表指定了所需图案的数量(包括0,表示不需要图案)。

        random_patterns[][] = [image, state]
        state:
             can_choose     is_visiable
        0       no               no      # 消除后的状态
        1       no               yes     # 第二层初始状态
        2       yes              yes     # 第一层初始状态
    """  
    random_patterns = []
    
    # 随机选取一组数据进行初始化
    random_num_list = num_list[random.randint(0, len(num_list) - 1)]
    while len(random_patterns) < ROWS:
        card_row = []
        while len(card_row) < COLS:
            pattern_index = random.randint(0, len(patterns) - 1)
            if random_num_list[pattern_index] > 0:
                card_row.append([patterns[pattern_index], state])
                random_num_list[pattern_index] -= 1
        random_patterns.append(card_row)

    return random_patterns

# 绘制卡片矩阵
def draw_cards(cards, offset = 0):
    for row in range(ROWS):
        for col in range(COLS):
            tile = cards[row][col][0]
            state = cards[row][col][1]
            if tile is not None and state != 0:
                screen.blit(tile, (col * (BLOCK_SIZE *5 // 4) + BLOCK_SIZE // 4 + offset, row * (BLOCK_SIZE * 5 // 4) + BLOCK_SIZE // 4 + offset))

def draw_selected_cards(selected_cards):
    for i in range(len(selected_cards)):
        image = selected_cards[i][2][0]
        if image is not None:
            screen.blit(image, (i * (BLOCK_SIZE + 21) + 120, SCREEN_HEIGHT - BLOCK_SIZE - 5))

def state_change(cards, row, col):
    # 如果为不可选可见的初始状态，则改为可选可见状态
    if cards[row][col][1] == 1:
        return 2
    # 如果为可选可见状态或已消除状态，则改为不可选不可见的删除状态
    else:
        return 0

# 消除三个相同的卡片
def check_match(cards, cards2, row, col, del_cards_num):
    '''
        思路:将selected_cards中的图与原始数据库里的所有图片比较,
        比较成功则计数器加一并且记录图片是几号选择框,如果计数器大于等于3,
        则匹配成功,消去匹配成功的三个selected_card,重组selected_cards。
    '''
    # 允许最大选择数量为5,如果超过最大限制则游戏失败退出游戏
    if len(selected_cards) > 5:
        selected_cards.clear()

        # 输出失败信息，显示失败界面
        print("Game over!!!")
        screen.blit(over_pattern, (0, 0))
        pygame.display.flip()
        time.sleep(2)
        return False, del_cards_num
    elif 3 <= len(selected_cards) <= 5:
        # 初始化记录数组，num_array[] = [image, num]; selected_cards[] = [row, col, image]
        num_array = []
        
        # 检查是否有可匹配的卡片
        num_array.append([selected_cards[0][2], 1])
        # 计算后续已选卡片的数量
        for i in range(1, len(selected_cards)):
            # 查看当前处理的卡片是否在已计算的卡片中
            for j in range(len(num_array)):
                if num_array[j][0] == selected_cards[i][2]:
                    # 在已计算的卡片中就累加，并检查是否有可匹配的卡片
                    num_array[j][1] += 1
                    if num_array[j][1] >= 3:
                        # 卡片可以匹配，则消除,消除完不必再判断其他已选卡片，则直接返回True
                        copy_selected_cards = [selected for selected in selected_cards]
                        for k in range(len(copy_selected_cards)):
                            if copy_selected_cards[k][2] == num_array[j][0]:
                                selected_cards.remove(copy_selected_cards[k])
                        del_cards_num += 3
                        return True, del_cards_num
                else:
                    # 不在已计算的卡片中，则存储新的卡片到num_array
                    num_array.append([selected_cards[i][2], 1])
        return True, del_cards_num
    else:
        return True, del_cards_num

    '''
    初代版本：简单三个匹配，不匹配则还原，匹配则消除
    r1, c1, image1 = selected_cards[0]
    r2, c2, image2 = selected_cards[1]
    r3, c3, image3 = selected_cards[2]
    if image1 == image2 == image3:
         # 相同则消除
        cards[r1][c1] = None
        cards[r2][c2] = None
        cards[r3][c3] = None
    else:
        # 不相同则还原
        if image1 is not None:
            cards[r1][c1] = image1
            screen.blit(image1, (c1 * (BLOCK_SIZE *5 // 4) + BLOCK_SIZE // 4, r1 * (BLOCK_SIZE * 5 // 4) + BLOCK_SIZE // 4))
        if image2 is not None:
            cards[r2][c2] = image2
            screen.blit(image2, (c2 * (BLOCK_SIZE *5 // 4) + BLOCK_SIZE // 4, r2 * (BLOCK_SIZE * 5 // 4) + BLOCK_SIZE // 4))
        if image3 is not None:
            cards[r3][c3] = image3
            screen.blit(image3, (c3 * (BLOCK_SIZE *5 // 4) + BLOCK_SIZE // 4, r3 * (BLOCK_SIZE * 5 // 4) + BLOCK_SIZE // 4))
    selected_cards.clear()
    '''

# 主游戏循环
def game_activate():
    # 游戏状态 
    running = True
    del_cards_num = 0
    game_state = 'MAIN_MENU' 
    time_left = game_time  # 当前剩余时间
    #cards = generate_cards() # 随机生成游戏板(初代，不会保证卡片可以完全消除)
    cards = generate_random_patterns(patterns, num_list, 2) # 随机生成游戏板(并保证卡片可以完全消除)
    cards2 = generate_random_patterns(patterns, num_list, 1) # 第二层

    clock = pygame.time.Clock()

    while running:
        clock.tick(FPS)

        # 事件处理
        for event in pygame.event.get():
            # 退出操作
            if event.type == pygame.QUIT:
                running = False

            # 鼠标点击操作
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if game_state == 'MAIN_MENU':
                    # 点击"新游戏"按钮
                    if ((x - 210) ** 2 + (y - 430) ** 2) ** 0.5 < 120:
                        game_state = 'NEW_GAME'
                        x, y = 0, 0

                    # 点击"退出"按钮
                    if ((x - 510) ** 2 + (y - 430) ** 2) ** 0.5 < 120:
                        running = False
                    continue
            
            if game_state == 'MAIN_MENU':
                # 显示背景图
                screen.blit(back_pattern, (0, 0))
                pygame.display.flip()
                
            elif game_state == 'NEW_GAME':
                # 绘制屏幕
                screen.fill(WHITE)
                draw_cards(cards2, 5)
                draw_cards(cards, 0)
                screen.blit(block_pattern, (0, SCREEN_HEIGHT - 3 * BLOCK_SIZE))
                draw_selected_cards(selected_cards) # 要先绘制背景再绘制已选图片，不然已选图片会被背景覆盖！！！
                #pygame.display.flip()

                ###################****************** AI 生成 *******************###################
                # 更新时间
                if time_left > 0:
                    time_left -= 1 / FPS  # 每帧减少的时间(秒)
                else:
                    running = False

                    # 打印超时信息,显示失败界面
                    print("Game Over: Time's up!")
                    screen.blit(time_out_pattern, (0, 0))
                    pygame.display.flip()
                    time.sleep(2)

                # 显示倒计时  
                time_text = font.render(f"Time Left: {int(time_left)}", True, WHITE)  
                screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, SCREEN_HEIGHT - 220))  # 居中显示 
                pygame.display.flip()
                ###################****************** AI 生成 *******************###################
                
                # 如果点击图案间隙，则不进行任何操作
                if(x % (BLOCK_SIZE *5 // 4) < BLOCK_SIZE // 4 or y % (BLOCK_SIZE *5 // 4) < BLOCK_SIZE // 4):
                    continue
                # 如果点击图案，则进行判断
                col, row = x // (BLOCK_SIZE *5 // 4), y // (BLOCK_SIZE *5 // 4)

                if cards[row][col][1] != 0 or cards2[row][col][1] != 0:
                    if cards[row][col][1] == 2:
                        selected_cards.append([row, col, cards[row][col]])
                    
                    elif cards2[row][col][1] == 2:
                        selected_cards.append([row, col, cards2[row][col]])

                    # 改变原图像显示和可选性
                    cards[row][col][1] = state_change(cards, row, col)
                    cards2[row][col][1] = state_change(cards2, row, col)

                    # 检查是否可以匹配消除(消除之后会随即点击第二层的卡片##############)
                    running, del_cards_num = check_match(cards, cards2, row, col, del_cards_num)

                    # 完全消除，游戏结束
                    if del_cards_num == 2 * ROWS * COLS:
                        running = False

                        # 打印成功信息,显示成功界面
                        print("Game successful!!!")
                        screen.blit(successful_pattern, (0, 0))
                        pygame.display.flip()
                        time.sleep(2)
                x, y = 0, 0

    pygame.quit()

if __name__ == '__main__':
    game_activate()

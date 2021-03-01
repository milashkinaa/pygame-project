import math
import os
from random import randint
from collections import deque


import pygame
from pygame.locals import *




FPS = 60
ANIMATION_SPEED = 0.18  # пиксели в миллисекунду
WIN_WIDTH = 284 * 2     # Размер изображения 284x512 пикселей; выложено плиткой дважды
WIN_HEIGHT = 512


class Bird(pygame.sprite.Sprite):


    """
    Приложение, где игрок управляет птичкой.

    Птица - "герой" этой игры.  Игрок может заставить его подняться
    (это нужно делать быстро), иначе она разобьется. Нужно пройти через
    пространство между трубами(за каждую пройденную трубу начисляется одно
    очко); если она врезается в трубу, игра заканчивается.


    Управление возможно реализовать нажатием следующих клавиш:

    1) стрелка вверх
    2) пробел

    обе эти кнопки реализуют поднятие птицы


    Атрибуты:

    x: Координата X птицы.

    y: Координата Y птицы.

    msec_to_climb: Количество миллисекунд, оставшихся до подъема,
    когда птица поднимается.

    CLIMB_DURATION миллисекунды.



    Константы:
    WIDTH: Ширина изображения птицы в пикселях.

    HEIGHT: Высота изображения птицы в пикселях.

    SINK_SPEED: С какой скоростью, в пикселях в миллисекунду, птица
        спускается за одну секунду, не поднимаясь.

    CLIMB_SPEED: С какой скоростью, в пикселях в миллисекунду, птица
        поднимается в среднем за одну секунду при подъеме.

    CLIMB_DURATION: Количество миллисекунд, которое требуется птице для
        выполнения полного набора высоты.

    """


    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.18
    CLIMB_SPEED = 0.3
    CLIMB_DURATION = 333.3

    def __init__(self, x, y, msec_to_climb, images):

        """
        Инициализация птички.

        Аргументы:

        x: Координата X птицы.

        y: Координата Y птицы.

        msec_to_climb: Количество секунд, оставшихся до набора высоты,
         когда птица набирает полную высоту.

        images: Кортеж, содержащий изображения, чтобы показать птицу.
          Он содержит следующие картинки:
                0. изображение птицы с крылом, направленным вверх
                1. изображение птицы с крылом, направленным вниз

        """

        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):

        """
        Изменение положения птицы.

        Эта функция использует функцию косинуса для достижения плавного подъема:
        В первом и последнем кадрах птица поднимается очень мало, в
        середине подъема она поднимается много.
        Один полный подъем длится CLIMB_DURATION миллисекунды, в течение которых
        птица поднимается со средней скоростью CLIMB_SPEED px/ms.
        Атрибут msec_to_climb этой птицы будет автоматически
        уменьшен соответствующим образом, если он был > 0 при вызове этого метода.

        Аргументы:
        delta_frames: Количество кадров, прошедших с момента запуска этого метода

        """

        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.CLIMB_DURATION
            self.y -= (Bird.CLIMB_SPEED * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self):

        """
        Получение изображения птицы.

        Этот атрибут рассчитывает, какое изображение
        нужно подставить - то, где крыло опущено, или то,
        где оно поднято.
        Атрибут помогает получить "хлопанье"
        крыльев, чтобы "оживить" игру.

        """

        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):

        """
        Рассчитываем столкновения, чтобы их избежать
        """
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):

        """
        Получите положение, ширину и высоту птицы в виде pygame.Rect.
        """
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):

    """
    Представляет собой препятствие.

    В игре есть препятствие в виде труб,
    между которыми есть препятствие.
    Птица должна пройти между ними,
    иначе произойдет столкновение и конец игры.

    Атрибуты:
    x:  X-позиция Трубы, чтобы сделать движение плавным.

    image: pygame.Surface - фоновое изображение,
    на фоне которого размещены трубы.

    mask: Битовая маска, убирающая все пиксели
    с прозрачностью больше 127, чтобы не было накладок

    top_pieces: Количество верхних частей труб
    bottom_pieces: Количество нижних частей труб

    Constants:
    WIDTH: Ширина куска трубы в пикселях.

    PIECE_HEIGHT: Высота, в пикселях, куска трубы.

    ADD_INTERVAL: Интервал в миллисекундах
    между добавлением новых труб.

    """


    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000


    def __init__(self, pipe_end_img, pipe_body_img):

        """
        Инициализирует новую случайную трубную пару.

        Новой паре труб будет
        автоматически присвоен x = float(WIN_WIDTH - 1).

        Аргументы:
        pipe_end_img: Изображение, используемое для представления
        концевой части трубы.

        pipe_body_img: Изображение, используемое для представления
        одного горизонтального среза из тела трубы.
        """


        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()   # ускоряет наложение изображений
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -                  # заполняет окно сверху вниз
             3 * Bird.HEIGHT -             # формирует расстояние между трубами для птицы
             3 * PipePair.PIECE_HEIGHT) /  # формирует части труб
            PipePair.PIECE_HEIGHT          # получает количество кусков труб
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces


        # нижняя труба
        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)


        # верхняя труба
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        # фиксируем добавленные детальки
        self.top_pieces += 1
        self.bottom_pieces += 1

        # обнаруживает столкновения
        self.mask = pygame.mask.from_surface(self.image)


    @property
    def top_height_px(self):

        """
        Получаем высоту верхней трубы в пикселях
        """
        return self.top_pieces * PipePair.PIECE_HEIGHT


    @property
    def bottom_height_px(self):

        """
        Получаем высоту нижней трубы в пикселях.
        """

        return self.bottom_pieces * PipePair.PIECE_HEIGHT


    @property
    def visible(self):

        """
        Получаем изображение трубы с промежутком
        """

        return -PipePair.WIDTH < self.x < WIN_WIDTH


    @property
    def rect(self):

        """
        Получаем прямоугольник, содержащий трубу и ее размеры
        """

        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)


    def update(self, delta_frames=1):

        """
        Изменяем размещение трубы

        Аргументы:
        delta_frames: Количество кадров, прошедших с тех пор,
        как этот метод был последний раз вызван.
        """

        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):

        """
        Рассчитываем, столкнется ли птица с трубой

        Аргументы:
        bird: Положение птицы
        """

        return pygame.sprite.collide_mask(self, bird)


def load_images():

    """
    Загружаем все изображения, необходимые для игры, и помещаем в словарь.

    Возвращаемый словарь имеет следующие ключи:
    background: Фоновое изображение игры.
    bird-wingup: Изображение птицы с крылом, направленным вверх.
        Используется вместе с bird-wingdown, чтобы создать видение полета птицы.
    bird-wingdown: Изображение птицы с крылом, направленным вниз.
        Используется вместе с bird-wingup, чтобы создать видение полета птицы.
    pipe-end: Используется вместе с pipe-body, чтобы нарисовать трубу
    pipe-body: Используется вместе с pipe-end, чтобы нарисовать трубу
    """


    def load_image(img_file_name):

        """
        Возвращает картинки

        Эта функция ищет изображения в папке изображений игры
        (dirname(__file__)/images/).
        Все изображения преобразуются перед тем, как быть
        вернулся, чтобы ускорить блиттинг.

        Аргументы:
        img_file_name: Имя файла
        (включая его расширение, например '.png')
        требуемого изображения, без пути к файлу.
        """


        file_name = os.path.join(os.path.dirname(__file__),
                                 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img


    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            # изображения для анимации хлопающей птицы-анимированные GIF-файлы
            # не поддерживается в pygame
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):

    """
    Конвертировать кадров в миллисекундах, по прошествии указанного количества кадров в секунду.

    Аргументы:
    frames: Сколько кадров преобразовать в миллисекунду.
    fps: Частота кадров, используемая для преобразования.  По умолчанию: FPS.
    """

    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):

    """
    Преобразуем миллисекунды в кадры с заданной частотой кадров.

    Аргументы:
    milliseconds: Сколько миллисекунд нужно преобразовать в кадры.
    fps: Частота кадров, используемая для преобразования.  По умолчанию: FPS.
    """

    return fps * milliseconds / 1000.0


def main():


    """

    Запуск приложения.

    """


    pygame.init()


    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Pygame Flappy Bird')


    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)  # шрифт по умолчанию
    images = load_images()


    # птица остается в том же положении x, поэтому bird.x - это константа
    # центральная птица на экране
    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))


    pipes = deque()


    frame_clock = 0  # этот счетчик увеличивается только в том случае, если игра не приостановлена
    score = 0
    done = paused = False
    while not done:
        clock.tick(FPS)


        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pp = PipePair(images['pipe-end'], images['pipe-body'])
            pipes.append(pp)


        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                    e.key in (K_UP, K_RETURN, K_SPACE)):
                bird.msec_to_climb = Bird.CLIMB_DURATION


        if paused:
            continue  # Ничего не рисуем


        # проверяем наличие столкновений
        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
            done = True


        for x in (0, WIN_WIDTH / 2):
            display_surface.blit(images['background'], (x, 0))


        while pipes and not pipes[0].visible:
            pipes.popleft()


        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)


        bird.update()
        display_surface.blit(bird.image, bird.rect)


        # обновление и отображение результатов
        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True


        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))


        pygame.display.flip()
        frame_clock += 1


    print('Игра окончена! Счет: %i' % score)
    pygame.quit()


if __name__ == '__main__':
    main()
